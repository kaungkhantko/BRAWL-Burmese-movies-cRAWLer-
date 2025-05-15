"""
Tests for the HeaderMapper class.
"""
import pytest
from unittest.mock import MagicMock, patch

from burmese_movies_crawler.utils.header_mapper import HeaderMapper
from burmese_movies_crawler.utils.exceptions import TableProcessingError


def test_map_with_exact_matches():
    """Test that map correctly maps headers with exact matches."""
    # Create a mock field matcher
    field_matcher = MagicMock()
    field_matcher.match.side_effect = lambda text: {
        "title": ("title", 90),
        "year": ("year", 85),
        "director": ("director", 80),
        "unknown": (None, 0)
    }.get(text.lower(), (None, 0))
    
    mapper = HeaderMapper(field_matcher)
    
    # Test with exact matches
    headers = ["Title", "Year", "Director", "Unknown"]
    result = mapper.map(headers)
    
    assert result == {"Title": "title", "Year": "year", "Director": "director"}
    
    # Verify that field_matcher.match was called for each header
    assert field_matcher.match.call_count == 4


def test_map_with_empty_input():
    """Test that map correctly handles empty input."""
    # Create a mock field matcher
    field_matcher = MagicMock()
    
    mapper = HeaderMapper(field_matcher)
    
    # Test with empty input
    result = mapper.map([])
    
    assert result == {}
    
    # Verify that field_matcher.match was not called
    field_matcher.match.assert_not_called()
    
    # Test with None input
    result = mapper.map(None)
    
    assert result == {}


def test_map_with_cache():
    """Test that map uses caching for performance."""
    # Create a mock field matcher
    field_matcher = MagicMock()
    field_matcher.match.side_effect = lambda text: {
        "title": ("title", 90),
        "year": ("year", 85)
    }.get(text.lower(), (None, 0))
    
    mapper = HeaderMapper(field_matcher)
    
    # Call map with the same headers multiple times
    headers = ["Title", "Year"]
    result1 = mapper.map(headers)
    result2 = mapper.map(headers)
    
    # The results should be the same
    assert result1 == result2
    
    # And field_matcher.match should only be called once for each header
    assert field_matcher.match.call_count == 2
    
    # Call with different headers
    headers2 = ["Title", "Year", "Director"]
    result3 = mapper.map(headers2)
    
    # field_matcher.match should be called for the new header
    assert field_matcher.match.call_count == 3


def test_map_with_error():
    """Test that map correctly handles errors."""
    # Create a mock field matcher
    field_matcher = MagicMock()
    field_matcher.match.side_effect = Exception("Matching error")
    
    mapper = HeaderMapper(field_matcher)
    
    # Test with an error
    with pytest.raises(TableProcessingError):
        mapper.map(["Title", "Year"])


def test_map_with_cache_error():
    """Test that map correctly handles cache errors."""
    # Create a mock field matcher
    field_matcher = MagicMock()
    field_matcher.match.return_value = ("title", 90)
    
    mapper = HeaderMapper(field_matcher)
    
    # Mock the cache key creation to raise an exception
    with patch("burmese_movies_crawler.utils.header_mapper.tuple") as mock_tuple:
        mock_tuple.side_effect = Exception("Cache key error")
        
        # Should continue without caching
        result = mapper.map(["Title", "Year"])
        
        assert result == {"Title": "title", "Year": "title"}


def test_map_with_cache_lookup_error():
    """Test that map correctly handles cache lookup errors."""
    # Create a mock field matcher
    field_matcher = MagicMock()
    field_matcher.match.return_value = ("title", 90)
    
    mapper = HeaderMapper(field_matcher)
    
    # Create a mock cache that raises an exception on lookup
    class MockCache(dict):
        def __contains__(self, key):
            raise Exception("Cache lookup error")
    
    # Replace the cache with our mock
    mapper._header_map_cache = MockCache()
    
    # Should continue without using the cache
    result = mapper.map(["Title", "Year"])
    
    assert result == {"Title": "title", "Year": "title"}