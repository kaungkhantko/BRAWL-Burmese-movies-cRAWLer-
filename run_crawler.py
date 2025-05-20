#!/usr/bin/env python3
"""
Main entry point for running the Burmese Movies Crawler.

This script provides a unified interface for running the crawler in both normal and mock modes.
"""

import os
import argparse
import subprocess
import time
from datetime import datetime
from threading import Timer
from pathlib import Path

from burmese_movies_crawler.config import DEFAULT_TIMEOUT, get_timestamp
from burmese_movies_crawler.core.io_utils import setup_output_paths, print_run_summary, compare_with_golden
from burmese_movies_crawler.core.process_utils import run_with_timeout


def get_scrapy_path() -> str:
    """
    Get the path to the scrapy executable.
    
    Returns:
        Path to the scrapy executable
    """
    # Use the full path to scrapy in the virtual environment
    return os.path.join(os.getcwd(), ".venv", "bin", "scrapy")


def build_scrapy_command(output_paths, timeout, spider_name="movies", extra_args=None):
    """
    Build the scrapy command.
    
    Args:
        output_paths: Dictionary containing output paths
        timeout: Timeout in seconds
        spider_name: Name of the spider to run
        extra_args: Extra arguments to pass to scrapy
        
    Returns:
        List of command arguments
    """
    scrapy_path = get_scrapy_path()
    
    # Command with full path to scrapy
    command = [
        scrapy_path, "crawl", spider_name,
        "-s", f"LOG_FILE={output_paths['log_file']}",
        # Add CLOSESPIDER_TIMEOUT setting (as a backup)
        "-s", f"CLOSESPIDER_TIMEOUT={timeout - 5}",
    ]
    
    # Add extra arguments if provided
    if extra_args:
        command.extend(extra_args)
        
    return command


def main():
    """Main entry point for running the crawler."""
    parser = argparse.ArgumentParser(description='Run the Burmese Movies Crawler')
    parser.add_argument('--mock', action='store_true', help='Run in mock mode')
    parser.add_argument('--fixture', help='Specify a fixture to use for the first URL (only in mock mode)')
    parser.add_argument('--compare-golden', action='store_true', help='Compare output with golden file (only in mock mode)')
    parser.add_argument('--update-golden', action='store_true', help='Update the golden file with current output (only in mock mode)')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT, help=f'Timeout in seconds (default: {DEFAULT_TIMEOUT})')
    args = parser.parse_args()
    
    # Set environment variables
    if args.mock:
        os.environ["MOCK_MODE"] = "true"
        
        # Set fixture if provided
        if args.fixture:
            os.environ["MOCK_FIXTURE"] = args.fixture
    
    # Setup output paths
    timestamp = get_timestamp()
    os.environ["SCRAPY_RUN_TIMESTAMP"] = timestamp
    output_paths = setup_output_paths(timestamp)
    
    # Build extra args for scrapy
    extra_args = []
    if args.mock and args.fixture:
        extra_args.extend(["-a", f"fixture={args.fixture}"])
    
    # Build and run the command
    command = build_scrapy_command(
        output_paths=output_paths,
        timeout=args.timeout,
        extra_args=extra_args
    )
    
    # Print info
    mode_str = "MOCK MODE" if args.mock else "normal mode"
    print(f"Running crawler in {mode_str} with {args.timeout} second timeout...")
    print(f"Output will be saved to {output_paths['output_dir']}")
    
    # Run the command
    run_with_timeout(command, timeout_seconds=args.timeout)
    
    print("Crawler finished.")
    
    # Print summary and compare with golden file if in mock mode
    if args.mock:
        print_run_summary(output_paths["output_dir"])
        
        if args.compare_golden or args.update_golden:
            compare_with_golden(output_paths["output_dir"], update_golden=args.update_golden)


if __name__ == "__main__":
    main()