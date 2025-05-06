import pytest
from scrapy.http import HtmlResponse, Request
from burmese_movies_crawler.utils.field_extractor import FieldExtractor
from burmese_movies_crawler.items import BurmeseMoviesItem

@pytest.fixture
def extractor():
    return FieldExtractor()

def fake_response(url, body, status=200, meta=None):
    """
    Create a mock HtmlResponse object for testing Scrapy components.

    Parameters:
    - url (str): The URL of the page being faked.
    - body (str or bytes): The HTML content of the page.
    - status (int): HTTP status code (default is 200).
    - meta (dict): Optional metadata to include in the request.

    Returns:
    - HtmlResponse: A mock Scrapy response object.
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
    extractor = FieldExtractor(invalid_links=invalid_links)
    response = fake_response("https://example.com", html)

    links = extractor.extract_links(response)

    # Expected: Anchored and duplicate variants are normalized or stripped
    expected_links = {
        "https://example.com/1",
        "/relative/link",
        "/some/page",                  # assuming fragments are stripped
        "https://example.com/page"     # fragments and duplicates removed
    }
    assert set(links) == expected_links

    # Check presence of expected invalid reasons
    reasons = [reason for reason, url in invalid_links]
    urls = [url for reason, url in invalid_links]

    assert "mailto:someone@example.com" in urls
    assert "//example.com/page" in urls
    assert "javascript:void(0)" in urls
    assert "tel:+1234567890" in urls
    assert "" in urls  # Empty
    assert "#" in urls or "Placeholder or fragment" in reasons
    assert "None" in urls
    assert "htp:/bad.url" in urls
    assert "/some/page" in links
    assert "/some/page#section" not in urls  # Optional: sanity check
    assert "https://example.com/page" in links
    assert "https://example.com/page#comments" not in urls

    print("All link extraction edge cases passed.")

def test_extract_main_fields():
    html = """
        <html>
            <body>
                <h1 class="entry-title">  Test Movie  </h1>
                <span class="ytps"> 2023 </span>
                <div class="entry-content"><img src=" poster.jpg " /></div>
                <iframe src=" https://streaming.com/video "></iframe>
            </body>
        </html>
    """

    extractor = FieldExtractor()
    response = fake_response("https://example.com/detail", html)
    fields = extractor.extract_main_fields(response)

    # Assert correct values (stripped)
    assert fields['title'] == "Test Movie"
    assert fields['year'] == "2023"
    assert fields['poster_url'] == "poster.jpg"
    assert fields['streaming_link'] == "https://streaming.com/video"

def test_extract_main_fields_missing_elements():
    html = """
        <html><body>
            <h1 class="title">Alt Title</h1>
            <!-- year and others missing -->
        </body></html>
    """

    extractor = FieldExtractor()
    response = fake_response("https://example.com/partial", html)
    fields = extractor.extract_main_fields(response)

    # Validate fallback selector worked for title
    assert fields['title'] == "Alt Title"
    assert fields['year'] is None
    assert fields['poster_url'] is None
    assert fields['streaming_link'] is None

def test_extract_main_fields_multiple_matches():
    html = """
        <html><body>
            <h1 class="entry-title">Primary Title</h1>
            <h1 class="title">Secondary Title</h1>
        </body></html>
    """
    extractor = FieldExtractor()
    response = fake_response("https://example.com", html)
    fields = extractor.extract_main_fields(response)
    assert fields['title'] == "Primary Title"  # Checks first-match logic

def test_extract_main_fields_empty_tags():
    html = """
        <html><body>
            <h1 class="entry-title"></h1>
            <span class="ytps"></span>
        </body></html>
    """
    extractor = FieldExtractor()
    response = fake_response("https://example.com", html)
    fields = extractor.extract_main_fields(response)
    assert fields['title'] is None
    assert fields['year'] is None

def test_extract_main_fields_malformed_html():
    html = "<html><h1 class='entry-title'>Malformed Movie"
    extractor = FieldExtractor()
    response = fake_response("https://example.com", html)
    fields = extractor.extract_main_fields(response)
    assert fields['title'] == "Malformed Movie"

def test_extract_main_fields_utf8_characters():
    html = "<html><h1 class='entry-title'>မြန်မာဇာတ်ကား</h1></html>"
    extractor = FieldExtractor()
    response = fake_response("https://example.com", html)
    fields = extractor.extract_main_fields(response)
    assert fields['title'] == "မြန်မာဇာတ်ကား"

def test_extract_main_fields_nested_tags():
    html = """
        <html><body>
            <div class="entry-title"><h1><span>Nested Movie</span></h1></div>
        </body></html>
    """
    extractor = FieldExtractor()
    response = fake_response("https://example.com", html)
    fields = extractor.extract_main_fields(response)
    # Expect None because selector looks for h1.entry-title, not div.entry-title h1
    assert fields['title'] is None

def test_extract_main_fields_commented_out():
    html = """
        <html><body>
            <!-- <h1 class="entry-title">Commented Title</h1> -->
        </body></html>
    """
    extractor = FieldExtractor()
    response = fake_response("https://example.com", html)
    fields = extractor.extract_main_fields(response)
    assert fields['title'] is None

def test_extract_main_fields_js_injected_skipped():
    html = """
        <html><body>
            <script>
                document.write('<h1 class="entry-title">JS Title</h1>');
            </script>
        </body></html>
    """
    extractor = FieldExtractor()
    response = fake_response("https://example.com", html)
    fields = extractor.extract_main_fields(response)
    assert fields['title'] is None  # JS not executed in static HTML

def test_extract_main_fields_long_strings():
    long_title = "A" * 100_000
    html = f"""
        <html><body>
            <h1 class="entry-title">{long_title}</h1>
        </body></html>
    """
    extractor = FieldExtractor()
    response = fake_response("https://example.com", html)
    fields = extractor.extract_main_fields(response)
    assert fields['title'] == long_title


def test_extract_paragraphs(extractor, monkeypatch):
    html = b"""
        <html><body>
            <div class="entry-content">
                <p>Director: John Doe</p>
                <p>Genre: Drama</p>
            </div>
        </body></html>
    """
    monkeypatch.setattr(extractor, "_match_field", lambda text: ("director", 90) if "Director" in text else ("genre", 80))
    monkeypatch.setattr(extractor, "_clean_text", lambda text: text.split(":")[-1].strip())
    response = fake_response("https://example.com", html)
    data = extractor.extract_paragraphs(response)
    assert data["director"] == "John Doe"
    assert data["genre"] == "Drama"

def test_extract_from_table(extractor, monkeypatch):
    html = b"""
        <html>
        <body>
            <table>
                <thead><tr><th>Title</th><th>Year</th></tr></thead>
                <tbody>
                    <tr><td>Test Film</td><td>2021</td></tr>
                </tbody>
            </table>
        </body>
        </html>
    """
    monkeypatch.setattr(extractor, "_map_headers", lambda headers: {"Title": "title", "Year": "year"})
    response = fake_response("https://example.com", html)
    table = response.css("table")[0]
    items = list(extractor.extract_from_table(response, table))
    assert len(items) == 1
    assert isinstance(items[0], BurmeseMoviesItem)
    assert items[0]["title"] == "Test Film"
    assert items[0]["year"] == "2021"
