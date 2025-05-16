"""
Integration tests for the extraction system.
"""
import pytest
from unittest.mock import patch
from scrapy.http import HtmlResponse, Request

from burmese_movies_crawler.factory import create_extractor_engine
from burmese_movies_crawler.utils.exceptions import FieldExtractorError, ExtractionError


@pytest.fixture
def fake_response():
    """Create a mock HtmlResponse object for testing."""
    def _create(url, body, status=200, meta=None):
        if isinstance(body, str):
            body = body.encode('utf-8')
        return HtmlResponse(
            url=url,
            body=body,
            encoding='utf-8',
            status=status,
            request=Request(url=url, meta=meta or {})
        )
    return _create


@pytest.fixture
def extractor_engine():
    """Create an extractor engine for testing."""
    return create_extractor_engine()


# Test HTML content fixtures
@pytest.fixture
def standard_html():
    """HTML with all expected elements."""
    return """
    <html>
        <head><title>Test Movie Page</title></head>
        <body>
            <h1 class="entry-title">The Test Movie</h1>
            <span class="ytps">2023</span>
            <div class="entry-content">
                <img src="poster.jpg" />
                <p>Director: John Doe</p>
                <p>Genre: Action, Drama</p>
                <p>Cast: Actor One, Actor Two</p>
                <iframe src="https://streaming.com/video"></iframe>
                <table>
                    <thead><tr><th>Title</th><th>Year</th><th>Director</th></tr></thead>
                    <tbody>
                        <tr><td>Related Movie 1</td><td>2022</td><td>Jane Smith</td></tr>
                        <tr><td>Related Movie 2</td><td>2021</td><td>Bob Johnson</td></tr>
                    </tbody>
                </table>
                <div class="links">
                    <a href="https://example.com/movie1">Movie 1</a>
                    <a href="https://example.com/movie2">Movie 2</a>
                    <a href="/relative/link">Relative Link</a>
                </div>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def edge_case_htmls():
    """Collection of HTML content for edge case testing."""
    return {
        "empty": "",
        "malformed": """
            <html><body><h1 class="entry-title">Malformed HTML Test
            <div class="entry-content"><p>Unclosed tags
            <img src="broken.jpg" alt="Missing quote></div></body></html>
        """,
        "missing_elements": """
            <html><body><div class="entry-content">
            <p>Some content without structured data</p>
            <table><tr><td>Just a cell</td></tr></table>
            </div></body></html>
        """,
        "invalid_urls": """
            <html><body><div class="links">
            <a href="javascript:void(0)">JavaScript</a>
            <a href="mailto:test@example.com">Email</a>
            <a href="https://example.com/valid">Valid</a>
            </div></body></html>
        """,
        "table_formats": """
            <html><body><div class="entry-content">
            <table id="table1">
                <thead><tr><th>Title</th><th>Year</th></tr></thead>
                <tbody><tr><td>Movie A</td><td>2020</td></tr></tbody>
            </table>
            <table id="table2">
                <tr><th>Title</th><th>Year</th></tr>
                <tr><td>Movie B</td><td>2021</td></tr>
            </table>
            <table id="table3">
                <tr><th>Title</th><th>Year</th><th>Director</th></tr>
                <tr><td>Movie C</td><td>2022</td></tr>
            </table>
            </div></body></html>
        """,
        "relative_urls": """
            <html><body><div class="entry-content">
            <img src="/images/poster.jpg" />
            <div class="links">
                <a href="/relative/path">Relative</a>
                <a href="./another-relative">Another</a>
                <a href="https://example.com/absolute">Absolute</a>
            </div>
            </div></body></html>
        """,
        "unicode": """
            <html><body>
            <h1 class="entry-title">မြန်မာ ရုပ်ရှင်</h1>
            <span class="ytps">၂၀၂၃</span>
            <div class="entry-content">
                <p>ဒါရိုက်တာ: ဦးကျော်</p>
                <table><tr><th>ခေါင်းစဉ်</th><th>နှစ်</th></tr>
                <tr><td>ရုပ်ရှင် ၁</td><td>၂၀၂၂</td></tr></table>
            </div>
            </body></html>
        """
    }


def test_standard_extraction(fake_response, extractor_engine, standard_html):
    """Test extraction with standard HTML containing all expected elements."""
    response = fake_response("https://example.com/test-movie", standard_html)
    result = extractor_engine.extract_all(response)
    
    # Verify links
    assert len(result["links"]) >= 3
    assert "https://example.com/movie1" in result["links"]
    assert "https://example.com/movie2" in result["links"]
    assert "https://example.com/relative/link" in result["links"]
    
    # Verify main fields
    assert result["main_fields"]["title"] == "The Test Movie"
    assert result["main_fields"]["year"] == "2023"
    assert result["main_fields"]["poster_url"] == "poster.jpg"
    assert result["main_fields"]["streaming_link"] == "//streaming.com/video"
    
    # Verify paragraph fields
    assert "director" in result["paragraph_fields"]
    assert "genre" in result["paragraph_fields"]
    assert "cast" in result["paragraph_fields"]
    
    # Verify combined fields
    assert result["fields"]["title"] == "The Test Movie"
    assert result["fields"]["year"] == "2023"
    
    # Verify table items
    assert len(result["items"]) == 2
    assert result["items"][0]["title"] == "Related Movie 1"
    assert result["items"][0]["year"] == "2022"
    assert result["items"][1]["title"] == "Related Movie 2"
    assert result["items"][1]["year"] == "2021"


@pytest.mark.parametrize("case", [
    "empty", "malformed", "missing_elements", "invalid_urls", 
    "table_formats", "relative_urls", "unicode"
])
def test_edge_cases(fake_response, extractor_engine, edge_case_htmls, case):
    """Test extraction with various edge cases."""
    html = edge_case_htmls[case]
    url = f"https://example.com/{case}"
    
    # Use a different base URL for relative URL testing
    if case == "relative_urls":
        url = "https://example.com/movies/action/"
        
    response = fake_response(url, html)
    result = extractor_engine.extract_all(response)
    
    # All results should have the basic structure
    assert "links" in result
    assert "main_fields" in result
    assert "paragraph_fields" in result
    assert "fields" in result
    assert "items" in result
    
    # Case-specific assertions
    if case == "empty":
        assert len(result["links"]) == 0
        assert len(result["main_fields"]) == 0
        assert len(result["fields"]) == 0
        
    elif case == "invalid_urls":
        assert "https://example.com/valid" in result["links"]
        assert not any(link.startswith("javascript:") for link in result["links"])
        assert not any(link.startswith("mailto:") for link in result["links"])
        
    elif case == "table_formats":
        titles = [item["title"] for item in result["items"] if "title" in item]
        assert len(titles) >= 3
        assert "Movie A" in titles
        assert "Movie B" in titles
        assert "Movie C" in titles
        
    elif case == "relative_urls":
        assert "https://example.com/relative/path" in result["links"]
        assert "https://example.com/movies/action/another-relative" in result["links"]
        assert "https://example.com/absolute" in result["links"]
        
    elif case == "unicode":
        if "title" in result["main_fields"]:
            assert result["main_fields"]["title"] == "မြန်မာ ရုပ်ရှင်"
        if result["items"] and "title" in result["items"][0]:
            assert result["items"][0]["title"] == "ရုပ်ရှင် ၁"


def test_error_handling(fake_response, extractor_engine):
    """Test error handling during extraction."""
    response = fake_response("https://example.com/error-test", "<html><body></body></html>")
    
    with patch('burmese_movies_crawler.extractors.link_extractor.LinkExtractor.extract') as mock_extract:
        mock_extract.side_effect = ExtractionError("Simulated extraction error")
        with pytest.raises(FieldExtractorError):
            extractor_engine.extract_all(response)


def test_http_error_response(fake_response, extractor_engine):
    """Test handling of HTTP error responses."""
    response = fake_response("https://example.com/not-found", "<html><body>Not Found</body></html>", status=404)
    result = extractor_engine.extract_all(response)
    
    # Should still have the basic structure
    assert "links" in result
    assert "main_fields" in result
    assert "paragraph_fields" in result
    assert "fields" in result
    assert "items" in result