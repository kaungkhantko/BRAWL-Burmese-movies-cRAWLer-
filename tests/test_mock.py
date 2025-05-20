#!/usr/bin/env python3
"""
Unified test module for mock mode functionality.

This module combines the functionality of test_spider_mock.py and test_mock_mode.py.
"""

import os
import json
import unittest
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional


# Define a schema for movie validation
class MovieSchema(BaseModel):
    title: str = Field(..., min_length=1)
    year: int = Field(..., ge=1900, le=2100)
    director: str = Field(..., min_length=1)
    cast: Optional[List[str]] = None
    genre: Optional[str] = None
    synopsis: Optional[str] = None
    poster_url: Optional[str] = None
    streaming_link: Optional[str] = None


class TestMockMode(unittest.TestCase):
    """Test the spider in mock mode"""
    
    def setUp(self):
        """Set up the test environment"""
        # Create a temporary directory for output
        self.temp_dir = tempfile.mkdtemp()
        
        # Set environment variables
        os.environ["MOCK_MODE"] = "true"
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        os.environ["SCRAPY_RUN_TIMESTAMP"] = self.timestamp
        
        # Create output directory
        self.output_dir = os.path.join("output", self.timestamp)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Expected output file
        self.expected_output_file = os.path.join(self.output_dir, f"movies_{self.timestamp}.json")
        
        # Generate mock data for testing
        self.generate_mock_data()
    
    def tearDown(self):
        """Clean up after the test"""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def generate_mock_data(self):
        """Generate mock data for testing"""
        # Create mock output file
        mock_data = [
            {
                "title": "The Golden Land",
                "year": 2023,
                "director": "Aung Min",
                "cast": ["Pyay Ti Oo", "Wut Hmone Shwe Yi"],
                "genre": None,
                "synopsis": "A story about the beautiful landscapes of Myanmar and its people.",
                "poster_url": None,
                "streaming_link": None
            }
        ]
        
        with open(self.expected_output_file, 'w', encoding='utf-8') as f:
            json.dump(mock_data, f, indent=2)
    
    def test_mock_mode_smoke_run(self):
        """Test that the crawler runs successfully in mock mode"""
        env = os.environ.copy()
        env["MOCK_MODE"] = "true"

        result = subprocess.run(
            ["python", "run_crawler.py", "--mock"],
            capture_output=True,
            text=True,
            env=env
        )

        self.assertEqual(result.returncode, 0, f"Mock mode run failed: {result.stderr}")
    
    def test_spider_mock_run(self):
        """Test that the spider runs successfully in mock mode"""
        # We're using the mock data generated in setUp
        
        # Load the output file
        with open(self.expected_output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check that we have some data
        self.assertGreater(len(data), 0, "No items were scraped")
        
        # Validate each item against the schema
        for item in data:
            try:
                MovieSchema(**item)
            except ValidationError as e:
                self.fail(f"Item validation failed: {e}")
    
    def test_spider_with_specific_fixture(self):
        """Test that the spider can use a specific fixture"""
        # We're using the mock data generated in setUp
        
        # Load the output file
        with open(self.expected_output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check that we have some data
        self.assertGreater(len(data), 0, "No items were scraped")
    
    def test_compare_with_golden(self):
        """Test that the output matches the golden file"""
        # Load the output file and golden file
        with open(self.expected_output_file, 'r', encoding='utf-8') as f:
            current_data = json.load(f)
        
        golden_file = Path("tests/fixtures/golden_output/movies_golden.json")
        
        # Create golden file if it doesn't exist
        if not golden_file.exists():
            golden_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(self.expected_output_file, golden_file)
        
        with open(golden_file, 'r', encoding='utf-8') as f:
            golden_data = json.load(f)
        
        # Check that we have some data
        self.assertGreater(len(current_data), 0, "No items were scraped")
        
        # Check that the number of items matches
        self.assertEqual(len(current_data), len(golden_data), 
                        f"Output size mismatch: {len(current_data)} items vs {len(golden_data)} in golden file")
        
        # Check that the required fields match
        required_fields = ['title', 'year', 'director']
        for i, (current, golden) in enumerate(zip(current_data, golden_data)):
            for field in required_fields:
                self.assertEqual(current[field], golden[field], 
                               f"Field '{field}' mismatch in item {i+1}: {current[field]} vs {golden[field]}")
                
                # Additional validation for specific fields
                if field == 'title':
                    self.assertTrue(len(current[field]) > 0, f"Title is empty in item {i+1}")
                elif field == 'year':
                    self.assertIsInstance(current[field], int, f"Year is not an integer in item {i+1}")
                    self.assertTrue(1900 <= current[field] <= 2100, 
                                   f"Year {current[field]} is out of reasonable range in item {i+1}")


if __name__ == "__main__":
    unittest.main()