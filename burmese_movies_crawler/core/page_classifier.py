"""
Page classifier for the Burmese Movies Crawler.

This module provides functionality for classifying pages as catalogue or detail pages.
"""

from scrapy.http import HtmlResponse
from typing import Dict, List, Tuple, Any

from burmese_movies_crawler.core.link_utils import (
    extract_page_stats, rule_detail_like,
    evaluate_catalogue_rules, compute_catalogue_score
)
from burmese_movies_crawler.config import DEFAULT_RULE_THRESHOLDS, CATALOGUE_RULES


class PageClassifier:
    """
    Classifier for determining page types (catalogue or detail).
    """
    
    def __init__(self, thresholds: Dict[str, int] = None, rules: List[Tuple[str, str, int]] = None):
        """
        Initialize the page classifier.
        
        Args:
            thresholds: Rule thresholds
            rules: List of rules
        """
        self.thresholds = thresholds or DEFAULT_RULE_THRESHOLDS
        self.rules = rules or CATALOGUE_RULES

    def is_catalogue_page(self, response: HtmlResponse) -> bool:
        """
        Determine if a page is a catalogue page.
        
        Args:
            response: The response object
            
        Returns:
            True if the page is a catalogue page
        """
        stats = extract_page_stats(response)
        if not rule_detail_like(stats):
            rule_results = evaluate_catalogue_rules(response, stats, self.rules, self.thresholds)
            score = compute_catalogue_score(rule_results, method="sum")
            return score >= self.thresholds['score_threshold']
        return False

    def is_detail_page(self, response: HtmlResponse) -> bool:
        """
        Determine if a page is a detail page.
        
        Args:
            response: The response object
            
        Returns:
            True if the page is a detail page
        """
        stats = extract_page_stats(response)
        return rule_detail_like(stats)