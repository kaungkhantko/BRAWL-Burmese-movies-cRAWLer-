import scrapy
import logging
from burmese_movies.items import BurmeseMoviesItem
from scrapy.http import HtmlResponse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from scrapy.http import HtmlResponse
from burmese_movies.candidate_extractor import extract_candidate_blocks
from burmese_movies.openai_selector import query_openai_for_best_selector


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
        self.logger.info(f"Parsing rendered page: {response.url}")
        if self.is_catalogue_page(response):
            self.logger.info(f"Detected CATALOGUE page: {response.url}")
            for detail_page_link in self.extract_movie_links(response):
                yield response.follow(detail_page_link, callback=self.parse)
        elif self.is_detail_page(response):
            self.logger.info(f"Detected DETAIL page: {response.url}")
            yield self.parse_movie_detail(response)
        else:
            self.logger.warning(f"Unknown page type: {response.url}")
        # Step 1: Extract candidate blocks
        candidates = extract_candidate_blocks(response.text)
        self.logger.info(f"Extracted {len(candidates)} candidate blocks.")

        if not candidates:
            self.logger.warning("No candidates extracted, skipping page.")
            return

        # Step 2: Use OpenAI to select the best candidate
        try:
            best_index = query_openai_for_best_selector(candidates)
            self.logger.info(f"OpenAI selected Block #{best_index + 1} for movie parsing.")
        except Exception as e:
            self.logger.error(f"OpenAI query failed: {e}")
            best_index = 0  # fallback to first block

        best_block_html = candidates[best_index]

        # Step 3: Parse the best block
        best_response = HtmlResponse(
            url=response.url,
            body=best_block_html,
            encoding='utf-8'
        )

        # (Very simple: assume each movie is one div/article/section inside the best block)
        for movie in best_response.css('div, article, section'):
            item = BurmeseMoviesItem()
            for field, selectors in self.SELECTORS.items():
                item[field] = self.extract_with_fallback(movie, selectors, field)
            yield item

    def is_catalogue_page(self, response):
        # If there are lots of movie cards on this page, assume it's a catalogue
        movie_cards = response.css('div.movie-card, div.card, div.movie')
        return len(movie_cards) >= 5

    def is_detail_page(self, response):
        # If there is a big title, poster, and maybe a streaming link
        title = response.css('h1.title, h1.entry-title, div.movie-title').get()
        poster = response.css('img.poster, img.cover').get()
        return bool(title and poster)
    def extract_movie_links(self, response):
        # Find all movie card links
        links = response.css('div.movie-card a::attr(href)').getall()
        links += response.css('div.card a::attr(href)').getall()
        links += response.css('div.movie a::attr(href)').getall()
        self.logger.info(f"Found {len(links)} movie links on catalogue page.")
        return links
