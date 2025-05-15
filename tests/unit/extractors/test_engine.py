"""
Tests for the ExtractorEngine class.
"""
import pytest
from unittest.mock import MagicMock, patch

from burmese_movies_crawler.extractors.engine import ExtractorEngine
from burmese_movies_crawler.utils.exceptions import FieldExtractorError


def test_extract_all():
    """Test that extract_all calls all the necessary extractors."""
    # Create mock extractors
    link_extractor = MagicMock()
    link_extractor.extract.return_value = ["https://example.com/1", "https://example.com/2"]
    
    main_field_extractor = MagicMock()
    main_field_extractor.extract.return_value = {"title": "Test Movie", "year": "2023"}
    
    paragraph_extractor = MagicMock()
    paragraph_extractor.extract.return_value = {"director": "John Doe", "genre": "Action"}
    
    table_extractor = MagicMock()
    table_items = [{"title": "Table Movie", "year": "2022"}]
    table_extractor.extract.return_value = table_items
    
    # Create the engine with mock extractors
    engine = ExtractorEngine(
        link_extractor=link_extractor,
        main_field_extractor=main_field_extractor,
        paragraph_extractor=paragraph_extractor,
        table_extractor=table_extractor
    )
    
    # Create a mock response
    response = MagicMock()
    response.css.return_value = ["table1", "table2"]
    
    # Call extract_all
    result = engine.extract_all(response)
    
    # Verify that all extractors were called
    link_extractor.extract.assert_called_once_with(response)
    main_field_extractor.extract.assert_called_once_with(response)
    paragraph_extractor.extract.assert_called_once_with(response)
    
    # Verify that the result contains the expected data
    assert result["links"] == ["https://example.com/1", "https://example.com/2"]
    assert result["main_fields"] == {"title": "Test Movie", "year": "2023"}
    assert result["paragraph_fields"] == {"director": "John Doe", "genre": "Action"}
    assert result["fields"] == {
        "title": "Test Movie", 
        "year": "2023", 
        "director": "John Doe", 
        "genre": "Action"
    }
    assert "items" in result


def test_extract_all_error_handling():
    """Test that extract_all handles errors properly."""
    # Create mock extractors that raise exceptions
    link_extractor = MagicMock()
    link_extractor.extract.side_effect = FieldExtractorError("Link extraction error")
    
    main_field_extractor = MagicMock()
    paragraph_extractor = MagicMock()
    table_extractor = MagicMock()
    
    # Create the engine with mock extractors
    engine = ExtractorEngine(
        link_extractor=link_extractor,
        main_field_extractor=main_field_extractor,
        paragraph_extractor=paragraph_extractor,
        table_extractor=table_extractor
    )
    
    # Create a mock response
    response = MagicMock()
    
    # Call extract_all and expect an exception
    with pytest.raises(FieldExtractorError):
        engine.extract_all(response)
    
    # Test with a different type of exception
    link_extractor.extract.side_effect = ValueError("Unexpected error")
    
    with pytest.raises(FieldExtractorError):
        engine.extract_all(response)