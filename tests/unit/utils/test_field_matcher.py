"""
Tests for the FieldMatcher class.
"""
import pytest
from unittest.mock import MagicMock, patch

from burmese_movies_crawler.utils.field_matcher import FieldMatcher
from burmese_movies_crawler.utils.exceptions import ProcessingError


def test_match_with_exact_match():
    """Test that match correctly identifies an exact match."""
    # Create a mock field mapper
    field_mapper = MagicMock()
    field_mapper.get_field_patterns.return_value = {
        "title": {
            "labels": ["Film Title", "Movie Title"],
            "threshold": 80
        },
        "director": {
            "labels": ["Director", "Directed By"],
            "threshold": 70
        }
    }
    
    matcher = FieldMatcher(field_mapper)
    
    # Test with an exact match
    field, score = matcher.match("Film Title")
    
    assert field == "title"
    assert score >= 80


def test_match_with_fuzzy_match():
    """Test that match correctly identifies a fuzzy match."""
    # Create a mock field mapper
    field_mapper = MagicMock()
    field_mapper.get_field_patterns.return_value = {
        "title": {
            "labels": ["Film Title", "Movie Title"],
            "threshold": 80
        },
        "director": {
            "labels": ["Director", "Directed By"],
            "threshold": 70
        }
    }
    
    matcher = FieldMatcher(field_mapper)
    
    # Test with a fuzzy match
    field, score = matcher.match("Film Titles")
    
    assert field == "title"
    assert score >= 80


def test_match_with_no_match():
    """Test that match correctly handles no match."""
    # Create a mock field mapper
    field_mapper = MagicMock()
    field_mapper.get_field_patterns.return_value = {
        "title": {
            "labels": ["Film Title", "Movie Title"],
            "threshold": 80
        },
        "director": {
            "labels": ["Director", "Directed By"],
            "threshold": 70
        }
    }
    
    matcher = FieldMatcher(field_mapper)
    
    # Test with no match
    field, score = matcher.match("Something Completely Different")
    
    assert field is None
    assert score == 0


def test_match_with_empty_input():
    """Test that match correctly handles empty input."""
    # Create a mock field mapper
    field_mapper = MagicMock()
    field_mapper.get_field_patterns.return_value = {}
    
    matcher = FieldMatcher(field_mapper)
    
    # Test with empty input
    field, score = matcher.match("")
    
    assert field is None
    assert score == 0
    
    field, score = matcher.match(None)
    
    assert field is None
    assert score == 0


def test_match_with_multiple_matches():
    """Test that match correctly handles multiple matches."""
    # Create a mock field mapper
    field_mapper = MagicMock()
    field_mapper.get_field_patterns.return_value = {
        "title": {
            "labels": ["Film Title", "Movie Title"],
            "threshold": 80
        },
        "name": {
            "labels": ["Film Title", "Movie Name"],
            "threshold": 80
        }
    }
    
    # Mock the fuzzywuzzy process.extractOne function
    with patch("burmese_movies_crawler.utils.field_matcher.process") as mock_process:
        # Set up the mock to return different scores for different fields
        def mock_extract_one(text, choices):
            if "title" in choices:
                return "Film Title", 90
            elif "name" in choices:
                return "Film Title", 85
            return None, 0
        
        mock_process.extractOne = mock_extract_one
        
        matcher = FieldMatcher(field_mapper)
        
        # Test with multiple matches
        field, score = matcher.match("Film Title")
        
        # Should return the field with the highest score
        assert field == "title"
        assert score == 90


def test_match_with_error():
    """Test that match correctly handles errors."""
    # Create a mock field mapper
    field_mapper = MagicMock()
    field_mapper.get_field_patterns.return_value = {
        "title": {
            "labels": ["Film Title", "Movie Title"],
            "threshold": 80
        }
    }
    
    # Mock the fuzzywuzzy process.extractOne function to raise an exception
    with patch("burmese_movies_crawler.utils.field_matcher.process") as mock_process:
        mock_process.extractOne.side_effect = Exception("Fuzzy matching error")
        
        matcher = FieldMatcher(field_mapper)
        
        # Test with an error
        with pytest.raises(ProcessingError):
            matcher.match("Film Title")


def test_match_caching():
    """Test that match uses caching for performance."""
    # Create a mock field mapper
    field_mapper = MagicMock()
    field_mapper.get_field_patterns.return_value = {
        "title": {
            "labels": ["Film Title", "Movie Title"],
            "threshold": 80
        }
    }
    
    # Mock the fuzzywuzzy process.extractOne function
    with patch("burmese_movies_crawler.utils.field_matcher.process") as mock_process:
        mock_process.extractOne.return_value = ("Film Title", 90)
        
        matcher = FieldMatcher(field_mapper)
        
        # Call match with the same input multiple times
        field1, score1 = matcher.match("Film Title")
        field2, score2 = matcher.match("Film Title")
        
        # The results should be the same
        assert field1 == field2
        assert score1 == score2
        
        # And process.extractOne should only be called once
        assert mock_process.extractOne.call_count == 1
        
        # Call with a different input
        field3, score3 = matcher.match("Movie Title")
        
        # process.extractOne should be called again
        assert mock_process.extractOne.call_count == 2