"""
Tests for the ParagraphExtractor class.
"""
import pytest
from unittest.mock import MagicMock, patch
from scrapy.http import HtmlResponse, Request

from burmese_movies_crawler.extractors.paragraph_extractor import ParagraphExtractor
from burmese_movies_crawler.utils.exceptions import ExtractionError, ProcessingError


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
def field_matcher():
    """Fixture for FieldMatcher with mocked match method."""
    matcher = MagicMock()
    return matcher


@pytest.fixture
def text_cleaner():
    """Fixture for TextCleaner with mocked clean method."""
    cleaner = MagicMock()
    return cleaner


@pytest.fixture
def extractor(field_matcher, text_cleaner):
    """Fixture for ParagraphExtractor with mocked dependencies."""
    return ParagraphExtractor(field_matcher, text_cleaner)


@pytest.mark.parametrize(
    "html, mock_matches, expected",
    [
        # Normal case
        (
            "<html><body><div class='entry-content'><p>Director: John Doe</p><p>Genre: Drama</p></div></body></html>",
            [("director", 90), ("genre", 85)],
            {"director": "John Doe", "genre": "Drama"},
        ),

        # Extra whitespace
        (
            "<html><body><div class='entry-content'><p>  Director  :   Jane Smith  </p></div></body></html>",
            [("director", 90)],
            {"director": "Jane Smith"},
        ),

        # Irrelevant text
        (
            "<html><body><div class='entry-content'><p>This is just a note.</p><p>Genre: Comedy</p></div></body></html>",
            [(None, 0), ("genre", 85)],
            {"genre": "Comedy"},
        ),

        # Repeated fields
        (
            "<html><body><div class='entry-content'><p>Director: First One</p><p>Director: Second One</p><p>Genre: Thriller</p></div></body></html>",
            [("director", 90), ("director", 90), ("genre", 85)],
            {"director": "First One", "genre": "Thriller"},
        ),

        # Weak match score
        (
            "<html><body><div class='entry-content'><p>Directed by: Someone</p></div></body></html>",
            [("director", 60)],  # Below threshold
            {},
        ),

        # Empty tag
        (
            "<html><body><div class='entry-content'><p></p><p>Genre: Mystery</p></div></body></html>",
            [(None, 0), ("genre", 85)],
            {"genre": "Mystery"},
        ),

        # Non-breaking space / malformed text
        (
            "<html><body><div class='entry-content'><p>Director&nbsp;: Robert</p></div></body></html>",
            [("director", 90)],
            {"director": "Robert"},
        ),

        # Burmese label and value
        (
            "<html><body><div class='entry-content'><p>ဒါရိုက်တာ - မောင်မောင်</p></div></body></html>",
            [("director", 90)],
            {"director": "မောင်မောင်"},
        ),

        # Unicode French label
        (
            "<html><body><div class='entry-content'><p>Réalisateur : Jean-Luc</p></div></body></html>",
            [("director", 90)],
            {"director": "Jean-Luc"},
        ),
    ]
)
def test_extract_paragraphs_variants(extractor, html, mock_matches, expected):
    """Test that extract correctly extracts fields from paragraphs."""
    response = fake_response("https://example.com", html)
    
    # Configure the field_matcher mock to return the specified matches
    extractor.field_matcher.match.side_effect = mock_matches
    
    # Configure the text_cleaner mock to return the text after the colon or dash
    def mock_clean(text):
        if ":" in text:
            return text.split(":", 1)[1].strip()
        elif "-" in text:
            return text.split("-", 1)[1].strip()
        elif "–" in text:
            return text.split("–", 1)[1].strip()
        return text.strip()
    
    extractor.text_cleaner.clean.side_effect = mock_clean
    
    result = extractor.extract(response)
    
    assert result == expected


def test_extract_paragraphs_with_none_response(extractor):
    """Test that extract correctly handles None response."""
    with pytest.raises(ExtractionError):
        extractor.extract(None)


def test_extract_paragraphs_with_css_error(extractor):
    """Test that extract correctly handles CSS selector errors."""
    # Create a mock response that raises an exception when css() is called
    response = MagicMock()
    response.css.side_effect = Exception("CSS selector error")
    
    with pytest.raises(ExtractionError):
        extractor.extract(response)


def test_extract_paragraphs_with_field_matching_error(extractor):
    """Test that extract correctly handles field matching errors."""
    html = "<html><body><div class='entry-content'><p>Director: John Doe</p></div></body></html>"
    response = fake_response("https://example.com", html)
    
    # Configure the field_matcher mock to raise an exception
    extractor.field_matcher.match.side_effect = Exception("Field matching error")
    
    # Should handle errors for individual paragraphs
    result = extractor.extract(response)
    assert isinstance(result, dict)
    assert len(result) == 0


def test_extract_paragraphs_with_paragraph_processing_error(extractor):
    """Test that extract correctly handles paragraph processing errors."""
    # Create a mock response with a mix of valid and invalid paragraphs
    class PartialBadResponse:
        def css(self, selector):
            class BadResult:
                def getall(self):
                    return ["Normal text", None, object()]  # None and object() will cause errors
            return BadResult()
    
    # Should handle errors for individual paragraphs
    result = extractor.extract(PartialBadResponse())
    assert isinstance(result, dict)
    assert len(result) == 0


def test_extract_paragraphs_with_length_filtering(extractor):
    """Test that extract correctly filters paragraphs by length."""
    html = """
        <html><body><div class='entry-content'>
            <p>Too short</p>
            <p>This is a paragraph with good length that should be processed</p>
            <p>This is an extremely long paragraph that exceeds the maximum length limit and should be filtered out because it's too verbose and contains too much information to be a simple field label and value pair. It goes on and on with unnecessary details that don't contribute to the extraction process.</p>
        </div></body></html>
    """
    response = fake_response("https://example.com", html)
    
    # Configure the field_matcher mock to return a match for the middle paragraph
    extractor.field_matcher.match.return_value = ("description", 90)
    
    # Configure the text_cleaner mock to return the input text
    extractor.text_cleaner.clean.side_effect = lambda text: text
    
    result = extractor.extract(response)
    
    # Only the middle paragraph should be processed and matched
    assert len(result) == 1
    assert "description" in result