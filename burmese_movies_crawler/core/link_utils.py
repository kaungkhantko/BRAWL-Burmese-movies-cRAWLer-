"""
Link utilities for the Burmese Movies Crawler.

This module provides functions for handling links, URL validation, and page classification.
"""

from urllib.parse import urlparse
import logging
import re
from scrapy.http import HtmlResponse
from typing import Dict, List, Tuple, Any, Optional

logger = logging.getLogger(__name__)


def is_valid_link(url: str, invalid_links_log: Optional[List] = None) -> bool:
    """
    Centralized validation for link filtering and logging.

    Args:
        url: The fully resolved URL (after urljoin and urldefrag).
        invalid_links_log: Optional list to append (reason, url) for invalid entries.

    Returns:
        True if the URL is valid for crawling.
    """
    def log(reason):
        if invalid_links_log is not None:
            invalid_links_log.append((reason, url))

    if not isinstance(url, str):
        log("Non-string input")
        return False

    url = url.strip()
    url_lower = url.lower()

    # Parse URL first so we can use it for validation
    parsed = urlparse(url)
    
    # Reject obvious garbage or placeholders
    if url_lower in ("", "none", "void(0)") or url_lower.endswith("/none"):
        log("Empty or None")
        return False
    
    # Reject fragment-only links or base URLs without paths
    if url_lower.startswith('#') or (parsed.scheme in ('http', 'https') and parsed.netloc and (not parsed.path or parsed.path == '/')):
        log("Fragment-only link or base URL")
        return False

    # Reject known non-crawlable schemes
    if url_lower.startswith(('javascript:', 'mailto:', 'tel:')):
        log("Non-crawlable scheme")
        return False

    # Allow valid absolute http/https URLs
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return True

    # Accept clean relative URLs (must look like real paths)
    if not parsed.scheme and parsed.path and parsed.path.startswith(("/", "./", "../")):
        return True

    log("Unsupported or malformed URL format")
    return False


def extract_page_stats(response: HtmlResponse) -> Dict[str, int]:
    """
    Count basic elements on the page for classification.
    
    Args:
        response: The response object
        
    Returns:
        Dictionary of element counts
    """
    return {
        'links': len(response.xpath('//a')),
        'images': len(response.xpath('//img')),
        'iframes': len(response.xpath('//iframe')),
        'paragraphs': len(response.xpath('//p')),
        'tables': len(response.xpath('//table')),
    }


def rule_detail_like(stats: Dict[str, int]) -> bool:
    """
    Negative rule: pages with iframes but very few links look like detail pages.
    
    Args:
        stats: Page statistics
        
    Returns:
        True if the page is likely a detail page
    """
    return not (stats['iframes'] >= 1 and stats['links'] < 30)


def rule_link_heavy(stats: Dict[str, int], thresholds: Dict[str, int]) -> bool:
    """
    Rule for link-heavy pages.
    
    Args:
        stats: Page statistics
        thresholds: Rule thresholds
        
    Returns:
        True if the page is link-heavy
    """
    return (stats['links'] > thresholds['link_heavy_min_links'] and 
            stats['iframes'] <= thresholds['link_heavy_max_iframes'])


def rule_text_heavy(stats: Dict[str, int], thresholds: Dict[str, int]) -> bool:
    """
    Rule for text-heavy pages.
    
    Args:
        stats: Page statistics
        thresholds: Rule thresholds
        
    Returns:
        True if the page is text-heavy
    """
    return (stats['paragraphs'] > thresholds['text_heavy_min_paragraphs'] and 
            stats['images'] <= thresholds['text_heavy_max_images'])


def rule_table_catalogue(response: HtmlResponse, stats: Dict[str, int], thresholds: Dict[str, int]) -> bool:
    """
    Rule for table-based catalogue pages.
    
    Args:
        response: The response object
        stats: Page statistics
        thresholds: Rule thresholds
        
    Returns:
        True if the page is a table-based catalogue
    """
    if stats['tables'] >= 1:
        rows = response.css('table tbody tr') or response.css('table tr')
        return len(rows) >= thresholds['table_min_rows']
    return False


def rule_fallback_links(stats: Dict[str, int], thresholds: Dict[str, int]) -> bool:
    """
    Fallback rule for link-based pages.
    
    Args:
        stats: Page statistics
        thresholds: Rule thresholds
        
    Returns:
        True if the page passes the fallback link rule
    """
    return (stats['links'] > thresholds['fallback_min_links'] and 
            stats['images'] <= thresholds['fallback_max_images'])


def evaluate_catalogue_rules(
    response: HtmlResponse, 
    stats: Dict[str, int], 
    rules: List[Tuple[str, str, int]], 
    thresholds: Dict[str, int]
) -> List[Dict[str, Any]]:
    """
    Run each rule function and collect results.
    
    Args:
        response: The response object
        stats: Page statistics
        rules: List of (name, function_name, weight) tuples
        thresholds: Rule thresholds
        
    Returns:
        List of rule results
    """
    results = []
    rule_functions = {
        "rule_link_heavy": rule_link_heavy,
        "rule_text_heavy": rule_text_heavy,
        "rule_table_catalogue": rule_table_catalogue,
        "rule_fallback_links": rule_fallback_links
    }
    
    for name, rule_fn_name, weight in rules:
        try:
            rule_fn = rule_functions.get(rule_fn_name)
            if not rule_fn:
                logger.error(f"Rule function {rule_fn_name} not found")
                continue
                
            passed = rule_fn(response, stats, thresholds) if rule_fn_name == "rule_table_catalogue" else rule_fn(stats, thresholds)
            results.append({'name': name, 'passed': passed, 'weight': weight})
        except Exception as e:
            logger.error(f"[Rule Error] {name}: {e}")
            results.append({'name': name, 'passed': False, 'weight': weight})
    return results


def compute_catalogue_score(rule_results: List[Dict[str, Any]], method: str = "sum") -> float:
    """
    Combine rule_results into a single score or boolean.
    
    Args:
        rule_results: List of rule results
        method: Method to use for computing the score
        
    Returns:
        Score or boolean result
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