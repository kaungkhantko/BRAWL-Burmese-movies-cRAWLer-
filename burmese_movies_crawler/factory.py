"""
Factory module for creating extractor components.
"""
from typing import List, Optional

from burmese_movies_crawler.core.extractors.engine import ExtractorEngine
from burmese_movies_crawler.core.extractors.link_extractor import LinkExtractor
from burmese_movies_crawler.core.extractors.main_field_extractor import MainFieldExtractor
from burmese_movies_crawler.core.extractors.paragraph_extractor import ParagraphExtractor
from burmese_movies_crawler.core.extractors.table_extractor import TableExtractor
from burmese_movies_crawler.utils.field_mapper import FieldMapper
from burmese_movies_crawler.utils.field_matcher import FieldMatcher
from burmese_movies_crawler.utils.header_mapper import HeaderMapper
from burmese_movies_crawler.utils.text_cleaner import TextCleaner


def create_extractor_engine(
    content_type: str = "movies",
    invalid_links: Optional[List[str]] = None
) -> ExtractorEngine:
    """
    Create an ExtractorEngine with all necessary dependencies.
    
    Args:
        content_type: The type of content to extract (default: "movies")
        invalid_links: List of invalid link patterns to exclude
        
    Returns:
        Configured ExtractorEngine instance
    """
    # Create shared utilities
    field_mapper = FieldMapper(content_type)
    field_matcher = FieldMatcher(field_mapper)
    text_cleaner = TextCleaner()
    header_mapper = HeaderMapper(field_matcher)
    
    # Create specialized extractors
    link_extractor = LinkExtractor(invalid_links)
    main_field_extractor = MainFieldExtractor(text_cleaner)
    paragraph_extractor = ParagraphExtractor(field_matcher, text_cleaner)
    table_extractor = TableExtractor(header_mapper)
    
    # Create and return the engine
    return ExtractorEngine(
        link_extractor=link_extractor,
        main_field_extractor=main_field_extractor,
        paragraph_extractor=paragraph_extractor,
        table_extractor=table_extractor
    )