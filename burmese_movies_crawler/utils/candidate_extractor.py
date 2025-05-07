from bs4 import BeautifulSoup

BLACKLIST_KEYWORDS = ["login", "subscribe", "advertisement", "sponsored", "cookie"]

def extract_candidate_blocks(page_source, max_candidates=5):
    """
    Extracts top candidate movie blocks from page HTML using structural and content heuristics.
    Returns up to `max_candidates` HTML snippets (str).
    """
    soup = BeautifulSoup(page_source, 'html.parser')
    raw_candidates = []

    for tag in soup.select('div, section, article'):
        has_img = tag.find('img') is not None
        has_link = tag.find('a') is not None
        block_text = tag.get_text(strip=True).lower()

        # Basic heuristics
        if not (has_img and has_link and len(block_text) > 30):
            continue

        # Filter out junk content
        if any(bad_word in block_text for bad_word in BLACKLIST_KEYWORDS):
            continue

        snippet = str(tag)[:1500]  # Truncate to avoid overly large blocks
        raw_candidates.append((snippet, len(block_text)))  # Store with length for ranking

    # Rank by extracted text length
    ranked_candidates = sorted(raw_candidates, key=lambda x: x[1], reverse=True)

    # Return only HTML snippets (strip the length scores)
    return [snippet for snippet, _ in ranked_candidates[:max_candidates]]
