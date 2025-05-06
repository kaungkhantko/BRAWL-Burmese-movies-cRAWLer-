# # burmese_movies_crawler/utils/page_classifier.py

from scrapy.http import HtmlResponse
from .link_utils import *
from burmese_movies_crawler.utils.link_utils import (
    extract_page_stats, rule_detail_like,
    rule_link_heavy, rule_text_heavy, rule_table_catalogue, rule_fallback_links,
    evaluate_catalogue_rules, compute_catalogue_score
)

class PageClassifier:
    def __init__(self, thresholds, rules):
        self.thresholds = thresholds
        self.rules = rules

    def is_catalogue_page(self, response):
        stats = extract_page_stats(response)
        if not rule_detail_like(stats):
            rule_results = evaluate_catalogue_rules(response, stats, self.rules, self.thresholds)
            score = compute_catalogue_score(rule_results, method="sum")
            return score >= self.thresholds['score_threshold']
        return False

        return score >= threshold

    def is_detail_page(self, response):
        stats = extract_page_stats(response)
        return rule_detail_like(stats)