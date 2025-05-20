import pytest
from burmese_movies_crawler.core.link_utils import (
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
from urllib.parse import urldefrag, urljoin


@pytest.mark.parametrize("raw_url, base_url", [
    # Absolute URLs (should pass)
    ("https://example.com/path", "https://example.com"),  # Need a path to pass validation
    ("https://example.com/search?q=test", "https://example.com"),

    # Fragment should be stripped but still valid
    ("https://example.com/path#section", "https://example.com"),  # Need a path to pass validation

    # Whitespace should be stripped and accepted
    ("   https://example.com/page   ", "https://example.com"),

    # Valid relative URLs (should pass after urljoin)
    ("/relative/path", "https://example.com"),
    ("./about", "https://example.com/movies"),
    ("../movies", "https://example.com/films/page")
])
def test_valid_links(raw_url, base_url):
    """
    Ensure valid absolute and relative URLs are accepted
    after normalization and defragmentation.
    """
    invalid_log = []

    # Simulate normalization as done in extract_links()
    resolved = urljoin(base_url, raw_url.strip())
    clean = urldefrag(resolved)[0]

    assert is_valid_link(clean, invalid_log) is True
    assert not invalid_log  # Nothing should be logged


@pytest.mark.parametrize("url, reason", [
    ("", "Empty or None"),
    ("#", "Fragment-only link or base URL"),
    ("void(0)", "Empty or None"),
    ("none", "Empty or None"),
    ("javascript:void(0)", "Non-crawlable scheme"),
    ("mailto:someone@example.com", "Non-crawlable scheme"),
    ("tel:123456789", "Non-crawlable scheme"),
    ("ftp://example.com", "Unsupported or malformed URL format"),  # Now correctly classified
    ("data:text/html;base64,xyz", "Unsupported or malformed URL format"),
    ("http:/", "Unsupported or malformed URL format"),  # Now correctly classified
    (":", "Unsupported or malformed URL format"),
    ("JavaScript:void(0)", "Non-crawlable scheme"),
    ("MAILTO:user@example.com", "Non-crawlable scheme"),
    ("//example.com", "Unsupported or malformed URL format")
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


# Helper function to create HtmlResponse objects for testing
def create_html_response(html_content, url="http://example.com"):
    """Create a HtmlResponse object with the given HTML content."""
    return HtmlResponse(url=url, body=html_content.encode('utf-8'), encoding='utf-8')


# HTML fixtures for reuse
@pytest.fixture
def basic_html():
    return """
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


@pytest.fixture
def table_html():
    return """
    <html>
        <body>
            <table>
                <tbody>
                    <tr><td>Row 1</td></tr>
                    <tr><td>Row 2</td></tr>
                </tbody>
            </table>
        </body>
    </html>
    """

def create_table_html(rows=2):
    """Helper function to create HTML with a table containing the specified number of rows."""
    rows_html = "".join([f"<tr><td>Row {i}</td></tr>" for i in range(1, rows+1)])
    return f"""
    <html>
        <body>
            <table>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </body>
    </html>
    """


@pytest.mark.describe("extract_page_stats tests")
class TestExtractPageStats:
    def test_extract_page_stats_basic(self, basic_html):
        """Test basic element counting with one of each element type."""
        response = create_html_response(basic_html)
        stats = extract_page_stats(response)
        assert stats == {'links': 1, 'images': 1, 'iframes': 1, 'paragraphs': 1, 'tables': 1}
    
    def test_extract_page_stats_multiple(self):
        """Test counting multiple instances of each element type."""
        html = """
        <html>
            <body>
                <a href="#">Link 1</a>
                <a href="#">Link 2</a>
                <a href="#">Link 3</a>
                <img src="img1.png" />
                <img src="img2.png" />
                <iframe src="frame1.html"></iframe>
                <iframe src="frame2.html"></iframe>
                <p>Paragraph 1</p>
                <p>Paragraph 2</p>
                <table><tbody><tr><td>Table 1</td></tr></tbody></table>
                <table><tbody><tr><td>Table 2</td></tr></tbody></table>
            </body>
        </html>
        """
        response = create_html_response(html)
        stats = extract_page_stats(response)
        assert stats == {'links': 3, 'images': 2, 'iframes': 2, 'paragraphs': 2, 'tables': 2}
    
    def test_extract_page_stats_empty(self):
        """Test with empty HTML document."""
        html = "<html><body></body></html>"
        response = create_html_response(html)
        stats = extract_page_stats(response)
        assert stats == {'links': 0, 'images': 0, 'iframes': 0, 'paragraphs': 0, 'tables': 0}
    
    def test_extract_page_stats_malformed(self):
        """Test with malformed HTML."""
        html = """
        <html>
            <body>
                <a href="#">Unclosed link
                <img src="img.png">
                <p>Paragraph</p
                <table><tr>No tbody</table>
            </body>
        """
        response = create_html_response(html)
        stats = extract_page_stats(response)
        # Even with malformed HTML, scrapy's xpath should still count elements
        assert stats['links'] == 1
        assert stats['images'] == 1
        assert stats['paragraphs'] == 1
        # Scrapy's parser doesn't recognize the malformed table
        assert stats['tables'] == 0
        assert stats['iframes'] == 0


@pytest.mark.describe("rule_detail_like tests")
class TestRuleDetailLike:
    @pytest.mark.parametrize("stats, expected", [
        # No iframes, many links
        ({'iframes': 0, 'links': 50}, True),
        # Has iframes but also many links
        ({'iframes': 2, 'links': 30}, True),
        # Has iframes and few links
        ({'iframes': 1, 'links': 10}, False),
        ({'iframes': 3, 'links': 29}, False),
        # Edge cases
        ({'iframes': 1, 'links': 30}, True),  # Exactly at threshold
        ({'iframes': 0, 'links': 5}, True),   # No iframes, few links
    ])
    def test_rule_detail_like(self, stats, expected):
        """Test rule_detail_like with various inputs."""
        assert rule_detail_like(stats) is expected


@pytest.mark.describe("rule_link_heavy tests")
class TestRuleLinkHeavy:
    @pytest.mark.parametrize("stats, expected", [
        # Many links, few iframes
        ({'links': 30, 'iframes': 1}, True),
        # Many links, at max iframes threshold
        ({'links': 50, 'iframes': 2}, True),
        # Too few links
        ({'links': 15, 'iframes': 1}, False),
        # Too many iframes
        ({'links': 30, 'iframes': 3}, False),
        # Both conditions fail
        ({'links': 10, 'iframes': 5}, False),
        # Edge cases
        ({'links': 20, 'iframes': 1}, False),  # Exactly at min links threshold
        ({'links': 21, 'iframes': 1}, True),   # Just above min links threshold
    ])
    def test_rule_link_heavy(self, stats, expected):
        """Test rule_link_heavy with various inputs."""
        thresholds = {'link_heavy_min_links': 20, 'link_heavy_max_iframes': 2}
        assert rule_link_heavy(stats, thresholds) is expected


@pytest.mark.describe("rule_text_heavy tests")
class TestRuleTextHeavy:
    @pytest.mark.parametrize("stats, expected", [
        # Many paragraphs, few images
        ({'paragraphs': 10, 'images': 2}, True),
        # Many paragraphs, at max images threshold
        ({'paragraphs': 15, 'images': 3}, True),
        # Too few paragraphs
        ({'paragraphs': 3, 'images': 2}, False),
        # Too many images
        ({'paragraphs': 10, 'images': 4}, False),
        # Both conditions fail
        ({'paragraphs': 3, 'images': 5}, False),
        # Edge cases
        ({'paragraphs': 5, 'images': 2}, False),  # Exactly at min paragraphs threshold
        ({'paragraphs': 6, 'images': 2}, True),   # Just above min paragraphs threshold
    ])
    def test_rule_text_heavy(self, stats, expected):
        """Test rule_text_heavy with various inputs."""
        thresholds = {'text_heavy_min_paragraphs': 5, 'text_heavy_max_images': 3}
        assert rule_text_heavy(stats, thresholds) is expected


@pytest.mark.describe("rule_fallback_links tests")
class TestRuleFallbackLinks:
    @pytest.mark.parametrize("stats, expected", [
        # Many links, few images
        ({'links': 15, 'images': 3}, True),
        # Many links, at max images threshold
        ({'links': 20, 'images': 5}, True),
        # Too few links
        ({'links': 8, 'images': 3}, False),
        # Too many images
        ({'links': 15, 'images': 6}, False),
        # Both conditions fail
        ({'links': 5, 'images': 10}, False),
        # Edge cases
        ({'links': 10, 'images': 3}, False),  # Exactly at min links threshold
        ({'links': 11, 'images': 3}, True),   # Just above min links threshold
    ])
    def test_rule_fallback_links(self, stats, expected):
        """Test rule_fallback_links with various inputs."""
        thresholds = {'fallback_min_links': 10, 'fallback_max_images': 5}
        assert rule_fallback_links(stats, thresholds) is expected


@pytest.mark.describe("rule_table_catalogue tests")
class TestRuleTableCatalogue:
    def test_rule_table_catalogue_true(self, table_html):
        """Test when table catalogue rule passes (returns True)."""
        response = create_html_response(table_html)
        stats = {'tables': 1}
        thresholds = {'table_min_rows': 2}
        assert rule_table_catalogue(response, stats, thresholds) is True
    
    def test_rule_table_catalogue_false_no_tables(self):
        """Test when there are no tables (returns False)."""
        html = "<html><body><p>No tables here</p></body></html>"
        response = create_html_response(html)
        stats = {'tables': 0}
        thresholds = {'table_min_rows': 2}
        assert rule_table_catalogue(response, stats, thresholds) is False
    
    def test_rule_table_catalogue_false_too_few_rows(self):
        """Test when there are tables but too few rows (returns False)."""
        html = create_table_html(rows=1)
        response = create_html_response(html)
        stats = {'tables': 1}
        thresholds = {'table_min_rows': 2}
        assert rule_table_catalogue(response, stats, thresholds) is False
    
    def test_rule_table_catalogue_multiple_tables(self):
        """Test with multiple tables."""
        html = """
        <html>
            <body>
                <table>
                    <tbody>
                        <tr><td>Table 1 Row 1</td></tr>
                    </tbody>
                </table>
                <table>
                    <tbody>
                        <tr><td>Table 2 Row 1</td></tr>
                        <tr><td>Table 2 Row 2</td></tr>
                        <tr><td>Table 2 Row 3</td></tr>
                    </tbody>
                </table>
            </body>
        </html>
        """
        response = create_html_response(html)
        stats = {'tables': 2}
        thresholds = {'table_min_rows': 2}
        # Should pass because at least one table has enough rows
        assert rule_table_catalogue(response, stats, thresholds) is True
    
    def test_rule_table_catalogue_malformed_table(self):
        """Test with malformed table HTML."""
        html = """
        <html>
            <body>
                <table>
                    <tr><td>No tbody tag</td></tr>
                    <tr><td>But still has rows</td></tr>
                </table>
            </body>
        </html>
        """
        response = create_html_response(html)
        stats = {'tables': 1}
        thresholds = {'table_min_rows': 2}
        
        # With the improved implementation, tables without tbody should now pass
        assert rule_table_catalogue(response, stats, thresholds) is True


@pytest.mark.describe("evaluate_catalogue_rules tests")
class TestEvaluateCatalogueRules:
    def test_evaluate_catalogue_rules_all_pass(self, table_html):
        """Test when all rules pass."""
        response = create_html_response(table_html)
        stats = {'links': 30, 'iframes': 0, 'paragraphs': 10, 'images': 2, 'tables': 1}
        thresholds = {
            'link_heavy_min_links': 20,
            'link_heavy_max_iframes': 1,
            'text_heavy_min_paragraphs': 5,
            'text_heavy_max_images': 5,
            'table_min_rows': 2,
            'fallback_min_links': 10,
            'fallback_max_images': 5
        }
        rules = [
            ("link_heavy", "rule_link_heavy", 1),
            ("text_heavy", "rule_text_heavy", 2),
            ("table_catalogue", "rule_table_catalogue", 3)
        ]
        
        results = evaluate_catalogue_rules(response, stats, rules, thresholds)
        
        assert len(results) == 3
        assert all(r['passed'] for r in results)
        assert [r['name'] for r in results] == ["link_heavy", "text_heavy", "table_catalogue"]
        assert [r['weight'] for r in results] == [1, 2, 3]
    
    def test_evaluate_catalogue_rules_mixed_results(self):
        """Test with some rules passing and some failing."""
        html = """
        <html>
            <body>
                <table><tbody>
                    <tr><td>Only one row</td></tr>
                </tbody></table>
                <a href="#">Link 1</a>
                <p>Paragraph 1</p>
            </body>
        </html>
        """
        response = create_html_response(html)
        stats = {'links': 30, 'iframes': 0, 'paragraphs': 1, 'images': 10, 'tables': 1}
        thresholds = {
            'link_heavy_min_links': 20,
            'link_heavy_max_iframes': 1,
            'text_heavy_min_paragraphs': 5,
            'text_heavy_max_images': 5,
            'table_min_rows': 2,
            'fallback_min_links': 10,
            'fallback_max_images': 5
        }
        rules = [
            ("link_heavy", "rule_link_heavy", 1),
            ("text_heavy", "rule_text_heavy", 2),
            ("table_catalogue", "rule_table_catalogue", 3)
        ]
        
        results = evaluate_catalogue_rules(response, stats, rules, thresholds)
        
        assert len(results) == 3
        # link_heavy should pass, others should fail
        assert results[0]['passed'] is True
        assert results[1]['passed'] is False  # text_heavy fails (too few paragraphs, too many images)
        assert results[2]['passed'] is False  # table_catalogue fails (too few rows)
    
    def test_evaluate_catalogue_rules_error_handling(self):
        """Test error handling in rule evaluation."""
        html = "<html><body></body></html>"
        response = create_html_response(html)
        stats = {'links': 30, 'iframes': 0}  # Missing 'paragraphs' key
        thresholds = {
            'link_heavy_min_links': 20,
            'link_heavy_max_iframes': 1,
            'text_heavy_min_paragraphs': 5,
            'text_heavy_max_images': 5
        }
        
        # Define a rule function that will raise an exception
        def failing_rule(stats, thresholds):
            raise KeyError("Missing key")
        
        rules = [
            ("link_heavy", "rule_link_heavy", 1),
            ("failing_rule", "failing_rule", 2),
            ("text_heavy", "rule_text_heavy", 3)  # This will also fail due to missing 'paragraphs' key
        ]
        
        results = evaluate_catalogue_rules(response, stats, rules, thresholds)
        
        assert len(results) == 3
        assert results[0]['passed'] is True  # link_heavy passes
        assert results[1]['passed'] is False  # failing_rule fails with exception
        assert results[2]['passed'] is False  # text_heavy fails with KeyError


@pytest.mark.describe("compute_catalogue_score tests")
class TestComputeCatalogueScore:
    @pytest.mark.parametrize("results, expected", [
        # All rules pass
        ([
            {'name': 'rule1', 'passed': True, 'weight': 1},
            {'name': 'rule2', 'passed': True, 'weight': 2},
            {'name': 'rule3', 'passed': True, 'weight': 3}
        ], 6),
        # Some rules fail
        ([
            {'name': 'rule1', 'passed': True, 'weight': 1},
            {'name': 'rule2', 'passed': False, 'weight': 2},
            {'name': 'rule3', 'passed': True, 'weight': 3}
        ], 4),
        # All rules fail
        ([
            {'name': 'rule1', 'passed': False, 'weight': 1},
            {'name': 'rule2', 'passed': False, 'weight': 2},
            {'name': 'rule3', 'passed': False, 'weight': 3}
        ], 0),
    ])
    def test_compute_catalogue_score_sum(self, results, expected):
        """Test sum method for score computation."""
        assert compute_catalogue_score(results, method="sum") == expected
    
    @pytest.mark.parametrize("results, expected", [
        # All rules pass
        ([
            {'name': 'rule1', 'passed': True, 'weight': 1},
            {'name': 'rule2', 'passed': True, 'weight': 2},
            {'name': 'rule3', 'passed': True, 'weight': 3}
        ], 100.0),
        # Half of weights pass
        ([
            {'name': 'rule1', 'passed': True, 'weight': 3},
            {'name': 'rule2', 'passed': False, 'weight': 3}
        ], 50.0),
        # All rules fail
        ([
            {'name': 'rule1', 'passed': False, 'weight': 1},
            {'name': 'rule2', 'passed': False, 'weight': 2}
        ], 0.0),
        # Empty results
        ([], 0.0),
    ])
    def test_compute_catalogue_score_weighted_average(self, results, expected):
        """Test weighted_average method for score computation."""
        assert compute_catalogue_score(results, method="weighted_average") == expected
    
    @pytest.mark.parametrize("results, expected", [
        # Majority pass
        ([
            {'name': 'rule1', 'passed': True, 'weight': 1},
            {'name': 'rule2', 'passed': True, 'weight': 1},
            {'name': 'rule3', 'passed': False, 'weight': 1}
        ], True),
        # Equal split
        ([
            {'name': 'rule1', 'passed': True, 'weight': 1},
            {'name': 'rule2', 'passed': False, 'weight': 1}
        ], False),
        # Majority fail
        ([
            {'name': 'rule1', 'passed': False, 'weight': 1},
            {'name': 'rule2', 'passed': False, 'weight': 1},
            {'name': 'rule3', 'passed': True, 'weight': 1}
        ], False),
    ])
    def test_compute_catalogue_score_strict_majority(self, results, expected):
        """Test strict_majority method for score computation."""
        assert compute_catalogue_score(results, method="strict_majority") is expected
    
    def test_compute_catalogue_score_default(self):
        """Test default method (should be same as sum)."""
        results = [
            {'name': 'rule1', 'passed': True, 'weight': 1},
            {'name': 'rule2', 'passed': False, 'weight': 2},
            {'name': 'rule3', 'passed': True, 'weight': 3}
        ]
        # Default should be the same as "sum"
        assert compute_catalogue_score(results) == compute_catalogue_score(results, method="sum")
        assert compute_catalogue_score(results, method="invalid_method") == compute_catalogue_score(results, method="sum")