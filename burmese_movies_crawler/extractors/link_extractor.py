"""
Link extraction module for web crawling.
"""
import logging
from typing import List, Optional, Set
from urllib.parse import urldefrag, urljoin

from burmese_movies_crawler.utils.exceptions import ExtractionError
from burmese_movies_crawler.utils.link_utils import is_valid_link

logger = logging.getLogger(__name__)


class LinkExtractor:
    """
    Extracts and normalizes links from HTML responses.
    """
    
    def __init__(self, invalid_links: Optional[List[str]] = None):
        """
        Initialize the link extractor with optional invalid links.
        
        Args:
            invalid_links: List of invalid link patterns to exclude
        """
        self.invalid_links = invalid_links if invalid_links is not None else []
    
    def extract(self, response) -> List[str]:
        """
        Extract links from a response, normalize and filter them.
        
        Args:
            response: Scrapy response object
            
        Returns:
            List of normalized, valid URLs
            
        Raises:
            ExtractionError: If an error occurs during link extraction
        """
        try:
            if not response:
                logger.error("No response object provided")
                raise ExtractionError("No response object provided")

            combined_selector = (
                'div.item a::attr(href), div.card a::attr(href), div.movie a::attr(href), '
                'div.movie-entry a::attr(href), div.movie-card a::attr(href), article a::attr(href)'
            )

            try:
                # Always combine specific and generic selectors
                primary = response.css(combined_selector).getall()
                fallback = response.css('a::attr(href)').getall()
                links = list(set(primary) | set(fallback))
            except Exception as e:
                logger.error(f"Failed to extract links with CSS selector: {str(e)}")
                raise ExtractionError(f"CSS selector error: {str(e)}") from e

            unique_links: Set[str] = set()
            for link in links:
                try:
                    if not isinstance(link, str):
                        continue

                    raw = link.strip()

                    # Normalize before validation
                    resolved = urljoin(response.url, raw)
                    clean = urldefrag(resolved)[0]

                    if is_valid_link(clean, self.invalid_links):
                        unique_links.add(clean)

                except Exception as e:
                    logger.warning(f"Error processing link '{link}': {str(e)}")

            logger.info(f"Extracted {len(unique_links)} valid links after filtering.")
            return list(unique_links)

        except Exception as e:
            if not isinstance(e, ExtractionError):
                logger.error(f"Link extraction error: {str(e)}")
                raise ExtractionError(f"Failed to extract links: {str(e)}") from e
            raise