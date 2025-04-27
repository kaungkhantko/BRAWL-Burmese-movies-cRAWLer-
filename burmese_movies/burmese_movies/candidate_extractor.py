from bs4 import BeautifulSoup

def extract_candidate_blocks(page_source, max_candidates=10):
    """Extract top candidate movie blocks from page HTML using simple rules."""
    soup = BeautifulSoup(page_source, 'html.parser')
    candidates = []

    # Look for div, section, article blocks
    for tag in soup.find_all(['div', 'section', 'article']):
        # Basic heuristic: contains an image and a link, and some text
        has_img = tag.find('img') is not None
        has_link = tag.find('a') is not None
        text_len = len(tag.get_text(strip=True))

        if has_img and has_link and text_len > 30:
            # Summarize this block nicely: outerHTML
            snippet = str(tag)[:1500]  # Limit snippet size to avoid giant blocks
            candidates.append(snippet)

    # Limit number of candidates
    return candidates[:max_candidates]
