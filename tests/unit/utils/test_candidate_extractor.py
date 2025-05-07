import pytest
import json
from pathlib import Path
from burmese_movies_crawler.utils.candidate_extractor import extract_candidate_blocks

FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures"

def read_fixture(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def find_html_fixtures(content_type: str = "movies"):
    """Recursively collect HTML files under the media type directory."""
    fixture_dir = FIXTURE_ROOT / content_type
    return list(fixture_dir.glob("*.html"))

@pytest.mark.parametrize("fixture_path", find_html_fixtures("movies"))
def test_candidate_block_extraction_on_movie_fixtures(fixture_path):
    html = read_fixture(fixture_path)
    candidates = extract_candidate_blocks(html, max_candidates=5)

    assert isinstance(candidates, list)
    assert all(isinstance(c, str) for c in candidates)

    # Heuristic expectations (can expand later via sidecar .json files)
    if "catalog" in fixture_path.name.lower():
        assert len(candidates) >= 1, f"Expected some candidates in catalog: {fixture_path.name}"
    elif "empty" in fixture_path.name.lower():
        assert len(candidates) == 0, f"Expected no candidates in empty page: {fixture_path.name}"
    elif "ad" in fixture_path.name.lower():
        assert all("advertisement" not in c.lower() and "login" not in c.lower() for c in candidates)

def test_malformed_html_still_extracts():
    html = "<div><a href='/watch'><img src='poster.jpg'><p>Great movie</div>"
    candidates = extract_candidate_blocks(html)
    assert len(candidates) == 1
    assert "Great movie" in candidates[0]
