import pytest
from burmese_movies_crawler.utils.link_utils import is_valid_link

@pytest.mark.parametrize("url", [
    "https://example.com",
    "/relative/path",
    "./about",
    "../movies",
    "https://example.com#section",
    "https://example.com/search?q=test",
    "   https://example.com/page   "
])
def test_valid_links(url):
    assert is_valid_link(url) is True

@pytest.mark.parametrize("url, reason", [
    ("", "Empty URL"),
    ("#", "Placeholder or fragment"),
    ("void(0)", "Placeholder or fragment"),
    ("none", "Placeholder or fragment"),
    ("javascript:void(0)", "Non-crawlable scheme"),
    ("mailto:someone@example.com", "Non-crawlable scheme"),
    ("tel:123456789", "Non-crawlable scheme"),
    ("ftp://example.com", "Unsupported URL format"),
    ("data:text/html;base64,xyz", "Unsupported URL format"),
    ("http:/", "Unsupported URL format"),
    (":", "Unsupported URL format"),
    ("JavaScript:void(0)", "Non-crawlable scheme"),
    ("MAILTO:user@example.com", "Non-crawlable scheme"),
    ("//example.com", "Protocol-relative URL")
])
def test_invalid_links(url, reason):
    log = []
    assert is_valid_link(url, log) is False
    assert log[0] == (reason, url)

@pytest.mark.parametrize("non_string", [None, 123, [], {}])
def test_non_string_inputs(non_string):
    log = []
    assert is_valid_link(non_string, log) is False
    assert log[0] == ("Non-string input", non_string)
