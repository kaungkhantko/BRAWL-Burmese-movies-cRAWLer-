# # burmese_movies_crawler/utils/selenium_manager.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class SeleniumManager:
    def __init__(self):
        self.opts = Options()
        self.opts.add_argument("--headless")
        self.opts.add_argument("--disable-gpu")
        self.opts.add_argument("--no-sandbox")
        self.opts.add_argument("--disable-dev-shm-usage")
        self.driver = None

    def __enter__(self):
        self.driver = webdriver.Chrome(options=self.opts)
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()
