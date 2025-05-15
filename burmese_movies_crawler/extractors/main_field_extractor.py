"""
Main field extraction module for web content.
"""
import logging
from typing import Dict, List, Optional

from burmese_movies_crawler.utils.exceptions import ExtractionError
from burmese_movies_crawler.utils.text_cleaner import TextCleaner

logger = logging.getLogger(__name__)


class MainFieldExtractor:
    """
    Extracts main fields from HTML responses using predefined selectors.
    """
    
    def __init__(self, text_cleaner: TextCleaner):
        """
        Initialize the main field extractor with a text cleaner.
        
        Args:
            text_cleaner: The text cleaner to use for normalizing extracted text
        """
        self.text_cleaner = text_cleaner
    
    def extract(self, response) -> Dict[str, str]:
        """
        Extract main fields from a response using predefined selectors.
        
        Args:
            response: Scrapy response object
            
        Returns:
            Dictionary of extracted fields
            
        Raises:
            ExtractionError: If an error occurs during field extraction
        """
        try:
            if not response:
                logger.error("No response object provided")
                raise ExtractionError("No response object provided")
                
            # Define fields with prioritized selectors (most specific first)
            fields = {
                'title': ['h1.entry-title::text', 'h1.title::text', 'div.movie-title::text'],
                'year': ['.ytps::text', 'span[class*="year"]::text'],
                'poster_url': ['div.entry-content img::attr(src)'],
                'streaming_link': ['iframe::attr(src)']
            }
            
            # Process all fields in a batch
            results = {}
            for field, selectors in fields.items():
                try:
                    value = self.extract_field_value(response, selectors)
                    if value:
                        results[field] = value
                except Exception as e:
                    logger.warning(f"Error extracting field '{field}': {str(e)}")
                    # Continue with next field
                    
            return results
            
        except Exception as e:
            if not isinstance(e, ExtractionError):
                logger.error(f"Main fields extraction error: {str(e)}")
                raise ExtractionError(f"Failed to extract main fields: {str(e)}") from e
            raise
    
    def extract_field_value(self, response, selectors: List[str]) -> Optional[str]:
        """
        Extract the first matching value from a list of selectors.
        
        Args:
            response: Scrapy response object
            selectors: List of CSS selectors to try
            
        Returns:
            Extracted and cleaned text, or None if not found
            
        Raises:
            ExtractionError: If an error occurs during extraction
        """
        try:
            if not response:
                logger.error("No response object provided")
                raise ExtractionError("No response object provided")
                
            if not selectors:
                logger.warning("No selectors provided")
                return None
                
            # Create a combined selector for more efficient querying
            if len(selectors) > 1:
                try:
                    combined_selector = ', '.join(selectors)
                    matches = response.css(combined_selector)
                    if matches:
                        value = matches.get()
                        if value:
                            return self.text_cleaner.clean(value)
                except Exception as e:
                    logger.warning(f"Error with combined selector: {str(e)}")
                    # Fall through to individual selectors
            
            # If combined selector didn't work, try individual selectors
            # This is a fallback for complex selectors that can't be combined
            for sel in selectors:
                try:
                    matches = response.css(sel)
                    if matches:
                        value = matches.get()
                        if value:
                            return self.text_cleaner.clean(value)
                        
                        # Fallback: get text content even if it's nested inside
                        try:
                            nested_text = matches.xpath('string()').get()
                            if nested_text and nested_text.strip():
                                return self.text_cleaner.clean(nested_text)
                        except Exception as e:
                            logger.warning(f"Error getting nested text for selector '{sel}': {str(e)}")
                except Exception as e:
                    logger.warning(f"Error with selector '{sel}': {str(e)}")
                    # Continue with next selector
            
            return None
            
        except Exception as e:
            if not isinstance(e, ExtractionError):
                logger.error(f"Extract field value error: {str(e)}")
                raise ExtractionError(f"Failed to extract field value: {str(e)}") from e
            raise