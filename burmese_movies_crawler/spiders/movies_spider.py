# module: burmese_movies_crawler.spiders.movies_spider

import scrapy
import logging
import os
import json
from datetime import datetime, timezone
from selenium.webdriver.chrome.options import Options
from fuzzywuzzy import process
from scrapy import signals
from burmese_movies_crawler.items import BurmeseMoviesItem, FIELD_SELECTORS
from burmese_movies_crawler.utils.orchestrator import handle_page
from burmese_movies_crawler.utils.link_utils import (
    rule_link_heavy, rule_text_heavy,
    rule_table_catalogue, rule_fallback_links
)
from burmese_movies_crawler.utils.selenium_manager import SeleniumManager
from burmese_movies_crawler.utils.page_classifier import PageClassifier
from burmese_movies_crawler.utils.field_extractor import FieldExtractor
from burmese_movies_crawler.utils.orchestrator import handle_page

logger = logging.getLogger(__name__)

class MoviesSpider(scrapy.Spider):
    name = "movies"
    allowed_domains = ["channelmyanmar.to"]
    start_urls = [
        "https://www.channelmyanmar.to/movies/",
        "https://en.wikipedia.org/wiki/List_of_Burmese_films",
        "https://www.imdb.com/search/title/?country_of_origin=MM",
        "https://www.savemyanmarfilm.org/film-catalogue/"
    ]

    MOVIE_DETAIL_FIELD_MAPPING = {
        'director': ['director', 'directed by', 'filmmaker'],
        'cast': ['cast', 'actors', 'starring'],
        'genre': ['genre', 'category', 'type'],
        'synopsis': ['synopsis', 'story', 'plot'],
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.crawler.settings.set('FEEDS', {spider.movies_output_file: {'format': 'json', 'encoding': 'utf8', 'overwrite': False}}, priority='spider')
        crawler.signals.connect(spider.open_spider, signal=signals.spider_opened)
        crawler.signals.connect(spider.close_spider, signal=signals.spider_closed)
        return spider

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = None
        self._setup_paths()
        self.start_time = None
        self.end_time = None
        self.warnings, self.errors = [], []
        self.items_scraped = 0
        self.invalid_links = []

        self.DEFAULT_RULE_THRESHOLDS = {
            'link_heavy_min_links': 50,
            'link_heavy_max_iframes': 0,
            'text_heavy_min_paragraphs': 50,
            'text_heavy_max_images': 5,
            'fallback_min_links': 30,
            'fallback_max_images': 5,
            'table_min_rows': 3,
            'score_threshold': 4,
        }

        self.CATALOGUE_RULES = [
            ("link_heavy", rule_link_heavy, 2),
            ("text_heavy", rule_text_heavy, 2),
            ("table_catalogue", rule_table_catalogue, 3),
            ("fallback_links", rule_fallback_links, 1),
        ]

        self.classifier = PageClassifier(self.DEFAULT_RULE_THRESHOLDS, self.CATALOGUE_RULES)
        self.extractor = FieldExtractor(self.invalid_links)

    def _setup_paths(self):
        timestamp = os.getenv("SCRAPY_RUN_TIMESTAMP", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        output_base = "output"
        self.timestamp = timestamp
        self.output_dir = os.path.join(output_base, timestamp)
        os.makedirs(self.output_dir, exist_ok=True)
        self.movies_output_file = os.path.join(self.output_dir, f"movies_{timestamp}.json")
        self.log_file = os.path.join(self.output_dir, f"crawler_output_{timestamp}.log")
        self.summary_file = os.path.join(self.output_dir, f"run_summary_{timestamp}.json")

    def open_spider(self, spider):
        # start up Selenium via our manager
        self.selenium_mgr = SeleniumManager()
        self.driver = self.selenium_mgr.__enter__()
        self.start_time = datetime.now(timezone.utc)
        logger.info("Chrome Driver started.")

    def close_spider(self, spider, reason):
        # tear down Selenium
        if self.selenium_mgr:
            self.selenium_mgr.__exit__(None, None, None)
        # record end time and save summary
        self.end_time = datetime.now(timezone.utc)
        self._save_run_summary(reason)

        # dump invalid links if any
        if self.invalid_links:
            path = os.path.join(self.output_dir,
                                f"invalid_links_{self.timestamp}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.invalid_links, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.invalid_links)} invalid links to {path}")

    def _save_run_summary(self, reason):
        summary = {
            "spider_name": self.name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "runtime_seconds": (self.end_time - self.start_time).total_seconds() if self.start_time else None,
            "items_scraped": self.items_scraped,
            "warnings": self.warnings,
            "errors": self.errors,
            "movies_output_file": self.movies_output_file,
            "log_file": self.log_file,
            "close_reason": reason
        }
        with open(self.summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=4, ensure_ascii=False)
        logger.info(f"Run summary saved to: {self.summary_file}")

    def parse(self, response):
        logger.info(f"Parsing page: {response.url}")
        try:
            result = handle_page(response.text, response.url,
                                self.classifier, self.extractor)
        except Exception as e:
            logger.exception(f"Failed to classify “{response.url}”: {e}")
            self.errors.append((response.url, str(e)))
            return

        if result["type"] == "catalogue":
            for link in result["links"]:
                yield response.follow(link,
                                    callback=self.parse,
                                    meta={'source': 'catalogue'},
                                    priority=10)

            # pagination
            if result.get("next_page"):
                yield response.follow(result["next_page"],
                                    callback=self.parse,
                                    meta={'source': 'pagination'},
                                    priority=5)

        elif result["type"] == "detail":
            item = BurmeseMoviesItem(**result["item"])
            yield item
            self.items_scraped += 1

        else:
            # unknown gets retried through candidate_extractor fallback
            for link in result.get("fallback_links", []):
                yield response.follow(link, callback=self.parse)


    def evaluate_catalogue_rules(self, response, stats):
        """Evaluate all rules and collect their boolean outcomes."""
        results = []

        for name, rule_fn, weight in self.CATALOGUE_RULES:
            try:
                if name == "table_catalogue":
                    passed = rule_fn(response, stats)
                else:
                    passed = rule_fn(stats)
                results.append({
                    'name': name,
                    'passed': passed,
                    'weight': weight
                })
                logger.info(f"[Rule {name}] Passed={passed} (weight {weight})")
            except Exception as e:
                logger.error(f"[Rule Error] {name}: {e}")
                results.append({
                    'name': name,
                    'passed': False,
                    'weight': weight
                })

        return results

    def _map_headers(self, headers):
        mapping = {
            'title': ['title', 'film title', 'film', 'movie'],
            'year': ['year', 'release year', 'film year'],
            'director': ['director', 'directed by', 'filmmaker'],
            'genre': ['genre', 'type', 'category']
        }
        results = {}
        for head in headers:
            for field, candidates in mapping.items():
                match, score = process.extractOne(head.lower(), candidates)
                if score > 70:
                    results[head] = field
        return results

    def _match_field(self, text):
        best, score = None, 0
        for field, candidates in self.MOVIE_DETAIL_FIELD_MAPPING.items():
            match, match_score = process.extractOne(text.lower(), candidates)
            if match_score > score:
                best, score = field, match_score
        return best, score

    def _clean_text(self, text):
        return text.split(':', 1)[-1].strip() if ':' in text else text

