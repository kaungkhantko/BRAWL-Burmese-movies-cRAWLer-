import scrapy
import logging
from burmese_movies.items import BurmeseMoviesItem
from scrapy.http import HtmlResponse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from scrapy.http import HtmlResponse
from burmese_movies.burmese_movies.candidate_extractor import extract_candidate_blocks  # Your new module


logger = logging.getLogger(__name__)

class MoviesSpider(scrapy.Spider):
    name = "movies"
    allowed_domains = ["channelmyanmar.to"]
    start_urls = ["https://www.channelmyanmar.to/movies/"]

    SELECTORS = {
        'title': ['h2.title::text', 'div.movie-title::text', 'span.title::text'],
        'year': ['span.year::text', 'div.release-year::text'],
        'director': ['span.director::text', 'div.director-name::text'],
        'cast': ['span.cast::text', 'div.actor-list::text'],
        'genre': ['span.genre::text', 'div.genre-tag::text'],
        'synopsis': ['p.synopsis::text', 'div.synopsis-text::text'],
        'poster_url': ['img.poster::attr(src)', 'img.cover::attr(src)'],
        'streaming_link': ['a.watch-link::attr(href)', 'a.stream-now::attr(href)'],
    }

    def __init__(self, *args, **kwargs):
        super(MoviesSpider, self).__init__(*args, **kwargs)
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # run Chrome without opening a window
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=chrome_options)

    def closed(self, reason):
        """Close Selenium browser when spider closes."""
        self.driver.quit()

    def extract_with_fallback(self, response, selectors, field_name):
        for sel in selectors:
            data = response.css(sel).get()
            if data:
                logger.info(f"[Matched] Field '{field_name}' → Selector '{sel}'")
                return data.strip()
        logger.warning(f"[Missing] Field '{field_name}' - No selector matched")
        return None

def parse(self, response):
    for url in self.start_urls:
        # --- Step 1: Use Selenium to render page ---
        self.driver.get(url)
        time.sleep(3)  # Later: replace with WebDriverWait for better efficiency

        # --- Step 2: Get full HTML source after rendering ---
        page_source = self.driver.page_source

        # --- Step 3: Create a Scrapy HtmlResponse from rendered page ---
        sel_response = HtmlResponse(
            url=self.driver.current_url,
            body=page_source,
            encoding='utf-8'
        )

        # --- Step 4: Extract candidate movie blocks from the rendered page ---
        candidates = extract_candidate_blocks(page_source)
        self.logger.info(f"Extracted {len(candidates)} candidate blocks for OpenAI analysis.")

        # --- Step 5: (Next) Pass candidates to OpenAI to pick the best one ---
        # TODO: Call OpenAI API here (next step)
        # best_selector = self.query_openai_for_best_selector(candidates)

        # For now, fallback manually until we have OpenAI integration
        best_selector = 'div.movie-card, div.card, div.movie'

        # --- Step 6: Use best selector to scrape movies ---
        for movie in sel_response.css(best_selector):
            item = BurmeseMoviesItem()
            for field, selectors in self.SELECTORS.items():
                item[field] = self.extract_with_fallback(movie, selectors, field)
            yield item
