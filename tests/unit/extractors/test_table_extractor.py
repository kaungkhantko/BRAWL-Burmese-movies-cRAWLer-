"""
Tests for the TableExtractor class.
"""
import pytest
from unittest.mock import MagicMock, patch
from scrapy.http import HtmlResponse, Request

from burmese_movies_crawler.extractors.table_extractor import TableExtractor
from burmese_movies_crawler.utils.exceptions import TableProcessingError
from burmese_movies_crawler.items import BurmeseMoviesItem


def fake_response(url, body, status=200, meta=None):
    """
    Create a mock HtmlResponse object for testing Scrapy components.
    """
    if isinstance(body, str):
        body = body.encode('utf-8')
    return HtmlResponse(
        url=url,
        body=body,
        encoding='utf-8',
        status=status,
        request=Request(url=url, meta=meta or {})
    )


@pytest.fixture
def header_mapper():
    """Fixture for HeaderMapper with mocked map method."""
    mapper = MagicMock()
    return mapper


@pytest.fixture
def extractor(header_mapper):
    """Fixture for TableExtractor with mocked dependencies."""
    return TableExtractor(header_mapper)


@pytest.mark.parametrize(
    "html, mapped_headers, expected",
    [
        # Normal case
        (
            """
            <table>
                <thead><tr><th>Title</th><th>Year</th></tr></thead>
                <tbody><tr><td>Test Film</td><td>2021</td></tr></tbody>
            </table>
            """,
            {"Title": "title", "Year": "year"},
            [{"title": "Test Film", "year": "2021"}]
        ),

        # Extra whitespace and mixed case headers
        (
            """
            <table>
                <thead><tr><th>  TITLE </th><th> year </th></tr></thead>
                <tbody><tr><td> Movie A </td><td> 2022 </td></tr></tbody>
            </table>
            """,
            {"TITLE": "title", "year": "year"},
            [{"title": "Movie A", "year": "2022"}]
        ),

        # Missing value in one column
        (
            """
            <table>
                <thead><tr><th>Title</th><th>Year</th></tr></thead>
                <tbody><tr><td></td><td>2020</td></tr></tbody>
            </table>
            """,
            {"Title": "title", "Year": "year"},
            [{"year": "2020"}]
        ),

        # Irrelevant headers ignored
        (
            """
            <table>
                <thead><tr><th>Random</th><th>Title</th></tr></thead>
                <tbody><tr><td>XYZ</td><td>Actual Movie</td></tr></tbody>
            </table>
            """,
            {"Title": "title"},
            [{"title": "Actual Movie"}]
        ),

        # Multilingual headers
        (
            """
            <table>
                <thead><tr><th>ဇာတ်ကားအမည်</th><th>နှစ်</th></tr></thead>
                <tbody><tr><td>မြန်မာဖလင်မ်</td><td>၂၀၁၉</td></tr></tbody>
            </table>
            """,
            {"ဇာတ်ကားအမည်": "title", "နှစ်": "year"},
            [{"title": "မြန်မာဖလင်မ်", "year": "၂၀၁၉"}]
        ),

        # No <thead> tag
        (
            """
            <table>
                <tr><th>Title</th><th>Year</th></tr>
                <tr><td>Alt Header Movie</td><td>2023</td></tr>
            </table>
            """,
            {"Title": "title", "Year": "year"},
            [{"title": "Alt Header Movie", "year": "2023"}]
        ),
    ]
)
def test_extract_from_table_variants(extractor, html, mapped_headers, expected):
    """Test that extract correctly extracts data from tables."""
    response = fake_response("https://example.com", html)
    
    # Configure the header_mapper mock to return the specified mapping
    extractor.header_mapper.map.return_value = mapped_headers
    
    # Get the table element from the response
    table = response.css("table")[0]
    
    # Extract items from the table
    items = list(extractor.extract(response, table))
    
    # Verify the extracted items
    assert len(items) == len(expected)
    for item, expected_values in zip(items, expected):
        assert isinstance(item, BurmeseMoviesItem)
        for field, value in expected_values.items():
            assert item.get(field) == value
    
    # Verify that items_scraped was incremented
    assert extractor.items_scraped == len(expected)


