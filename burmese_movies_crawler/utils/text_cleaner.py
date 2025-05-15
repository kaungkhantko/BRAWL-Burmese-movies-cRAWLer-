"""
Text cleaning utilities for data extraction.
"""
import re
import functools
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Compiled regex pattern for text cleaning
CLEAN_TEXT_PATTERN = re.compile(r'[:\-–]', re.UNICODE)


class TextCleaner:
    """
    Handles text cleaning and normalization with caching for performance.
    """
    
    def __init__(self):
        """Initialize the TextCleaner with regex patterns."""
        self._pattern = CLEAN_TEXT_PATTERN
    
    @functools.lru_cache(maxsize=128)
    def clean(self, text: Optional[str]) -> str:
        """
        Clean text using efficient regex operations with caching.
        
        Args:
            text: The text to clean
            
        Returns:
            Cleaned and normalized text string
        """
        try:
            if not text:
                return ""
                
            # Replace non-breaking space
            text = text.replace('\xa0', ' ')
            
            try:
                # Use pre-compiled regex pattern for splitting
                parts = self._pattern.split(text, maxsplit=1)
                
                # Extract value part efficiently
                return parts[-1].strip() if len(parts) > 1 else text.strip()
            except Exception as e:
                logger.warning(f"Error cleaning text with regex: {str(e)}")
                # Fallback to simple cleaning
                return text.strip()
                
        except Exception as e:
            logger.error(f"Text cleaning error: {str(e)}")
            return text.strip() if text else ""