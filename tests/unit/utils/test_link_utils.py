import pytest
from burmese_movies_crawler.utils.link_utils import (
    is_valid_link,
    extract_page_stats,
    rule_detail_like,
    rule_link_heavy,
    rule_text_heavy,
    rule_fallback_links,
    rule_table_catalogue,
    evaluate_catalogue_rules,
    compute_catalogue_score)
from scrapy.http import HtmlResponse

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


# TODO: Needs edge cases and logic for the following functions
def test_extract_page_stats():
    html = """
    <html>
        <body>
            <a href="#">Link</a>
            <img src="img.png" />
            <iframe src="frame.html"></iframe>
            <p>Paragraph</p>
            <table><tbody><tr><td>Row</td></tr></tbody></table>
        </body>
    </html>
    """
    response = HtmlResponse(url="http://example.com", body=html, encoding='utf-8')
    stats = extract_page_stats(response)
    assert stats == {'links': 1, 'images': 1, 'iframes': 1, 'paragraphs': 1, 'tables': 1}

def test_rule_detail_like():
    assert rule_detail_like({'iframes': 1, 'links': 10}) is False
    assert rule_detail_like({'iframes': 0, 'links': 100}) is True

def test_rule_link_heavy():
    thresholds = {'link_heavy_min_links': 20, 'link_heavy_max_iframes': 2}
    assert rule_link_heavy({'links': 30, 'iframes': 1}, thresholds) is True
    assert rule_link_heavy({'links': 15, 'iframes': 1}, thresholds) is False

def test_rule_text_heavy():
    return
def test_rule_fallback_links():
    return

def test_rule_table_catalogue():
    html = "<table><tbody><tr><td>1</td></tr><tr><td>2</td></tr></tbody></table>"
    response = HtmlResponse(url="http://example.com", body=html, encoding='utf-8')
    stats = {'tables': 1}
    thresholds = {'table_min_rows': 2}
    assert rule_table_catalogue(response, stats, thresholds) is True

def test_evaluate_catalogue_rules_success():
    stats = {'links': 40, 'iframes': 0, 'paragraphs': 10, 'images': 2, 'tables': 1}
    thresholds = {
        'link_heavy_min_links': 30,
        'link_heavy_max_iframes': 1,
        'text_heavy_min_paragraphs': 5,
        'text_heavy_max_images': 5,
        'table_min_rows': 1,
        'fallback_min_links': 10,
        'fallback_max_images': 5
    }
    rules = [
        ("link_heavy", rule_link_heavy, 1),
        ("text_heavy", rule_text_heavy, 2),
        ("table_catalogue", rule_table_catalogue, 3)
    ]
    response = HtmlResponse(url="http://example.com", body="<table><tbody><tr><td></td></tr></tbody></table>", encoding="utf-8")
    results = evaluate_catalogue_rules(response, stats, rules, thresholds)
    assert all(isinstance(r, dict) for r in results)
    assert len(results) == 3

def test_compute_catalogue_score_sum():
    results = [{'name': 'a', 'passed': True, 'weight': 2}, {'name': 'b', 'passed': False, 'weight': 3}]
    assert compute_catalogue_score(results, method="sum") == 2

def test_compute_catalogue_score_weighted_average():
    results = [{'name': 'a', 'passed': True, 'weight': 2}, {'name': 'b', 'passed': False, 'weight': 2}]
    assert compute_catalogue_score(results, method="weighted_average") == 50.0

def test_compute_catalogue_score_strict_majority():
    results = [{'name': 'a', 'passed': True, 'weight': 1}, {'name': 'b', 'passed': True, 'weight': 1}, {'name': 'c', 'passed': False, 'weight': 1}]
    assert compute_catalogue_score(results, method="strict_majority") is True
