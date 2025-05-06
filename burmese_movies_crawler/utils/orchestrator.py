# # burmese_movies_crawler/utils/orchestrator.py

from scrapy.http import HtmlResponse
from burmese_movies_crawler.utils.page_classifier import PageClassifier
from burmese_movies_crawler.utils.field_extractor import FieldExtractor
from burmese_movies_crawler.candidate_extractor import extract_candidate_blocks
from burmese_movies_crawler.openai_selector import query_openai_for_best_selector
import logging

logger = logging.getLogger(__name__)
def handle_page(html: str, url: str,
                classifier: PageClassifier,
                extractor: FieldExtractor,
                content_type: str = "movies") -> dict:

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
        idx = query_openai_for_best_selector(candidates)
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
