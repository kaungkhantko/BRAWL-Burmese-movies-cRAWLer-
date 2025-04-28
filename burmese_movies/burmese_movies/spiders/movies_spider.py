import scrapy
import logging
import os
import json
from datetime import datetime, timezone
from scrapy.http import HtmlResponse
from burmese_movies.items import BurmeseMoviesItem, FIELD_SELECTORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from burmese_movies.candidate_extractor import extract_candidate_blocks
from burmese_movies.openai_selector import query_openai_for_best_selector
from scrapy import signals

logger = logging.getLogger(__name__)

class MoviesSpider(scrapy.Spider):
    name = "movies"
    allowed_domains = ["channelmyanmar.to"]
    start_urls = [
        "https://www.channelmyanmar.to/movies/",
        "https://en.wikipedia.org/wiki/List_of_Burmese_films"
    ]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)

        crawler.signals.connect(spider.open_spider, signal=signals.spider_opened)
        crawler.signals.connect(spider.close_spider, signal=signals.spider_closed)

        timestamp = os.getenv("SCRAPY_RUN_TIMESTAMP", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        output_base = "output"
        output_dir = os.path.join(output_base, timestamp)
        os.makedirs(output_dir, exist_ok=True)

        spider.timestamp = timestamp
        spider.output_base = output_base
        spider.output_dir = output_dir
        spider.movies_output_file = os.path.join(spider.output_dir, f"movies_{timestamp}.json")
        spider.log_file = os.path.join(spider.output_dir, f"crawler_output_{timestamp}.log")
        spider.summary_file = os.path.join(spider.output_dir, f"run_summary_{timestamp}.json")
        spider.start_time = None
        spider.end_time = None
        spider.warnings = []
        spider.errors = []
        spider.items_scraped = 0

        crawler.settings.set('FEEDS', {
            spider.movies_output_file: {
                'format': 'json',
                'encoding': 'utf8',
                'overwrite': False,
            }
        }, priority='spider')

        return spider

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = None

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
            logger.info("Chrome Driver closed.")

        self.end_time = datetime.now(timezone.utc)
        runtime_seconds = (self.end_time - self.start_time).total_seconds() if self.start_time else None

        summary = {
            "spider_name": self.name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "runtime_seconds": runtime_seconds,
            "items_scraped": self.items_scraped,
            "warnings": self.warnings,
            "errors": self.errors,
            "movies_output_file": self.movies_output_file,
            "log_file": self.log_file,
            "close_reason": reason
        }
        try:
            summary_path = os.path.join(self.output_dir, f"run_summary_{self.timestamp}.json")
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=4, ensure_ascii=False)
            logger.info(f"Run summary saved to: {summary_path}")
        except Exception as e:
            logger.error(f"Failed to save run summary: {e}")

    def extract_with_fallback(self, response, selectors, field_name):
        for sel in selectors:
            data = response.css(sel).get()
            if data:
                logger.info(f"[Matched] Field '{field_name}' → Selector '{sel}'")
                return data.strip()
        warning_msg = f"[Missing] Field '{field_name}' - No selector matched"
        logger.warning(warning_msg)
        self.warnings.append(warning_msg)
        return None

    def parse(self, response):
        self.logger.info(f"Parsing rendered page: {response.url}")

        if self.is_catalogue_page(response):
            self.logger.info("Detected catalogue page. Collecting movie links...")
            for link in self.extract_movie_links(response):
                yield response.follow(link, callback=self.parse_movie_detail)
            next_page = response.css('a.next.page-numbers::attr(href)').get()
            if next_page:
                self.logger.info(f"Found next page: {next_page}")
                yield response.follow(next_page, callback=self.parse)
            else:
                self.logger.info("No next page found. Catalogue scraping complete.")


        elif self.is_detail_page(response):
            self.logger.info(f"Detected DETAIL page: {response.url}")
            yield from self.parse_movie_detail(response)

        else:
            self.logger.warning(f"Unknown page type: {response.url}")
            # Optional fallback: Try OpenAI block parsing if really necessary
            yield from self.parse_fallback_with_openai(response)

    def parse_movie_detail(self, response):
        """Parse an individual movie detail page."""
        item = BurmeseMoviesItem()

        # Title
        item['title'] = response.css('h1.entry-title::text, h1.title::text, div.movie-title::text').get(default='').strip()

        # Year
        item['year'] = response.css('.ytps::text, span[class*="year"]::text').get(default='').strip()

        # Director, Cast, Genre (split paragraphs)
        paragraphs = response.css('div.entry-content p::text').getall()
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if 'Director' in paragraph:
                item['director'] = paragraph.replace('Director:', '').strip()
            if 'Cast' in paragraph:
                item['cast'] = paragraph.replace('Cast:', '').strip()
            if 'Genre' in paragraph:
                item['genre'] = paragraph.replace('Genre:', '').strip()

        # Synopsis (first non-metadata paragraph)
        for paragraph in paragraphs:
            if all(keyword not in paragraph for keyword in ['Director', 'Cast', 'Genre']):
                item['synopsis'] = paragraph.strip()
                break

        # Poster
        item['poster_url'] = response.css('div.entry-content img::attr(src)').get()

        # Streaming link
        item['streaming_link'] = response.css('iframe::attr(src)').get()

        yield item
        self.items_scraped += 1

    def parse_fallback_with_openai(self, response):
        """If structure is unclear, fallback to OpenAI candidate block selection."""
        candidates = extract_candidate_blocks(response.text)
        self.logger.info(f"Extracted {len(candidates)} candidate blocks.")

        if not candidates:
            self.logger.warning("No candidates extracted, skipping page.")
            return

        try:
            best_index = query_openai_for_best_selector(candidates)
            self.logger.info(f"OpenAI selected Block #{best_index + 1} for movie parsing.")
        except Exception as e:
            self.logger.error(f"OpenAI query failed: {e}")
            best_index = 0  # fallback to first block

        best_block_html = candidates[best_index]
        best_response = HtmlResponse(url=response.url, body=best_block_html, encoding='utf-8')

        item = BurmeseMoviesItem()
        for field, selectors in FIELD_SELECTORS.items():
            value = self.extract_with_fallback(best_response, selectors, field)
            item[field] = value
        yield item

    def is_catalogue_page(self, response) -> bool:
        """Determine if this is a movie catalogue page based on structure."""
        movie_blocks = response.css('div.item a::attr(href)').getall()
        poster_imgs = response.css('img[src*="tmdb.org/t/p/"], img[src*="/uploads/"]').getall()
        return len(movie_blocks) >= 5 or len(poster_imgs) >= 5

    def is_detail_page(self, response) -> bool:
        """Determine if it's a movie detail page based on poster/title/iframe."""
        title = response.css('h1.entry-title, h1.title, div.movie-title').get()
        poster = response.css('img.poster, img.cover, div.entry-content img').get()
        iframe = response.css('iframe').get()
        return bool(title and poster and iframe)

    def extract_movie_links(self, response):
        """Extract movie links from a catalogue page."""
        links = response.css('div.item a::attr(href)').getall()
        self.logger.info(f"Found {len(links)} movie links on catalogue page.")
        return list(set(links))  # Remove duplicates
