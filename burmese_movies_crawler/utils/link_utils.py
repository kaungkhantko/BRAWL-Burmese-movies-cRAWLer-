from urllib.parse import urlparse
import logging
from scrapy.http import HtmlResponse

logger = logging.getLogger(__name__)

def is_valid_link(url, invalid_links_log=None):
    """
    Check if the given URL is valid for crawling.

    Parameters:
    - url (str): The URL to validate.
    - invalid_links_log (list): Optional list to append (reason, url) for invalid entries.

    Returns:
    - bool: True if the URL is valid, False otherwise.
    """
    def log(reason):
        if invalid_links_log is not None:
            invalid_links_log.append((reason, url))

    if not isinstance(url, str):
        log("Non-string input")
        return False

    if not url:
        log("Empty URL")
        return False

    url_normalized = url.strip().lower()

    if url_normalized.startswith(('javascript:', 'mailto:', 'tel:')):
        log("Non-crawlable scheme")
        return False

    if url_normalized in ['#', 'void(0)', 'none', '']:
        log("Placeholder or fragment")
        return False

    if url_normalized.startswith('//'):
        log("Protocol-relative URL")
        return False

    parsed = urlparse(url_normalized)

    if not (
        url_normalized.startswith('/') or
        url_normalized.startswith('./') or
        url_normalized.startswith('../') or
        (parsed.scheme in ('http', 'https') and parsed.netloc)
    ):
        log("Unsupported URL format")
        return False

    return True

def extract_page_stats(response):
    return {
        'links': len(response.xpath('//a')),
        'images': len(response.xpath('//img')),
        'iframes': len(response.xpath('//iframe')),
        'paragraphs': len(response.xpath('//p')),
        'tables': len(response.xpath('//table')),
    }

def rule_detail_like(stats):
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
    if method == "sum":
        return sum(r['weight'] for r in rule_results if r['passed'])
    elif method == "weighted_average":
        total = sum(r['weight'] for r in rule_results)
        passed = sum(r['weight'] for r in rule_results if r['passed'])
        return (passed / total) * 100 if total else 0
    elif method == "strict_majority":
        return sum(r['passed'] for r in rule_results) > len(rule_results) / 2
    return sum(r['weight'] for r in rule_results if r['passed'])

def is_catalogue_page(self, response):
    stats = {
        'links': len(response.xpath('//a')),
        'images': len(response.xpath('//img')),
        'iframes': len(response.xpath('//iframe')),
        'paragraphs': len(response.xpath('//p')),
        'tables': len(response.xpath('//table'))
    }
    logger.info(f"[Page stats] {stats}")

    if not self._rule_detail_like(stats):
        logger.info("Page likely a DETAIL page.")
        return False

    rule_results = self.evaluate_catalogue_rules(response, stats)

    score = self.compute_catalogue_score(rule_results, method=self.DEFAULT_RULE_THRESHOLDS.get('scoring_method', 'sum'))

    if isinstance(score, bool):
        return score  # For strict_majority style

    threshold = self.DEFAULT_RULE_THRESHOLDS.get('score_threshold', 3)
    logger.info(f"[Catalogue Score] {score} (Threshold={threshold})")

    return score >= threshold

def is_detail_page(response):
    return bool(response.css('h1.entry-title, h1.title, div.movie-title').get())
