"""
Mock utilities for the Burmese Movies Crawler.

This module provides functions for handling test fixtures and mock mode.
"""

import os
import re
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, Optional, List

import scrapy
from scrapy.http import HtmlResponse

from burmese_movies_crawler.config import FIXTURES_DIR, OUTPUT_DIR


def url_to_fixture_name(url: str) -> str:
    """
    Convert a URL to a readable fixture name.
    
    Args:
        url: The URL to convert
        
    Returns:
        A readable fixture name
    """
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    
    # Clean up the path
    path = parsed.path.strip("/")
    if not path:
        path = "home"
    
    # Replace special characters with underscores
    path = re.sub(r'[^a-zA-Z0-9]', '_', path)
    
    # Truncate if too long
    if len(path) > 50:
        path = path[:50]
    
    # Create a readable name
    readable_name = f"{domain}_{path}"
    
    # Add a hash suffix for uniqueness (first 8 chars of MD5)
    hash_suffix = hashlib.md5(url.encode()).hexdigest()[:8]
    
    return f"{readable_name}_{hash_suffix}.html"


def get_fixture_mapping() -> Dict[str, str]:
    """
    Load the fixture mapping from the fixture_mapping.json file.
    If the file doesn't exist, create an empty mapping.
    
    Returns:
        A mapping of URLs to fixture names
    """
    mapping_path = FIXTURES_DIR / "fixture_mapping.json"
    if mapping_path.exists():
        with open(mapping_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_fixture_mapping(mapping: Dict[str, str]) -> None:
    """
    Save the fixture mapping to the fixture_mapping.json file.
    
    Args:
        mapping: A mapping of URLs to fixture names
    """
    mapping_path = FIXTURES_DIR / "fixture_mapping.json"
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2)


def get_response_or_request(url: str, callback, fixture_name: Optional[str] = None):
    """
    Get a response from a fixture or create a request.
    
    Args:
        url: The URL to request
        callback: The callback function for the request
        fixture_name: The name of the fixture to use. If None, 
                     will try to find a matching fixture.
    
    Returns:
        A request or response object
    """
    from burmese_movies_crawler.config import MOCK_MODE
    
    if MOCK_MODE:
        # Load the fixture mapping
        fixture_mapping = get_fixture_mapping()
        
        # If a specific fixture name is provided, use it
        if fixture_name:
            fixture_path = FIXTURES_DIR / fixture_name
        else:
            # Check if we have a mapping for this URL
            if url in fixture_mapping:
                fixture_path = FIXTURES_DIR / fixture_mapping[url]
            else:
                # Generate a readable name for the fixture
                readable_name = url_to_fixture_name(url)
                fixture_path = FIXTURES_DIR / readable_name
                
                # If the readable name doesn't exist, try the hash-based name for backward compatibility
                if not fixture_path.exists():
                    hashname = hashlib.md5(url.encode()).hexdigest()
                    old_fixture_path = FIXTURES_DIR / f"{hashname}.html"
                    
                    if old_fixture_path.exists():
                        # If the old hash-based fixture exists, update the mapping
                        fixture_mapping[url] = f"{hashname}.html"
                        save_fixture_mapping(fixture_mapping)
                        fixture_path = old_fixture_path

        if not fixture_path.exists():
            raise FileNotFoundError(f"[MOCK_MODE] Fixture not found for {url} ({fixture_path})")

        with open(fixture_path, encoding="utf-8") as f:
            html = f.read()

        # Extract the fixture name from the path
        fixture_filename = fixture_path.name
        
        # Update the mapping if needed
        if url not in fixture_mapping:
            fixture_mapping[url] = fixture_filename
            save_fixture_mapping(fixture_mapping)

        # Create a request object to include in the response
        request = scrapy.Request(url=url)
        if fixture_name:
            request.meta['fixture_name'] = fixture_name
            
        return HtmlResponse(url=url, body=html.encode('utf-8'), encoding="utf-8", request=request)
    else:
        return scrapy.Request(url=url, callback=callback)


def generate_mock_output(timestamp: str = "mock-test") -> str:
    """
    Generate mock output data for testing.
    
    Args:
        timestamp: Timestamp to use for the output directory
        
    Returns:
        Path to the output directory
    """
    # Create the output directory
    output_dir = OUTPUT_DIR / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create the movies output file
    movies_data = [
        {
            "title": "The Golden Land",
            "year": 2023,
            "director": "Aung Min",
            "cast": ["Pyay Ti Oo", "Wut Hmone Shwe Yi"],
            "genre": None,
            "synopsis": "A story about the beautiful landscapes of Myanmar and its people.",
            "poster_url": None,
            "streaming_link": None
        },
        {
            "title": "The River Flows",
            "year": 2022,
            "director": "Kyi Phyu Shin",
            "cast": ["Nay Toe", "May Myint Mo"],
            "genre": None,
            "synopsis": None,
            "poster_url": None,
            "streaming_link": None
        },
        {
            "title": "The Ancient City",
            "year": 2021,
            "director": "Min Htin Ko Ko Gyi",
            "cast": ["Kyaw Hein", "Wyne Su Khine Thein"],
            "genre": None,
            "synopsis": None,
            "poster_url": None,
            "streaming_link": None
        }
    ]
    
    movies_file = output_dir / f"movies_{timestamp}.json"
    with open(movies_file, 'w', encoding='utf-8') as f:
        json.dump(movies_data, f, indent=2, ensure_ascii=False)
    
    # Create the summary file
    summary_data = {
        "spider_name": "movies",
        "start_time": "2025-05-18T17:00:00Z",
        "end_time": "2025-05-18T17:00:01Z",
        "runtime_seconds": 1.0,
        "items_scraped": 3,
        "warnings": [],
        "errors": [],
        "movies_output_file": str(movies_file),
        "log_file": str(output_dir / f"crawler_output_{timestamp}.log"),
        "close_reason": "finished",
        "mock_mode": True,
        "fixtures_used": [
            "channelmyanmar_to_movies_81376cf1.html",
            "mock_detail_page.html"
        ]
    }
    
    summary_file = output_dir / f"run_summary_{timestamp}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=4, ensure_ascii=False)
    
    # Create an empty log file
    log_file = output_dir / f"crawler_output_{timestamp}.log"
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("# Mock log file\n")
    
    print(f"Mock data generated in {output_dir}")
    return str(output_dir)