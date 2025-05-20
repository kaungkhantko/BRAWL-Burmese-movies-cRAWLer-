"""
Orchestrator for the Burmese Movies Crawler.

This module provides functionality for handling page processing and extraction.
"""

from scrapy.http import HtmlResponse
import logging

from burmese_movies_crawler.core.page_classifier import PageClassifier
from burmese_movies_crawler.core.extractors.engine import ExtractorEngine
from burmese_movies_crawler.utils.candidate_extractor import extract_candidate_blocks
from burmese_movies_crawler.utils.trafilatura_selectorr import pick_movie_block_with_trafilatura

logger = logging.getLogger(__name__)


def handle_page(
    html: str, 
    url: str,
    classifier: PageClassifier,
    extractor: ExtractorEngine,
    content_type: str = "movies"
) -> dict:
    """
    Handle a page by classifying it and extracting data.
    
    Args:
        html: The HTML content
        url: The URL of the page
        classifier: The page classifier
        extractor: The extractor engine
        content_type: The content type
        
    Returns:
        Dictionary with page type and extracted data
    """
    response = HtmlResponse(url=url, body=html, encoding='utf-8')

    if classifier.is_catalogue_page(response): 
        links = extractor.extract_links(response)
        next_page = response.css('a.next.page-numbers::attr(href)').get()
        return {"type": "catalogue", "links": links, "next_page": next_page}

    if classifier.is_detail_page(response):
        data = extractor.extract_main_fields(response)
        data.update(extractor.extract_paragraphs(response))
        return {"type": "detail", "item": data}

    # fallback via LLM
    candidates = extract_candidate_blocks(html)
    if not candidates:
        return {"type": "unknown", "fallback_links": []}

    try:
        idx = pick_movie_block_with_trafilatura(candidates)
        block_html = candidates[idx]
    except Exception as e:
        logger.warning(f"[LLM fallback failed] for {url}: {e}")
        return {"type": "unknown", "fallback_links": [], "llm_error": str(e)}

    # generate one-off fake detail page
    fake_resp = HtmlResponse(url=url, body=block_html, encoding='utf-8')
    try:
        data = extractor.extract_main_fields(fake_resp)
        data.update(extractor.extract_paragraphs(fake_resp))
        return {"type": "detail", "item": data}
    except Exception as e:
        logger.warning(f"[LLM fallback failed] for {url}: {e}")
        return {"type": "unknown", "fallback_links": [], "extractor_error": str(e)}