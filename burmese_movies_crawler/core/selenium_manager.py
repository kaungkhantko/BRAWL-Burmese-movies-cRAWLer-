"""
Selenium manager for the Burmese Movies Crawler.

This module provides functionality for managing Selenium WebDriver instances.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class SeleniumManager:
    """
    Context manager for Selenium WebDriver instances.
    """
    
    def __init__(self):
        """Initialize the Selenium manager."""
        self.opts = Options()
        self.opts.add_argument("--headless")
        self.opts.add_argument("--disable-gpu")
        self.opts.add_argument("--no-sandbox")
        self.opts.add_argument("--disable-dev-shm-usage")
        self.driver = None

    def __enter__(self):
        """
        Start the WebDriver.
        
        Returns:
            The WebDriver instance
        """
        self.driver = webdriver.Chrome(options=self.opts)
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Clean up the WebDriver.
        
        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        if self.driver:
            self.driver.quit()