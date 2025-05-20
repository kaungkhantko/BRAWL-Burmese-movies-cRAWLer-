# module: burmese_movies_crawler.spiders.movies_spider

import scrapy
import logging
import os
import json
from datetime import datetime, timezone
from scrapy import signals

from burmese_movies_crawler.items import BurmeseMoviesItem
from burmese_movies_crawler.core.orchestrator import handle_page
from burmese_movies_crawler.core.page_classifier import PageClassifier
from burmese_movies_crawler.core.selenium_manager import SeleniumManager
from burmese_movies_crawler.core.mock_utils import get_response_or_request
from burmese_movies_crawler.factory import create_extractor_engine
from burmese_movies_crawler.config import MOCK_MODE, DEFAULT_RULE_THRESHOLDS, CATALOGUE_RULES, START_URLS

logger = logging.getLogger(__name__)


class MoviesSpider(scrapy.Spider):
    name = "movies"
    allowed_domains = ["channelmyanmar.to"]
    start_urls = START_URLS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = None
        self._setup_paths()
        self.start_time = None
        self.end_time = None
        self.warnings, self.errors = [], []
        self.items_scraped = 0
        self.invalid_links = []
        self.fixture = kwargs.get('fixture')  # Get fixture from spider arguments

        self.classifier = PageClassifier(DEFAULT_RULE_THRESHOLDS, CATALOGUE_RULES)
        self.extractor = create_extractor_engine(content_type='movies', invalid_links=self.invalid_links)
        
        # Track fixtures used for reporting
        self.fixtures_used = set()

    def start_requests(self):
        # If a specific fixture is provided, use it for the first URL
        if MOCK_MODE and self.fixture:
            url = self.start_urls[0]
            logger.info(f"Using fixture {self.fixture} for {url}")
            self.fixtures_used.add(self.fixture)
            yield get_response_or_request(url, self.parse, fixture_name=self.fixture)
            
            # Process remaining URLs normally
            for url in self.start_urls[1:]:
                yield get_response_or_request(url, self.parse)
        else:
            # Process all URLs normally
            for url in self.start_urls:
                yield get_response_or_request(url, self.parse)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.crawler.settings.set('FEEDS', {spider.movies_output_file: {'format': 'json', 'encoding': 'utf8', 'overwrite': False}}, priority='spider')
        crawler.signals.connect(spider.open_spider, signal=signals.spider_opened)
        crawler.signals.connect(spider.close_spider, signal=signals.spider_closed)
        return spider

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
        if not MOCK_MODE:
            self.selenium_mgr = SeleniumManager()
            self.driver = self.selenium_mgr.__enter__()
            self.start_time = datetime.now(timezone.utc)
            logger.info("Chrome Driver started.")
        else:
            self.selenium_mgr = None
            self.start_time = datetime.now(timezone.utc)
            logger.info("Running in MOCK MODE - no Chrome Driver needed.")

    def close_spider(self, spider, reason):
        # tear down Selenium
        if hasattr(self, 'selenium_mgr') and self.selenium_mgr:
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
            "close_reason": reason,
            "mock_mode": MOCK_MODE
        }
        
        # Add fixtures used if in mock mode
        if MOCK_MODE:
            summary["fixtures_used"] = list(self.fixtures_used)
        
        with open(self.summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=4, ensure_ascii=False)
        logger.info(f"Run summary saved to: {self.summary_file}")

    def parse(self, response):
        logger.info(f"Parsing page: {response.url}")
        
        # Track fixtures used in mock mode
        if MOCK_MODE and hasattr(response, 'url') and response.url.startswith('http'):
            # Extract fixture name from request meta if available
            fixture_name = response.request.meta.get('fixture_name') if hasattr(response, 'request') else None
            if fixture_name:
                self.fixtures_used.add(fixture_name)
        
        try:
            result = handle_page(response.text, response.url,
                                self.classifier, self.extractor)
        except Exception as e:
            logger.exception(f"Failed to classify {response.url}: {e}")
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