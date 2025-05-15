"""
Integration tests for the extraction system.
"""
import pytest
from unittest.mock import MagicMock
from scrapy.http import HtmlResponse, Request

from burmese_movies_crawler.factory import create_extractor_engine


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


def test_extract_all_integration():
    """Test that the entire extraction pipeline works together."""
    # Create a sample HTML with various elements to extract
    html = """
    <html>
        <head>
            <title>Test Movie Page</title>
        </head>
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
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Year</th>
                            <th>Director</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Related Movie 1</td>
                            <td>2022</td>
                            <td>Jane Smith</td>
                        </tr>
                        <tr>
                            <td>Related Movie 2</td>
                            <td>2021</td>
                            <td>Bob Johnson</td>
                        </tr>
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
    
    # Create a response object
    response = fake_response("https://example.com/test-movie", html)
    
    # Create the extractor engine
    engine = create_extractor_engine()
    
    # Extract all data
    result = engine.extract_all(response)
    
    # Verify that all expected data was extracted
    
    # Links
    assert "links" in result
    assert len(result["links"]) >= 3
    assert "https://example.com/movie1" in result["links"]
    assert "https://example.com/movie2" in result["links"]
    assert "https://example.com/relative/link" in result["links"]
    
    # Main fields
    assert "main_fields" in result
    assert result["main_fields"]["title"] == "The Test Movie"
    assert result["main_fields"]["year"] == "2023"
    assert result["main_fields"]["poster_url"] == "poster.jpg"
    assert result["main_fields"]["streaming_link"] == "https://streaming.com/video"
    
    # Paragraph fields
    assert "paragraph_fields" in result
    assert "director" in result["paragraph_fields"]
    assert "genre" in result["paragraph_fields"]
    assert "cast" in result["paragraph_fields"]
    
    # Combined fields
    assert "fields" in result
    assert result["fields"]["title"] == "The Test Movie"
    assert result["fields"]["year"] == "2023"
    assert result["fields"]["director"] in result["paragraph_fields"]["director"]
    
    # Table items
    assert "items" in result
    assert len(result["items"]) == 2
    assert result["items"][0]["title"] == "Related Movie 1"
    assert result["items"][0]["year"] == "2022"
    assert result["items"][0]["director"] == "Jane Smith"
    assert result["items"][1]["title"] == "Related Movie 2"
    assert result["items"][1]["year"] == "2021"
    assert result["items"][1]["director"] == "Bob Johnson"