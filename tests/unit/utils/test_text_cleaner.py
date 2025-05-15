"""
Tests for the TextCleaner class.
"""
import pytest
import re
from unittest.mock import patch

from burmese_movies_crawler.utils.text_cleaner import TextCleaner, CLEAN_TEXT_PATTERN


def test_clean_text_with_colon():
    """Test that clean correctly handles text with a colon separator."""
    cleaner = TextCleaner()
    assert cleaner.clean("Director: John Doe") == "John Doe"
    assert cleaner.clean("Title: The Movie") == "The Movie"


def test_clean_text_with_dash():
    """Test that clean correctly handles text with a dash separator."""
    cleaner = TextCleaner()
    assert cleaner.clean("Director - John Doe") == "John Doe"
    assert cleaner.clean("Title - The Movie") == "The Movie"


def test_clean_text_with_unicode_dash():
    """Test that clean correctly handles text with a unicode dash separator."""
    cleaner = TextCleaner()
    assert cleaner.clean("Director – John Doe") == "John Doe"
    assert cleaner.clean("Title – The Movie") == "The Movie"


def test_clean_text_without_separator():
    """Test that clean correctly handles text without a separator."""
    cleaner = TextCleaner()
    assert cleaner.clean("John Doe") == "John Doe"
    assert cleaner.clean("The Movie") == "The Movie"


def test_clean_text_with_whitespace():
    """Test that clean correctly handles text with extra whitespace."""
    cleaner = TextCleaner()
    assert cleaner.clean("  Director:  John Doe  ") == "John Doe"
    assert cleaner.clean("  Title  -  The Movie  ") == "The Movie"


def test_clean_text_with_non_breaking_space():
    """Test that clean correctly handles text with non-breaking spaces."""
    cleaner = TextCleaner()
    assert cleaner.clean("Director:\xa0John Doe") == "John Doe"
    assert cleaner.clean("Title\xa0-\xa0The Movie") == "The Movie"


def test_clean_text_with_empty_input():
    """Test that clean correctly handles empty input."""
    cleaner = TextCleaner()
    assert cleaner.clean("") == ""
    assert cleaner.clean(None) == ""


def test_clean_text_with_multiple_separators():
    """Test that clean correctly handles text with multiple separators."""
    cleaner = TextCleaner()
    assert cleaner.clean("Director: John: Doe") == "John: Doe"
    assert cleaner.clean("Title - The - Movie") == "The - Movie"


def test_clean_text_with_regex_error():
    """Test that clean handles regex errors gracefully."""
    cleaner = TextCleaner()
    
    # Replace the pattern with one that will raise an exception
    original_pattern = cleaner._pattern
    try:
        # Mock the regex split to raise an exception
        with patch.object(CLEAN_TEXT_PATTERN, 'split', side_effect=Exception("Regex error")):
            # Should fall back to simple cleaning
            assert cleaner.clean("Director: John Doe") == "Director: John Doe"
    finally:
        # Restore the original pattern
        cleaner._pattern = original_pattern


def test_clean_text_caching():
    """Test that clean uses caching for performance."""
    cleaner = TextCleaner()
    
    # Call clean with the same input multiple times
    result1 = cleaner.clean("Director: John Doe")
    result2 = cleaner.clean("Director: John Doe")
    
    # The results should be the same
    assert result1 == result2
    
    # And the second call should use the cache
    # This is hard to test directly, but we can verify that the function has an lru_cache decorator
    assert hasattr(cleaner.clean, '__wrapped__')