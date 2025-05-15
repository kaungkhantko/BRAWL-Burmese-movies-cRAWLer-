# # burmese_movies_crawler/utils/link_utils.py

from urllib.parse import urlparse
import logging
from scrapy.http import HtmlResponse
import hashlib
from burmese_movies_crawler.settings import MOCK_MODE
logger = logging.getLogger(__name__)
import scrapy
import os

from urllib.parse import urlparse

def is_valid_link(url, invalid_links_log=None):
    """
    Centralized validation for link filtering and logging.

    Parameters:
    - url (str): The fully resolved URL (after urljoin and urldefrag).
    - invalid_links_log (list): Optional list to append (reason, url) for invalid entries.

    Returns:
    - bool: True if the URL is valid for crawling.
    """
    def log(reason):
        if invalid_links_log is not None:
            invalid_links_log.append((reason, url))

    if not isinstance(url, str):
        log("Non-string input")
        return False

    url = url.strip()
    url_lower = url.lower()

    # Reject obvious garbage or placeholders
    if url_lower in ("", "none", "void(0)"):
        log("Empty or None")
        return False
    if url_lower.startswith('#'):
        log("Fragment-only link")
        return False

    # Reject known non-crawlable schemes
    if url_lower.startswith(('javascript:', 'mailto:', 'tel:')):
        log("Non-crawlable scheme")
        return False

    parsed = urlparse(url)

    # Allow valid absolute http/https URLs
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return True

    # Accept clean relative URLs (must look like real paths)
    if not parsed.scheme and parsed.path and parsed.path.startswith(("/", "./", "../")):
        return True

    log("Unsupported or malformed URL format")
    return False

def extract_page_stats(response):
    """Count basic elements on the page for classification."""
    return {
        'links': len(response.xpath('//a')),
        'images': len(response.xpath('//img')),
        'iframes': len(response.xpath('//iframe')),
        'paragraphs': len(response.xpath('//p')),
        'tables': len(response.xpath('//table')),
    }

def rule_detail_like(stats):
    """Negative rule: pages with iframes but very few links look like detail pages."""
    return not (stats['iframes'] >= 1 and stats['links'] < 30)

def rule_link_heavy(stats, thresholds):
    return stats['links'] > thresholds['link_heavy_min_links'] and \
           stats['iframes'] <= thresholds['link_heavy_max_iframes']

def rule_text_heavy(stats, thresholds):
    return stats['paragraphs'] > thresholds['text_heavy_min_paragraphs'] and \
           stats['images'] <= thresholds['text_heavy_max_images']

def rule_table_catalogue(response, stats, thresholds):
    if stats['tables'] >= 1:
        rows = response.css('table tbody tr')
        return len(rows) >= thresholds['table_min_rows']
    return False

def rule_fallback_links(stats, thresholds):
    return stats['links'] > thresholds['fallback_min_links'] and \
           stats['images'] <= thresholds['fallback_max_images']

def evaluate_catalogue_rules(response, stats, rules, thresholds):
    """
    Run each rule function and collect (name, passed, weight).
    `rules` is a list of (name, fn, weight) where fn takes either
    (stats, thresholds) or (response, stats, thresholds) for table rules.
    """
    results = []
    for name, rule_fn, weight in rules:
        try:
            passed = rule_fn(response, stats, thresholds) if name == "table_catalogue" else rule_fn(stats, thresholds)
            results.append({'name': name, 'passed': passed, 'weight': weight})
        except Exception as e:
            logger.error(f"[Rule Error] {name}: {e}")
            results.append({'name': name, 'passed': False, 'weight': weight})
    return results

def compute_catalogue_score(rule_results, method="sum"):
    """
    Combine rule_results into a single score or boolean.
    rule_results: [{'name':..., 'passed':bool, 'weight':int}, ...]
    """
    if method == "sum":
        return sum(r['weight'] for r in rule_results if r['passed'])
    elif method == "weighted_average":
        total = sum(r['weight'] for r in rule_results)
        passed = sum(r['weight'] for r in rule_results if r['passed'])
        return (passed / total) * 100 if total else 0
    elif method == "strict_majority":
        return sum(r['passed'] for r in rule_results) > len(rule_results) / 2
    return sum(r['weight'] for r in rule_results if r['passed'])

def get_response_or_request(url: str, callback):
    if MOCK_MODE:
        # Safe hash-based naming (MD5)
        hashname = hashlib.md5(url.encode()).hexdigest()
        fixture_path = os.path.join("tests", "fixtures", f"{hashname}.html")

        if not os.path.exists(fixture_path):
            raise FileNotFoundError(f"[MOCK_MODE] Fixture not found for {url} ({fixture_path})")

        with open(fixture_path, encoding="utf-8") as f:
            html = f.read()

        return HtmlResponse(url=f"mock://{hashname}", body=html, encoding="utf-8")
    else:
        return scrapy.Request(url=url, callback=callback)