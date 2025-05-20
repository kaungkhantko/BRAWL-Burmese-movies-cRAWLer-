"""
Configuration module for the Burmese Movies Crawler.

This module centralizes all configuration settings and environment variables
used throughout the application.
"""

import os
from datetime import datetime
from pathlib import Path

# Core settings
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"
BOT_NAME = "burmese_movies_crawler"
SPIDER_MODULES = ["burmese_movies_crawler.spiders"]
NEWSPIDER_MODULE = "burmese_movies_crawler.spiders"

# Paths and directories
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
FIXTURES_DIR = BASE_DIR / "tests" / "fixtures"
GOLDEN_OUTPUT_DIR = FIXTURES_DIR / "golden_output"

# Timestamp handling
def get_timestamp():
    """Get the current timestamp or use the one from environment."""
    return os.getenv("SCRAPY_RUN_TIMESTAMP", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

# Spider settings
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 3
CLOSESPIDER_TIMEOUT = 85  # 85 seconds (slightly less than our 90 second timeout)

# Default timeout for spider execution (in seconds)
DEFAULT_TIMEOUT = 90

# Item pipeline
ITEM_PIPELINES = {
   "burmese_movies_crawler.pipelines.BurmeseMoviesPipeline": 100,
}

# Twisted reactor
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# Default rule thresholds for page classification
DEFAULT_RULE_THRESHOLDS = {
    'link_heavy_min_links': 50,
    'link_heavy_max_iframes': 0,
    'text_heavy_min_paragraphs': 50,
    'text_heavy_max_images': 5,
    'fallback_min_links': 30,
    'fallback_max_images': 5,
    'table_min_rows': 3,
    'score_threshold': 4,
}

# Spider start URLs
START_URLS = [
    "https://www.channelmyanmar.to/movies/",
    "https://en.wikipedia.org/wiki/List_of_Burmese_films",
    "https://www.imdb.com/search/title/?country_of_origin=MM",
    "https://www.savemyanmarfilm.org/film-catalogue/"
]

# Catalogue rules for page classification
CATALOGUE_RULES = [
    ("link_heavy", "rule_link_heavy", 2),
    ("text_heavy", "rule_text_heavy", 2),
    ("table_catalogue", "rule_table_catalogue", 3),
    ("fallback_links", "rule_fallback_links", 1),
]