# burmese_movies_crawler/utils/field_extractor.py

from .link_utils import is_valid_link
from burmese_movies_crawler.items import FIELD_SELECTORS
from fuzzywuzzy import process
import logging
from burmese_movies_crawler.items import BurmeseMoviesItem
from urllib.parse import urldefrag

logger = logging.getLogger(__name__)
class FieldExtractor:
    def __init__(self, invalid_links=None):
        self.invalid_links = invalid_links if invalid_links is not None else []
        self.items_scraped = 0

        self.CATALOGUE_FIELD_MAPPING = {
            'title': ['h1.entry-title::text', 'h1.title::text', 'div.movie-title::text'],
            'year': ['.ytps::text', 'span[class*="year"]::text'],
            'poster_url': ['div.entry-content img::attr(src)'],
            'streaming_link': ['iframe::attr(src)']
        }

        self.MOVIE_DETAIL_FIELD_MAPPING = {
            'title': ['title', 'film title', 'film', 'movie'],
            'year': ['year', 'release year', 'film year'],
            'director': ['director', 'directed by', 'filmmaker'],
            'genre': ['genre', 'type', 'category']
        }

        self.field_mapping = {
            'title': ['h1.entry-title::text', 'h1.title::text', 'div.movie-title::text'],
            'year': ['.ytps::text', 'span[class*="year"]::text'],
            'poster_url': ['div.entry-content img::attr(src)'],
            'streaming_link': ['iframe::attr(src)']
        }

        self.field_mapping.update(FIELD_SELECTORS)
        self.field_mapping.update(self.MOVIE_DETAIL_FIELD_MAPPING)
        self.field_mapping.update(self.CATALOGUE_FIELD_MAPPING)
    def extract_links(self, response):
        selectors = [
            'div.item a::attr(href)', 'div.card a::attr(href)', 'div.movie a::attr(href)',
            'div.movie-entry a::attr(href)', 'div.movie-card a::attr(href)',
            'article a::attr(href)', 'li a::attr(href)', 'a::attr(href)'
        ]
        links = []
        for selector in selectors:
            links.extend(response.css(selector).getall())

        unique_links = set()
        for link in links:
            if not link or not isinstance(link, str):
                continue
            stripped_link = urldefrag(link.strip())[0]  # Remove any #fragment
            if is_valid_link(stripped_link, self.invalid_links):
                unique_links.add(stripped_link)

        logger.info(f"Extracted {len(unique_links)} valid links after filtering.")
        return list(unique_links)
    
    def extract_first(self, response, selectors):
        for sel in selectors:
            value = response.css(sel).get()
            if value:
                return value.strip()
        return None
    
    def extract_main_fields(self, response):
        fields = {
            'title': ['h1.entry-title::text', 'h1.title::text', 'div.movie-title::text'],
            'year': ['.ytps::text', 'span[class*="year"]::text'],
            'poster_url': ['div.entry-content img::attr(src)'],
            'streaming_link': ['iframe::attr(src)']
        }
        return {field: self.extract_first(response, selectors) for field, selectors in fields.items()}
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

    def _match_field(self, text):
        best, score = None, 0
        for field, candidates in self.MOVIE_DETAIL_FIELD_MAPPING.items():
            match, match_score = process.extractOne(text.lower(), candidates)
            if match_score > score:
                best, score = field, match_score
        return best, score

    def _clean_text(self, text):
        return text.split(':', 1)[-1].strip() if ':' in text else text