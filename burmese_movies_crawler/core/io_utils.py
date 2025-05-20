"""
I/O utilities for the Burmese Movies Crawler.

This module provides functions for handling file operations, JSON processing,
and output formatting.
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from burmese_movies_crawler.config import OUTPUT_DIR, GOLDEN_OUTPUT_DIR, get_timestamp


def setup_output_paths(timestamp: Optional[str] = None) -> Dict[str, str]:
    """
    Set up output paths for a crawler run.
    
    Args:
        timestamp: Optional timestamp to use. If None, uses the current time.
        
    Returns:
        Dictionary containing paths for output files
    """
    if timestamp is None:
        timestamp = get_timestamp()
        
    output_dir = OUTPUT_DIR / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return {
        "timestamp": timestamp,
        "output_dir": str(output_dir),
        "movies_output_file": str(output_dir / f"movies_{timestamp}.json"),
        "log_file": str(output_dir / f"crawler_output_{timestamp}.log"),
        "summary_file": str(output_dir / f"run_summary_{timestamp}.json"),
    }


def save_json(data: Any, file_path: Union[str, Path], indent: int = 4) -> None:
    """
    Save data as JSON to the specified file path.
    
    Args:
        data: Data to save
        file_path: Path to save the file
        indent: JSON indentation level
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_json(file_path: Union[str, Path]) -> Any:
    """
    Load JSON data from the specified file path.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON data
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_run_summary(
    summary_file: Union[str, Path],
    spider_name: str,
    start_time: datetime,
    end_time: datetime,
    items_scraped: int,
    warnings: List[str],
    errors: List[str],
    movies_output_file: str,
    log_file: str,
    close_reason: str,
    mock_mode: bool,
    fixtures_used: Optional[List[str]] = None
) -> None:
    """
    Save a summary of the crawler run.
    
    Args:
        summary_file: Path to save the summary
        spider_name: Name of the spider
        start_time: Start time of the run
        end_time: End time of the run
        items_scraped: Number of items scraped
        warnings: List of warnings
        errors: List of errors
        movies_output_file: Path to the movies output file
        log_file: Path to the log file
        close_reason: Reason for closing the spider
        mock_mode: Whether the spider was run in mock mode
        fixtures_used: List of fixtures used (only in mock mode)
    """
    summary = {
        "spider_name": spider_name,
        "start_time": start_time.isoformat() if start_time else None,
        "end_time": end_time.isoformat() if end_time else None,
        "runtime_seconds": (end_time - start_time).total_seconds() if start_time else None,
        "items_scraped": items_scraped,
        "warnings": warnings,
        "errors": errors,
        "movies_output_file": movies_output_file,
        "log_file": log_file,
        "close_reason": close_reason,
        "mock_mode": mock_mode
    }
    
    # Add fixtures used if in mock mode
    if mock_mode and fixtures_used:
        summary["fixtures_used"] = fixtures_used
    
    save_json(summary, summary_file)


def print_run_summary(output_dir: Union[str, Path]) -> None:
    """
    Print a summary of the crawler run.
    
    Args:
        output_dir: Path to the output directory
    """
    output_dir = Path(output_dir)
    
    # Find the movies output file
    movies_files = list(output_dir.glob("movies_*.json"))
    if not movies_files:
        print("❌ No output files found!")
        return
    
    movies_file = movies_files[0]
    
    # Load the movies data
    try:
        movies_data = load_json(movies_file)
    except json.JSONDecodeError:
        print(f"❌ Error parsing {movies_file} - Invalid JSON")
        return
    except Exception as e:
        print(f"❌ Error reading {movies_file}: {str(e)}")
        return
    
    # Load the summary file if it exists
    summary_files = list(output_dir.glob("run_summary_*.json"))
    run_summary = {}
    if summary_files:
        try:
            run_summary = load_json(summary_files[0])
        except:
            pass
    
    # Print the summary
    print("\n📊 Run Summary:")
    print(f"  📁 Output directory: {output_dir}")
    print(f"  🎬 Movies scraped: {len(movies_data)}")
    
    if run_summary:
        if 'runtime_seconds' in run_summary:
            print(f"  ⏱️ Runtime: {run_summary['runtime_seconds']:.2f} seconds")
        if 'errors' in run_summary and run_summary['errors']:
            print(f"  ❌ Errors: {len(run_summary['errors'])}")
    
    # Print the first few movies
    if movies_data:
        print("\n📽️ First few movies:")
        for i, movie in enumerate(movies_data[:3]):
            print(f"  {i+1}. {movie.get('title', 'Unknown')} ({movie.get('year', 'Unknown')})")
            if 'director' in movie:
                print(f"     Director: {movie['director']}")
        
        if len(movies_data) > 3:
            print(f"  ... and {len(movies_data) - 3} more")
    else:
        print("\n⚠️ Warning: No movies were scraped!")


def compare_with_golden(output_dir: Union[str, Path], update_golden: bool = False) -> bool:
    """
    Compare the output with the golden output file.
    
    Args:
        output_dir: Path to the output directory
        update_golden: Whether to update the golden file
        
    Returns:
        True if the comparison was successful, False otherwise
    """
    output_dir = Path(output_dir)
    
    # Find the movies output file
    movies_files = list(output_dir.glob("movies_*.json"))
    if not movies_files:
        print("❌ No output files found for comparison!")
        return False
    
    movies_file = movies_files[0]
    golden_file = GOLDEN_OUTPUT_DIR / "movies_golden.json"
    
    if not golden_file.parent.exists():
        golden_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not golden_file.exists() and not update_golden:
        print("❌ Golden output file not found!")
        return False
    
    # Load current data
    try:
        current_data = load_json(movies_file)
    except Exception as e:
        print(f"❌ Error reading current output: {str(e)}")
        return False
    
    # Check if we have any data
    if len(current_data) == 0:
        print("❌ No items were scraped!")
        return False
    
    # Update golden file if requested
    if update_golden:
        try:
            # Copy the current output to the golden file
            shutil.copy(movies_file, golden_file)
            print(f"✅ Updated golden file: {golden_file}")
            return True
        except Exception as e:
            print(f"❌ Error updating golden file: {str(e)}")
            return False
    
    # Compare with existing golden file
    try:
        golden_data = load_json(golden_file)
    except Exception as e:
        print(f"❌ Error reading golden file: {str(e)}")
        return False
    
    # Compare the data
    if len(current_data) != len(golden_data):
        print(f"❌ Output size mismatch: {len(current_data)} items vs {len(golden_data)} in golden file")
        return False
    
    # Check if all required fields are present
    required_fields = ['title', 'year', 'director']
    for i, (current, golden) in enumerate(zip(current_data, golden_data)):
        for field in required_fields:
            if field not in current:
                print(f"❌ Missing required field '{field}' in item {i+1}")
                return False
            
            if current[field] != golden[field]:
                print(f"❌ Field '{field}' mismatch in item {i+1}: {current[field]} vs {golden[field]}")
                return False
    
    print("✅ Output matches golden file!")
    return True