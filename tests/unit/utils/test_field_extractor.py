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
                "year": None,
                "poster_url": None,
                "streaming_link": None
            }
        ),

        # Multiple matching tags — ensure first match wins
        (
            "<html><h1 class='entry-title'>First</h1><h1 class='title'>Second</h1></html>",
            {
                "title": "First",
                "year": None,
                "poster_url": None,
                "streaming_link": None
            }
        ),

        # Empty tags
        (
            "<html><h1 class='entry-title'></h1><span class='ytps'></span></html>",
            {
                "title": None,
                "year": None,
                "poster_url": None,
                "streaming_link": None
            }
        ),

        # Malformed but valid HTML
        (
            "<html><h1 class='entry-title'>Malformed Movie",
            {
                "title": "Malformed Movie",
                "year": None,
                "poster_url": None,
                "streaming_link": None
            }
        ),

        # Unicode (UTF-8)
        (
            "<html><h1 class='entry-title'>မြန်မာဇာတ်ကား</h1></html>",
            {
                "title": "မြန်မာဇာတ်ကား",
                "year": None,
                "poster_url": None,
                "streaming_link": None
            }
        ),

        # Nested tags
        (
            "<html><div><h1 class='entry-title'><span>Nested Title</span></h1></div></html>",
            {
                "title": "Nested Title",
                "year": None,
                "poster_url": None,
                "streaming_link": None
            }
        ),

        # Commented-out tags (should not be parsed)
        (
            "<html><!-- <h1 class='entry-title'>Hidden</h1> --></html>",
            {
                "title": None,
                "year": None,
                "poster_url": None,
                "streaming_link": None
            }
        ),

        # Very long title (stress test)
        (
            f"<html><h1 class='entry-title'>{'A' * 10000}</h1></html>",
            {
                "title": "A" * 10000,
                "year": None,
                "poster_url": None,
                "streaming_link": None
            }
        ),
    ]
)
def test_extract_main_fields_variants(html, expected):
    extractor = FieldExtractor()
    response = fake_response("https://example.com", html)
    fields = extractor.extract_main_fields(response)

    for field, expected_value in expected.items():
        assert fields[field] == expected_value

@pytest.mark.parametrize(
    "html, expected",
    [
        # Normal case
        (
            "<html><body><div class='entry-content'><p>Director: John Doe</p><p>Genre: Drama</p></div></body></html>",
            {"director": "John Doe", "genre": "Drama"},
        ),

        # Extra whitespace
        (
            "<html><body><div class='entry-content'><p>  Director  :   Jane Smith  </p></div></body></html>",
            {"director": "Jane Smith"},
        ),

        # Irrelevant text
        (
            "<html><body><div class='entry-content'><p>This is just a note.</p><p>Genre: Comedy</p></div></body></html>",
            {"genre": "Comedy"},
        ),

        # Repeated fields
        (
            "<html><body><div class='entry-content'><p>Director: First One</p><p>Director: Second One</p><p>Genre: Thriller</p></div></body></html>",
            {"director": "First One", "genre": "Thriller"},
        ),

        # Weak match score
        (
            "<html><body><div class='entry-content'><p>Directed by: Someone</p></div></body></html>",
            {},
        ),

        # Empty tag
        (
            "<html><body><div class='entry-content'><p></p><p>Genre: Mystery</p></div></body></html>",
            {"genre": "Mystery"},
        ),

        # Non-breaking space / malformed text
        (
            "<html><body><div class='entry-content'><p>Director&nbsp;: Robert</p></div></body></html>",
            {"director": "Robert"},
        ),

        # Burmese label and value
        (
            "<html><body><div class='entry-content'><p>ဒါရိုက်တာ - မောင်မောင်</p></div></body></html>",
            {"director": "မောင်မောင်"},
        ),

        # Unicode French label
        (
            "<html><body><div class='entry-content'><p>Réalisateur : Jean-Luc</p></div></body></html>",
            {"director": "Jean-Luc"},
        ),
    ]
)
def test_extract_paragraphs_variants(html, expected, monkeypatch):
    extractor = FieldExtractor()

    def mock_match(text):
        if "Director" in text or "Réalisateur" in text or "ဒါရိုက်တာ" in text:
            return "director", 90
        if "Genre" in text:
            return "genre", 85
        if "Directed by" in text:
            return "director", 60  # below threshold
        return None, 0

    monkeypatch.setattr(extractor, "_match_field", mock_match)
    monkeypatch.setattr(extractor, "_clean_text", lambda text: text.split(":", 1)[-1].strip())


    response = fake_response("https://example.com", html)
    result = extractor.extract_paragraphs(response)

    assert result == expected


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
            [{"title": None, "year": "2020"}]
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
def test_extract_from_table_variants(extractor, html, mapped_headers, expected, monkeypatch):
    monkeypatch.setattr(extractor, "_map_headers", lambda headers: mapped_headers)
    response = fake_response("https://example.com", html)
    table = response.css("table")[0]
    items = list(extractor.extract_from_table(response, table))

    assert len(items) == len(expected)
    for item, expected_values in zip(items, expected):
        assert isinstance(item, BurmeseMoviesItem)
        for field, value in expected_values.items():
            assert item.get(field) == value