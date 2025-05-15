# Burmese Movies Crawler - Extraction System

## Overview

This module provides a modular extraction system for web data, specifically designed for extracting movie information from various websites. The system is built with a focus on separation of concerns, testability, and maintainability.

## Architecture

The extraction system is organized into the following components:

### Extractor Engine

The `ExtractorEngine` class orchestrates the extraction process by delegating to specialized extractors:

```python
engine = create_extractor_engine()
result = engine.extract_all(response)
```

### Specialized Extractors

- **LinkExtractor**: Extracts and normalizes links from HTML responses
- **MainFieldExtractor**: Extracts main fields (title, year, etc.) using predefined selectors
- **ParagraphExtractor**: Extracts fields from paragraphs using fuzzy matching
- **TableExtractor**: Extracts structured data from tables

### Utility Services

- **FieldMapper**: Loads and provides access to field mappings
- **FieldMatcher**: Matches text to fields using fuzzy matching
- **TextCleaner**: Cleans and normalizes extracted text
- **HeaderMapper**: Maps table headers to field names

## Usage Example

```python
from burmese_movies_crawler.factory import create_extractor_engine

# Create the extractor engine with default settings
engine = create_extractor_engine()

# Extract all data from a Scrapy response
result = engine.extract_all(response)

# Access extracted data
links = result['links']
fields = result['fields']
items = result['items']
```

## Error Handling

The system uses a hierarchy of custom exceptions for better error handling:

- **FieldExtractorError**: Base exception for all extraction errors
- **InitializationError**: Error during initialization
- **ExtractionError**: Error during data extraction
- **ProcessingError**: Error during data processing
- **TableProcessingError**: Error during table processing

## Testing

Each component can be tested independently by mocking its dependencies:

```python
# Example: Testing LinkExtractor
def test_link_extractor():
    extractor = LinkExtractor()
    mock_response = create_mock_response(html="<a href='https://example.com'>Link</a>")
    links = extractor.extract(mock_response)
    assert "https://example.com" in links
```