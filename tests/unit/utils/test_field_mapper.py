"""
Tests for the FieldMapper class.
"""
import pytest
from unittest.mock import patch, mock_open
import yaml

from burmese_movies_crawler.utils.field_mapper import FieldMapper, load_field_mapping
from burmese_movies_crawler.utils.exceptions import InitializationError


def test_load_field_mapping():
    """Test that load_field_mapping loads and returns the correct mapping."""
    mock_yaml_data = """
    content_types:
      movies:
        title:
          labels: ["Film Title", "Movie Title"]
          confidence_threshold: 80
        year:
          labels: ["Release Year", "Year"]
          confidence_threshold: 70
    """
    
    with patch("builtins.open", mock_open(read_data=mock_yaml_data)):
        with patch("yaml.safe_load", return_value=yaml.safe_load(mock_yaml_data)):
            mapping = load_field_mapping("movies")
            
            assert "title" in mapping
            assert "year" in mapping
            assert mapping["title"]["labels"] == ["Film Title", "Movie Title"]
            assert mapping["title"]["confidence_threshold"] == 80


def test_load_field_mapping_invalid_content_type():
    """Test that load_field_mapping raises an error for invalid content types."""
    mock_yaml_data = """
    content_types:
      movies:
        title:
          labels: ["Film Title", "Movie Title"]
    """
    
    with patch("builtins.open", mock_open(read_data=mock_yaml_data)):
        with patch("yaml.safe_load", return_value=yaml.safe_load(mock_yaml_data)):
            with pytest.raises(ValueError):
                load_field_mapping("invalid_type")


def test_field_mapper_initialization():
    """Test that FieldMapper initializes correctly."""
    with patch("burmese_movies_crawler.utils.field_mapper.load_field_mapping") as mock_load:
        mock_load.return_value = {
            "title": {
                "labels": ["Film Title", "Movie Title"],
                "confidence_threshold": 80
            },
            "year": {
                "labels": ["Release Year", "Year"],
                "confidence_threshold": 70
            }
        }
        
        mapper = FieldMapper("movies")
        
        # Verify that load_field_mapping was called
        mock_load.assert_called_once_with("movies")
        
        # Verify that field patterns were created correctly
        assert "title" in mapper._field_patterns
        assert "year" in mapper._field_patterns
        assert mapper._field_patterns["title"]["labels"] == ["Film Title", "Movie Title"]
        assert mapper._field_patterns["title"]["threshold"] == 80


def test_field_mapper_initialization_error():
    """Test that FieldMapper handles initialization errors."""
    with patch("burmese_movies_crawler.utils.field_mapper.load_field_mapping") as mock_load:
        mock_load.side_effect = ValueError("Invalid content type")
        
        with pytest.raises(InitializationError):
            FieldMapper("invalid_type")


def test_get_labels_for():
    """Test that get_labels_for returns the correct labels."""
    with patch("burmese_movies_crawler.utils.field_mapper.load_field_mapping") as mock_load:
        mock_load.return_value = {
            "title": {
                "labels": ["Film Title", "Movie Title"],
                "confidence_threshold": 80
            }
        }
        
        mapper = FieldMapper("movies")
        
        # Verify that get_labels_for returns the correct labels
        assert mapper.get_labels_for("title") == ["Film Title", "Movie Title"]
        assert mapper.get_labels_for("nonexistent") == []


def test_get_threshold_for():
    """Test that get_threshold_for returns the correct threshold."""
    with patch("burmese_movies_crawler.utils.field_mapper.load_field_mapping") as mock_load:
        mock_load.return_value = {
            "title": {
                "labels": ["Film Title", "Movie Title"],
                "confidence_threshold": 80
            }
        }
        
        mapper = FieldMapper("movies")
        
        # Verify that get_threshold_for returns the correct threshold
        assert mapper.get_threshold_for("title") == 80
        assert mapper.get_threshold_for("nonexistent") == 70  # Default threshold


def test_get_all_fields():
    """Test that get_all_fields returns all field names."""
    with patch("burmese_movies_crawler.utils.field_mapper.load_field_mapping") as mock_load:
        mock_load.return_value = {
            "title": {
                "labels": ["Film Title", "Movie Title"],
                "confidence_threshold": 80
            },
            "year": {
                "labels": ["Release Year", "Year"],
                "confidence_threshold": 70
            }
        }
        
        mapper = FieldMapper("movies")
        
        # Verify that get_all_fields returns all field names
        assert set(mapper.get_all_fields()) == {"title", "year"}


def test_get_field_patterns():
    """Test that get_field_patterns returns all field patterns."""
    with patch("burmese_movies_crawler.utils.field_mapper.load_field_mapping") as mock_load:
        mock_load.return_value = {
            "title": {
                "labels": ["Film Title", "Movie Title"],
                "confidence_threshold": 80
            }
        }
        
        mapper = FieldMapper("movies")
        
        # Verify that get_field_patterns returns all field patterns
        patterns = mapper.get_field_patterns()
        assert "title" in patterns
        assert patterns["title"]["labels"] == ["Film Title", "Movie Title"]
        assert patterns["title"]["threshold"] == 80