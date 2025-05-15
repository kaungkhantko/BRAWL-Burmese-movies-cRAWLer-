"""
Field matching utilities using fuzzy matching.
"""
import functools
import logging
from typing import Dict, Tuple, Optional, List

from fuzzywuzzy import process
from burmese_movies_crawler.utils.exceptions import ProcessingError
from burmese_movies_crawler.utils.field_mapper import FieldMapper

logger = logging.getLogger(__name__)


class FieldMatcher:
    """
    Matches text to fields using fuzzy matching with caching.
    """
    
    def __init__(self, field_mapper: FieldMapper):
        """
        Initialize the field matcher with a field mapper.
        
        Args:
            field_mapper: The field mapper to use for field patterns
        """
        self.field_mapper = field_mapper
        self._field_match_cache: Dict[str, Tuple[Optional[str], int]] = {}
    
    @functools.lru_cache(maxsize=128)
    def match(self, text: str) -> Tuple[Optional[str], int]:
        """
        Match text to a field using fuzzy matching with caching.
        
        Args:
            text: The text to match against field labels
            
        Returns:
            Tuple of (field_name, confidence_score)
            
        Raises:
            ProcessingError: If an error occurs during matching
        """
        try:
            if not text:
                return None, 0
                
            # Check if we already processed this text
            text_lower = text.lower()
            if text_lower in self._field_match_cache:
                return self._field_match_cache[text_lower]
                
            best_field, best_score = None, 0
            
            # Use pre-computed field patterns for faster matching
            for field, pattern in self.field_mapper.get_field_patterns().items():
                try:
                    labels = pattern.get('labels', [])
                    if not labels:
                        continue
                        
                    match, match_score = process.extractOne(text_lower, labels)
                    threshold = pattern.get('threshold', 70)
                    
                    if match_score > best_score and match_score >= threshold:
                        best_field, best_score = field, match_score
                except Exception as e:
                    logger.warning(f"Error matching field '{field}': {str(e)}")
                    # Continue with next field
                    
            # Cache the result
            self._field_match_cache[text_lower] = (best_field, best_score)
            return best_field, best_score
            
        except Exception as e:
            logger.error(f"Field matching error for text '{text[:30]}...': {str(e)}")
            raise ProcessingError(f"Failed to match field: {str(e)}") from e