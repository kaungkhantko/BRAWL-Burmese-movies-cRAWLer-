"""
Tests for the LinkExtractor class.
"""
import pytest
from unittest.mock import MagicMock, patch
from scrapy.http import HtmlResponse, Request

from burmese_movies_crawler.extractors.link_extractor import LinkExtractor
from burmese_movies_crawler.utils.exceptions import ExtractionError


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


def test_extract_links():
    """Test that extract correctly extracts and normalizes links."""
    html = """
        <html>
            <body>
                <div class="item"><a href="https://example.com/1">Link 1</a></div>
                <li><a href="mailto:someone@example.com">Invalid</a></li>
                <article><a href="/relative/link">Relative</a></article>
                <div class="card"><a href="">Empty</a></div>
                <div class="movie"><a href="javascript:void(0)">JS Link</a></div>
                <div class="movie"><a href="tel:+1234567890">Tel Link</a></div>
                <div class="movie"><a href=" https://example.com/1 ">Duplicate with spaces</a></div>
                <div class="movie"><a href="None">None-ish</a></div>
                <a href="//example.com/page">Protocol-relative</a>
                <a href="htp:/bad.url">Malformed</a>
                <a href="#">Fragment link</a>
                <a href="javascript:void(0);">JS Action</a>
                <a href="  ">Whitespace Only</a>
                <a href="/some/page#section">With Fragment</a>
                <a href="https://example.com/page">Link</a>
                <a href="https://example.com/page#comments">Same page with fragment</a>
            </body>
        </html>
    """

    invalid_links = []
    extractor = LinkExtractor(invalid_links=invalid_links)
    response = fake_response("https://example.com", html)

    links = extractor.extract(response)

    # Expected: Anchored and duplicate variants are normalized or stripped
    expected_links = {
        "https://example.com/1",
        "https://example.com/relative/link",
        "https://example.com/some/page",      # now absolute
        "https://example.com/page"            # duplicate fragment handled
    }
    assert set(links) == expected_links


def test_extract_links_with_invalid_links():
    """Test that extract correctly handles invalid links."""
    html = """
        <html>
            <body>
                <a href="mailto:someone@example.com">Invalid</a>
                <a href="javascript:void(0)">JS Link</a>
                <a href="tel:+1234567890">Tel Link</a>
                <a href="">Empty</a>
                <a href="#">Fragment link</a>
                <a href="None">None-ish</a>
                <a href="htp:/bad.url">Malformed</a>
            </body>
        </html>
    """

    invalid_links = []
    extractor = LinkExtractor(invalid_links=invalid_links)
    response = fake_response("https://example.com", html)

    links = extractor.extract(response)

    # Should return empty list as all links are invalid
    assert links == []


def test_extract_links_with_none_response():
    """Test that extract correctly handles None response."""
    extractor = LinkExtractor()
    
    with pytest.raises(ExtractionError):
        extractor.extract(None)


def test_extract_links_with_css_error():
    """Test that extract correctly handles CSS selector errors."""
    # Create a mock response that raises an exception when css() is called
    response = MagicMock()
    response.css.side_effect = Exception("CSS selector error")
    
    extractor = LinkExtractor()
    
    with pytest.raises(ExtractionError):
        extractor.extract(response)


def test_extract_links_with_link_processing_error():
    """Test that extract correctly handles link processing errors."""
    html = """
        <html>
            <body>
                <a href="https://example.com/1">Link 1</a>
                <a href="https://example.com/2">Link 2</a>
            </body>
        </html>
    """
    
    extractor = LinkExtractor()
    response = fake_response("https://example.com", html)
    
    # Mock urljoin to raise an exception for the second link
    with patch('burmese_movies_crawler.extractors.link_extractor.urljoin') as mock_urljoin:
        mock_urljoin.side_effect = [
            "https://example.com/1",  # First call works
            Exception("URL join error")  # Second call raises exception
        ]
        
        # Should continue processing and return the first link
        links = extractor.extract(response)
        assert len(links) == 1
        assert links[0] == "https://example.com/1"