"""
Tests for the factory module.
"""
import pytest
from unittest.mock import patch, MagicMock

from burmese_movies_crawler.factory import create_extractor_engine
from burmese_movies_crawler.extractors.engine import ExtractorEngine
from burmese_movies_crawler.extractors.link_extractor import LinkExtractor
from burmese_movies_crawler.extractors.main_field_extractor import MainFieldExtractor
from burmese_movies_crawler.extractors.paragraph_extractor import ParagraphExtractor
from burmese_movies_crawler.extractors.table_extractor import TableExtractor
from burmese_movies_crawler.utils.field_mapper import FieldMapper
from burmese_movies_crawler.utils.field_matcher import FieldMatcher
from burmese_movies_crawler.utils.header_mapper import HeaderMapper
from burmese_movies_crawler.utils.text_cleaner import TextCleaner


def test_create_extractor_engine():
    """Test that create_extractor_engine creates an ExtractorEngine with all dependencies."""
    # Mock all the dependencies
    with patch('burmese_movies_crawler.factory.FieldMapper') as mock_field_mapper, \
         patch('burmese_movies_crawler.factory.FieldMatcher') as mock_field_matcher, \
         patch('burmese_movies_crawler.factory.TextCleaner') as mock_text_cleaner, \
         patch('burmese_movies_crawler.factory.HeaderMapper') as mock_header_mapper, \
         patch('burmese_movies_crawler.factory.LinkExtractor') as mock_link_extractor, \
         patch('burmese_movies_crawler.factory.MainFieldExtractor') as mock_main_field_extractor, \
         patch('burmese_movies_crawler.factory.ParagraphExtractor') as mock_paragraph_extractor, \
         patch('burmese_movies_crawler.factory.TableExtractor') as mock_table_extractor, \
         patch('burmese_movies_crawler.factory.ExtractorEngine') as mock_extractor_engine:
        
        # Create instances of the mocks
        mock_field_mapper_instance = MagicMock()
        mock_field_matcher_instance = MagicMock()
        mock_text_cleaner_instance = MagicMock()
        mock_header_mapper_instance = MagicMock()
        mock_link_extractor_instance = MagicMock()
        mock_main_field_extractor_instance = MagicMock()
        mock_paragraph_extractor_instance = MagicMock()
        mock_table_extractor_instance = MagicMock()
        mock_extractor_engine_instance = MagicMock()
        
        # Configure the mocks to return the instances
        mock_field_mapper.return_value = mock_field_mapper_instance
        mock_field_matcher.return_value = mock_field_matcher_instance
        mock_text_cleaner.return_value = mock_text_cleaner_instance
        mock_header_mapper.return_value = mock_header_mapper_instance
        mock_link_extractor.return_value = mock_link_extractor_instance
        mock_main_field_extractor.return_value = mock_main_field_extractor_instance
        mock_paragraph_extractor.return_value = mock_paragraph_extractor_instance
        mock_table_extractor.return_value = mock_table_extractor_instance
        mock_extractor_engine.return_value = mock_extractor_engine_instance
        
        # Call the factory function
        engine = create_extractor_engine(content_type="movies", invalid_links=["bad.com"])
        
        # Verify that all the dependencies were created with the correct parameters
        mock_field_mapper.assert_called_once_with("movies")
        mock_field_matcher.assert_called_once_with(mock_field_mapper_instance)
        mock_text_cleaner.assert_called_once_with()
        mock_header_mapper.assert_called_once_with(mock_field_matcher_instance)
        mock_link_extractor.assert_called_once_with(["bad.com"])
        mock_main_field_extractor.assert_called_once_with(mock_text_cleaner_instance)
        mock_paragraph_extractor.assert_called_once_with(mock_field_matcher_instance, mock_text_cleaner_instance)
        mock_table_extractor.assert_called_once_with(mock_header_mapper_instance)
        
        # Verify that the ExtractorEngine was created with the correct dependencies
        mock_extractor_engine.assert_called_once_with(
            link_extractor=mock_link_extractor_instance,
            main_field_extractor=mock_main_field_extractor_instance,
            paragraph_extractor=mock_paragraph_extractor_instance,
            table_extractor=mock_table_extractor_instance
        )
        
        # Verify that the factory function returns the ExtractorEngine instance
        assert engine == mock_extractor_engine_instance


def test_create_extractor_engine_with_defaults():
    """Test that create_extractor_engine uses default values when not provided."""
    # Create a real engine with default parameters
    engine = create_extractor_engine()
    
    # Verify that the engine is an instance of ExtractorEngine
    assert isinstance(engine, ExtractorEngine)
    
    # Verify that the engine has all the required dependencies
    assert isinstance(engine.link_extractor, LinkExtractor)
    assert isinstance(engine.main_field_extractor, MainFieldExtractor)
    assert isinstance(engine.paragraph_extractor, ParagraphExtractor)
    assert isinstance(engine.table_extractor, TableExtractor)