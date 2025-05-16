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
            
            # Try each selector individually
            for sel in selectors:
                try:
                    # Handle text extraction for nested elements
                    if "::text" not in sel and "::attr" not in sel:
                        # For selectors without ::text, add it to get direct text
                        direct_text_sel = f"{sel}::text"
                        value = response.css(direct_text_sel).get()
                        if value and value.strip():
                            return self.text_cleaner.clean(value)
                            
                        # If no direct text, try to get text from nested elements
                        element_sel = sel
                        nested_text = response.css(f"{element_sel} *::text").get()
                        if nested_text and nested_text.strip():
                            return self.text_cleaner.clean(nested_text)
                    else:
                        # For selectors with ::text or ::attr, use as is
                        value = response.css(sel).get()
                        if value and (isinstance(value, str) and value.strip()):
                            return self.text_cleaner.clean(value)
                            
                except Exception as e:
                    logger.warning(f"Error with selector '{sel}': {str(e)}")
                    # Continue with next selector
            
            # If we get here, try one more approach with XPath for nested content
            for sel in selectors:
                try:
                    # Extract the base selector without ::text or ::attr
                    base_sel = sel.split("::")[0] if "::" in sel else sel
                    
                    # Use XPath to get all text nodes
                    xpath_result = response.css(base_sel).xpath("string()").get()
                    if xpath_result and xpath_result.strip():
                        return self.text_cleaner.clean(xpath_result)
                except Exception as e:
                    logger.warning(f"Error with XPath fallback for '{sel}': {str(e)}")
            
            return None
            
        except Exception as e:
            if not isinstance(e, ExtractionError):
                logger.error(f"Extract field value error: {str(e)}")
                raise ExtractionError(f"Failed to extract field value: {str(e)}")
            raise
            
            return None
            
        except Exception as e:
            if not isinstance(e, ExtractionError):
                logger.error(f"Extract field value error: {str(e)}")
                raise ExtractionError(f"Failed to extract field value: {str(e)}") from e
            raise