import scrapy
import logging
import os
import json
import re
from datetime import datetime, timezone
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fuzzywuzzy import process
from scrapy import signals
from burmese_movies_crawler.items import BurmeseMoviesItem, FIELD_SELECTORS
from burmese_movies_crawler.candidate_extractor import extract_candidate_blocks
from burmese_movies_crawler.openai_selector import query_openai_for_best_selector
from urllib.parse import urlparse
from burmese_movies_crawler.utils.link_utils import is_valid_link

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
            'score_threshold': 4,  # minimum points to be classified as catalogue
        }

        self.CATALOGUE_RULES = [
            ("link_heavy", self._rule_link_heavy, 2),
            ("text_heavy", self._rule_text_heavy, 2),
            ("table_catalogue", self._rule_table_catalogue, 3),
            ("fallback_links", self._rule_fallback_links, 1)
        ]

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
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=chrome_options)
        self.start_time = datetime.now(timezone.utc)
        logger.info("Chrome Driver started.")

    def close_spider(self, spider, reason):
        if self.driver:
            self.driver.quit()
        self.end_time = datetime.now(timezone.utc)
        self._save_run_summary(reason)

        if self.invalid_links:
            invalid_links_path = os.path.join(self.output_dir, f"invalid_links_{self.timestamp}.json")
            with open(invalid_links_path, "w", encoding="utf-8") as f:
                json.dump(self.invalid_links, f, indent=4, ensure_ascii=False)
            logger.info(f"Saved {len(self.invalid_links)} invalid links to {invalid_links_path}")


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
        if self.is_catalogue_page(response):
            yield from self.parse_catalogue(response)
        elif self.is_detail_page(response):
            yield from self.parse_detail(response)
        else:
            yield from self.parse_unknown(response)

    def parse_catalogue(self, response):
        tables = response.css('table')
        if tables and len(response.css('table tbody tr')) >= 3:
            logger.info(f"Detected static table with {len(tables[0].css('tbody tr'))} rows.")
            yield from self.extract_from_table(response, tables[0])
            return
        links = self.extract_links(response)
        for link in links:
            yield response.follow(link, callback=self.parse, meta={'source': 'catalogue'}, priority=10)
        next_page = response.css('a.next.page-numbers::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse, meta={'source': 'pagination'}, priority=5)

    def parse_detail(self, response):
        item = BurmeseMoviesItem()
        item.update(self.extract_main_fields(response))
        item.update(self.extract_paragraphs(response))
        yield item
        self.items_scraped += 1

    def parse_unknown(self, response):
        logger.warning(f"Unknown page structure: {response.url}")
        candidates = extract_candidate_blocks(response.text)
        if not candidates:
            return
        best_block_html = candidates[query_openai_for_best_selector(candidates)]
        fake_response = HtmlResponse(url=response.url, body=best_block_html, encoding='utf-8')
        yield from self.parse_detail(fake_response)

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

    def extract_links(self, response):
        selectors = [
            'div.item a::attr(href)', 'div.card a::attr(href)', 'div.movie a::attr(href)',
            'div.movie-entry a::attr(href)', 'div.movie-card a::attr(href)',
            'article a::attr(href)', 'li a::attr(href)'
        ]
        links = []
        for selector in selectors:
            links.extend(response.css(selector).getall())

        unique_links = set()
        for link in links:
            if is_valid_link(link, self.invalid_links):
                unique_links.add(link.strip())

        logger.info(f"Extracted {len(unique_links)} valid links after filtering.")
        return list(unique_links)

    def extract_main_fields(self, response):
        fields = {
            'title': ['h1.entry-title::text', 'h1.title::text', 'div.movie-title::text'],
            'year': ['.ytps::text', 'span[class*="year"]::text'],
            'poster_url': ['div.entry-content img::attr(src)'],
            'streaming_link': ['iframe::attr(src)']
        }
        return {field: self._extract_first(response, selectors) for field, selectors in fields.items()}

    def extract_paragraphs(self, response):
        data, used = {}, set()
        for text in response.css('div.entry-content p::text').getall():
            clean = text.strip()
            field, score = self._match_field(clean)
            if field and field not in used and score > 70:
                data[field] = self._clean_text(clean)
                used.add(field)
        return data

    def extract_from_table(self, response, table):
        headers = [h.strip() for h in table.css('thead th::text, thead td::text').getall() if h.strip()]
        header_map = self._map_headers(headers)
        for row in table.css('tbody tr'):
            cells = [c.strip() for c in row.css('td::text, td *::text').getall() if c.strip()]
            if len(cells) != len(headers):
                continue
            item = BurmeseMoviesItem()
            for head, value in zip(headers, cells):
                field = header_map.get(head)
                if field:
                    item[field] = value
            if item.get('title'):
                yield item
                self.items_scraped += 1

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

    def _extract_first(self, response, selectors):
        for sel in selectors:
            value = response.css(sel).get()
            if value:
                return value.strip()
        return None

    def _match_field(self, text):
        best, score = None, 0
        for field, candidates in self.MOVIE_DETAIL_FIELD_MAPPING.items():
            match, match_score = process.extractOne(text.lower(), candidates)
            if match_score > score:
                best, score = field, match_score
        return best, score

    def _clean_text(self, text):
        return text.split(':', 1)[-1].strip() if ':' in text else text

