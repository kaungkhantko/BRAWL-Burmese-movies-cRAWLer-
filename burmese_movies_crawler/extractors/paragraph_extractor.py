"""
Paragraph extraction module for web content.
"""
import logging
from typing import Dict, Set

from burmese_movies_crawler.utils.exceptions import ExtractionError, ProcessingError
from burmese_movies_crawler.utils.field_matcher import FieldMatcher
from burmese_movies_crawler.utils.text_cleaner import TextCleaner

logger = logging.getLogger(__name__)

# Default confidence threshold
DEFAULT_THRESHOLD = 70


class ParagraphExtractor:
    """
    Extracts and infers fields from paragraphs in HTML responses.
    """
    
    def __init__(self, field_matcher: FieldMatcher, text_cleaner: TextCleaner):
        """
        Initialize the paragraph extractor with field matcher and text cleaner.
        
        Args:
            field_matcher: The field matcher to use for matching paragraphs to fields
            text_cleaner: The text cleaner to use for normalizing extracted text
        """
        self.field_matcher = field_matcher
        self.text_cleaner = text_cleaner
    
    def extract(self, response) -> Dict[str, str]:
        """
        Extract fields from paragraphs in a response.
        
        Args:
            response: Scrapy response object
            
        Returns:
            Dictionary of extracted fields
            
        Raises:
            ExtractionError: If an error occurs during paragraph extraction
            ProcessingError: If an error occurs during paragraph processing
        """
        try:
            if not response:
                logger.error("No response object provided")
                raise ExtractionError("No response object provided")
                
            data: Dict[str, str] = {}
            used: Set[str] = set()
            
            # We need to ensure that CSS errors are properly propagated
            # while still handling other types of errors gracefully
            try:
                paragraphs = []
                
                # First attempt to get direct text content
                paragraphs.extend(response.css('div.entry-content p::text').getall() or [])
                
                # Then try to get full paragraph content for paragraphs with HTML entities
                p_elements = response.css('div.entry-content p')
                if hasattr(p_elements, '__iter__'):  # Check if iterable
                    for p in p_elements:
                        try:
                            text = ''.join(p.css('::text').getall()).strip()
                            if text:  # Only add non-empty paragraphs
                                paragraphs.append(text)
                        except Exception as e:
                            # Skip problematic paragraphs but log the error
                            logger.warning(f"Error processing paragraph: {str(e)}")
                            continue
                            
            except Exception as e:
                logger.error(f"Failed to extract paragraphs: {str(e)}")
                raise ExtractionError(f"Failed to extract paragraphs: {str(e)}") from e
            
            # Pre-filter: only process paragraphs that are likely to contain field data
            # This avoids processing paragraphs that are too short or too long
            filtered_paragraphs = []
            for p in paragraphs:
                try:
                    p_stripped = p.strip()
                    if 5 <= len(p_stripped) <= 200:
                        filtered_paragraphs.append(p_stripped)
                except Exception as e:
                    logger.warning(f"Error processing paragraph: {str(e)}")
                    # Continue with next paragraph
            
            # Process paragraphs in batches
            for clean in filtered_paragraphs:
                try:
                    # Use field matching
                    field, score = self.field_matcher.match(clean)
                    if field and field not in used and score > DEFAULT_THRESHOLD:
                        data[field] = self.text_cleaner.clean(clean)
                        used.add(field)
                except Exception as e:
                    logger.warning(f"Error matching field for text '{clean[:30]}...': {str(e)}")
                    # Continue with next paragraph
                    
            return data
            
        except Exception as e:
            if not isinstance(e, (ExtractionError, ProcessingError)):
                logger.error(f"Paragraph extraction error: {str(e)}")
                raise ProcessingError(f"Failed to process paragraphs: {str(e)}") from e
            raise