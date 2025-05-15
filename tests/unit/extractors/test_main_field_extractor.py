"""
Tests for the MainFieldExtractor class.
"""
import pytest
from unittest.mock import MagicMock, patch
from scrapy.http import HtmlResponse, Request

from burmese_movies_crawler.extractors.main_field_extractor import MainFieldExtractor
from burmese_movies_crawler.utils.exceptions import ExtractionError
from burmese_movies_crawler.utils.text_cleaner import TextCleaner


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
def text_cleaner():
    """Fixture for TextCleaner with mocked clean method."""
    cleaner = MagicMock()
    cleaner.clean.side_effect = lambda text: text.strip() if text else ""
    return cleaner


@pytest.fixture
def extractor(text_cleaner):
    """Fixture for MainFieldExtractor with mocked dependencies."""
    return MainFieldExtractor(text_cleaner)


@pytest.mark.parametrize(
    "html, expected",
    [
        # Normal case
        (
            """
            <html>
                <h1 class="entry-title">Test Movie</h1>
                <span class="ytps">2023</span>
                <div class="entry-content"><img src="poster.jpg" /></div>
                <iframe src="https://streaming.com/video"></iframe>
            </html>
            """,
            {
                "title": "Test Movie",
                "year": "2023",
                "poster_url": "poster.jpg",
                "streaming_link": "https://streaming.com/video",
            }
        ),

        # Missing fields
        (
            "<html><h1 class='title'>Alt Title</h1></html>",
            {
                "title": "Alt Title",
            }
        ),

        # Multiple matching tags — ensure first match wins
        (
            "<html><h1 class='entry-title'>First</h1><h1 class='title'>Second</h1></html>",
            {
                "title": "First",
            }
        ),

        # Empty tags
        (
            "<html><h1 class='entry-title'></h1><span class='ytps'></span></html>",
            {}
        ),

        # Malformed but valid HTML
        (
            "<html><h1 class='entry-title'>Malformed Movie",
            {
                "title": "Malformed Movie",
            }
        ),

        # Unicode (UTF-8)
        (
            "<html><h1 class='entry-title'>မြန်မာဇာတ်ကား</h1></html>",
            {
                "title": "မြန်မာဇာတ်ကား",
            }
        ),

        # Nested tags
        (
            "<html><div><h1 class='entry-title'><span>Nested Title</span></h1></div></html>",
            {
                "title": "Nested Title",
            }
        ),

        # Commented-out tags (should not be parsed)
        (
            "<html><!-- <h1 class='entry-title'>Hidden</h1> --></html>",
            {}
        ),

        # Very long title (stress test)
        (
            f"<html><h1 class='entry-title'>{'A' * 1000}</h1></html>",
            {
                "title": "A" * 1000,
            }
        ),
    ]
)
def test_extract_main_fields_variants(extractor, html, expected):
    """Test that extract correctly extracts main fields from various HTML structures."""
    response = fake_response("https://example.com", html)
    
    # Configure the text_cleaner mock to return the input text
    extractor.text_cleaner.clean.side_effect = lambda text: text
    
    fields = extractor.extract(response)

    for field, expected_value in expected.items():
        assert field in fields
        assert fields[field] == expected_value


def test_extract_main_fields_with_none_response(extractor):
    """Test that extract correctly handles None response."""
    with pytest.raises(ExtractionError):
        extractor.extract(None)


def test_extract_main_fields_with_css_error(extractor):
    """Test that extract correctly handles CSS selector errors."""
    # Create a mock response that raises an exception when css() is called
    response = MagicMock()
    response.css.side_effect = Exception("CSS selector error")
    
    # Should handle errors for individual fields but not fail completely
    fields = extractor.extract(response)
    assert isinstance(fields, dict)
    assert len(fields) == 0


def test_extract_field_value_with_combined_selector(extractor):
    """Test that extract_field_value correctly handles combined selectors."""
    html = """
        <html>
            <h1 class="entry-title">Test Movie</h1>
            <h1 class="title">Alt Title</h1>
        </html>
    """
    response = fake_response("https://example.com", html)
    
    # Test with combined selector
    selectors = ["h1.entry-title::text", "h1.title::text"]
    value = extractor.extract_field_value(response, selectors)
    
    assert value == "Test Movie"


def test_extract_field_value_with_individual_selectors(extractor):
    """Test that extract_field_value correctly falls back to individual selectors."""
    html = """
        <html>
            <h1 class="title">Alt Title</h1>
        </html>
    """
    response = fake_response("https://example.com", html)
    
    # Test with combined selector that fails, then individual selectors
    with patch.object(response, 'css') as mock_css:
        # First call (combined selector) raises exception
        # Second call (individual selector) returns a match
        mock_match = MagicMock()
        mock_match.get.return_value = "Alt Title"
        
        mock_css.side_effect = [
            Exception("Combined selector error"),
            mock_match
        ]
        
        selectors = ["h1.entry-title::text", "h1.title::text"]
        value = extractor.extract_field_value(response, selectors)
        
        assert value == "Alt Title"


def test_extract_field_value_with_xpath_fallback(extractor):
    """Test that extract_field_value correctly falls back to xpath."""
    html = """
        <html>
            <h1 class="title"><span>Nested Title</span></h1>
        </html>
    """
    response = fake_response("https://example.com", html)
    
    # Mock the CSS selector to return a match with no direct text
    mock_match = MagicMock()
    mock_match.get.return_value = None
    
    # Mock the xpath to return the nested text
    mock_xpath_result = MagicMock()
    mock_xpath_result.get.return_value = "Nested Title"
    mock_match.xpath.return_value = mock_xpath_result
    
    with patch.object(response, 'css', return_value=mock_match):
        selectors = ["h1.title::text"]
        value = extractor.extract_field_value(response, selectors)
        
        assert value == "Nested Title"


def test_extract_field_value_with_no_selectors(extractor):
    """Test that extract_field_value correctly handles empty selectors."""
    response = fake_response("https://example.com", "<html></html>")
    
    value = extractor.extract_field_value(response, [])
    
    assert value is None