def test_extract_with_none_response(extractor):
    """Test that extract correctly handles None response."""
    with pytest.raises(TableProcessingError):
        list(extractor.extract(None, "table"))


def test_extract_with_none_table(extractor):
    """Test that extract correctly handles None table."""
    response = fake_response("https://example.com", "<html></html>")
    
    with pytest.raises(TableProcessingError):
        list(extractor.extract(response, None))


def test_extract_with_no_headers(extractor):
    """Test that extract correctly handles tables with no headers."""
    # Create a mock table that returns empty headers
    class EmptyHeadersTable:
        def css(self, selector):
            if "thead" in selector or "tr:first-child" in selector:
                class EmptyResult:
                    def getall(self):
                        return []
                return EmptyResult()
            return []
    
    response = fake_response("https://example.com", "<table></table>")
    
    # Should return empty generator, not raise exception
    items = list(extractor.extract(response, EmptyHeadersTable()))
    assert len(items) == 0


def test_extract_with_header_mapping_error(extractor):
    """Test that extract correctly handles header mapping errors."""
    html = """
        <table>
            <thead><tr><th>Title</th><th>Year</th></tr></thead>
            <tbody><tr><td>Test Film</td><td>2021</td></tr></tbody>
        </table>
    """
    response = fake_response("https://example.com", html)
    table = response.css("table")[0]
    
    # Configure the header_mapper mock to raise an exception
    extractor.header_mapper.map.side_effect = Exception("Header mapping error")
    
    with pytest.raises(TableProcessingError):
        list(extractor.extract(response, table))


def test_extract_with_row_processing_error(extractor):
    """Test that extract correctly handles row processing errors."""
    # Create a mock table with headers but that raises an exception when getting rows
    class BadTable:
        def css(self, selector):
            if "thead" in selector:
                class HeaderResult:
                    def getall(self):
                        return ["Header1", "Header2"]
                return HeaderResult()
            elif "tbody tr" in selector:
                raise Exception("Row processing error")
            return []
    
    response = fake_response("https://example.com", "<table></table>")
    
    # Configure the header_mapper mock to return a mapping
    extractor.header_mapper.map.return_value = {"Header1": "field1", "Header2": "field2"}
    
    with pytest.raises(TableProcessingError):
        list(extractor.extract(response, BadTable()))


def test_extract_with_cell_processing_error(extractor):
    """Test that extract correctly handles cell processing errors."""
    # Create a mock table with headers and rows but that raises an exception when getting cells
    class BadRowsTable:
        def css(self, selector):
            if "thead" in selector:
                class HeaderResult:
                    def getall(self):
                        return ["Title", "Year"]
                return HeaderResult()
            elif "tbody tr" in selector:
                return [MagicMock()]  # Return a mock row
            elif "tr:first-child" in selector:
                # Return empty for the fallback header selector
                class EmptyResult:
                    def getall(self):
                        return []
                return EmptyResult()
            return []
    
    # Create a mock row that raises an exception when getting cells
    mock_row = MagicMock()
    mock_row.css.side_effect = Exception("Cell processing error")
    
    response = fake_response("https://example.com", "<table></table>")
    
    # Configure the header_mapper mock to return a mapping
    extractor.header_mapper.map.return_value = {"Title": "title", "Year": "year"}
    
    # Create a table instance without using lambda to avoid recursion
    table = BadRowsTable()
    original_css = table.css
    
    # Define a non-recursive function to replace css
    def modified_css(selector):
        if "tbody tr" in selector:
            return [mock_row]
        else:
            return original_css(selector)
    
    # Replace the css method
    table.css = modified_css
    
    # Should handle the error and return an empty list
    items = list(extractor.extract(response, table))
    assert len(items) == 0


def test_create_item():
    """Test that _create_item correctly creates an item from cells and headers."""
    extractor = TableExtractor(MagicMock())
    
    cells = ["Test Film", "2021", "Director Name"]
    headers = ["Title", "Year", "Director"]
    header_map = {"Title": "title", "Year": "year", "Director": "director"}
    
    item = extractor._create_item(cells, headers, header_map)
    
    assert isinstance(item, BurmeseMoviesItem)
    assert item["title"] == "Test Film"
    assert item["year"] == "2021"
    assert item["director"] == "Director Name"