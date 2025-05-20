"""
Extractor engine module for orchestrating web data extraction.
"""
import logging
from typing import Dict, List, Any, Optional, Generator

from burmese_movies_crawler.items import BurmeseMoviesItem
from burmese_movies_crawler.utils.exceptions import FieldExtractorError
from burmese_movies_crawler.core.extractors.link_extractor import LinkExtractor
from burmese_movies_crawler.core.extractors.main_field_extractor import MainFieldExtractor
from burmese_movies_crawler.core.extractors.paragraph_extractor import ParagraphExtractor
from burmese_movies_crawler.core.extractors.table_extractor import TableExtractor

logger = logging.getLogger(__name__)


class ExtractorEngine:
    """
    Orchestrates the extraction process using specialized extractors.
    """
    
    def __init__(
        self,
        link_extractor: LinkExtractor,
        main_field_extractor: MainFieldExtractor,
        paragraph_extractor: ParagraphExtractor,
        table_extractor: TableExtractor
    ):
        """
        Initialize the extractor engine with specialized extractors.
        
        Args:
            link_extractor: Extractor for links
            main_field_extractor: Extractor for main fields
            paragraph_extractor: Extractor for paragraphs
            table_extractor: Extractor for tables
        """
        self.link_extractor = link_extractor
        self.main_field_extractor = main_field_extractor
        self.paragraph_extractor = paragraph_extractor
        self.table_extractor = table_extractor
    
    def extract_all(self, response) -> Dict[str, Any]:
        """
        Extract all data from a response using specialized extractors.
        
        Args:
            response: Scrapy response object
            
        Returns:
            Dictionary with extracted data including links, fields, and items
            
        Raises:
            FieldExtractorError: If an error occurs during extraction
        """
        result: Dict[str, Any] = {}
        
        try:
            # Extract links
            result['links'] = self.extract_links(response)
            
            # Extract main fields
            result['main_fields'] = self.extract_main_fields(response)
            
            # Extract paragraph fields
            result['paragraph_fields'] = self.extract_paragraphs(response)
            
            # Combine all fields
            result['fields'] = {**result['main_fields'], **result['paragraph_fields']}
            
            # Extract table items
            result['items'] = list(self.extract_from_tables(response))
            
            return result
            
        except FieldExtractorError as e:
            logger.error(f"Extraction error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during extraction: {str(e)}")
            raise FieldExtractorError(f"Failed to extract data: {str(e)}") from e
    
    def extract_links(self, response) -> List[str]:
        """
        Extract links from a response.
        
        Args:
            response: Scrapy response object
            
        Returns:
            List of extracted links
        """
        return self.link_extractor.extract(response)
    
    def extract_main_fields(self, response) -> Dict[str, str]:
        """
        Extract main fields from a response.
        
        Args:
            response: Scrapy response object
            
        Returns:
            Dictionary of extracted main fields
        """
        return self.main_field_extractor.extract(response)
    
    def extract_paragraphs(self, response) -> Dict[str, str]:
        """
        Extract fields from paragraphs in a response.
        
        Args:
            response: Scrapy response object
            
        Returns:
            Dictionary of extracted paragraph fields
        """
        return self.paragraph_extractor.extract(response)
    
    def extract_from_tables(self, response) -> Generator[BurmeseMoviesItem, None, None]:
        """
        Extract items from tables in a response.
        
        Args:
            response: Scrapy response object
            
        Yields:
            BurmeseMoviesItem objects with extracted data
        """
        # Find all tables in the response
        tables = response.css('table')
        
        for table in tables:
            yield from self.table_extractor.extract(response, table)