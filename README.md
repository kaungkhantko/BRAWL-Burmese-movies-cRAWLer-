# Burmese Movies Catalogue Crawler 🎥

A smart, self-improving web crawler for building a structured catalogue of Burmese movies from various online sources.

Built with [Scrapy](https://scrapy.org/), [Selenium](https://www.selenium.dev/), and enhanced by [OpenAI](https://openai.com/) for intelligent content block selection.

---

## Project Purpose

This project was created as a **hobby learning initiative** to practice real-world **data engineering** and **software engineering** concepts.

Key learning goals include:
- Building scalable crawlers with dynamic page classification
- Managing structured data pipelines (JSON, logs, summaries)
- Integrating AI assistance for semi-structured content extraction
- Improving robustness, error handling, and crawl orchestration
- Learning how to ship maintainable scraping frameworks, not just one-off scripts

---

## Features

- **Catalogue and Detail Classification**  
  Dynamically distinguishes between catalogue pages and individual movie pages during crawl.

- **Dynamic Link Extraction**  
  Prioritizes and weights selectors intelligently to extract links, even from irregular page structures.

- **Auto-Fallback via OpenAI**  
  If no clear HTML structure is detected, the crawler uses OpenAI GPT to choose the best movie block.

- **Paginated Crawling**  
  Automatically follows "next page" links across catalogue listings.

- **Full Run Summaries**  
  After every crawl, detailed metadata including runtime, items scraped, warnings, and errors are saved.

- **Organized Output**  
  All outputs (movie data, logs, and run summaries) are timestamped and saved neatly inside `output/{timestamp}/`.

---

## Installation

```bash
git clone https://github.com/yourusername/burmese-movies-crawler.git
cd burmese-movies-crawler
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

You must also have **Google Chrome** and **chromedriver** installed and available in your PATH.

---

## Usage

First, activate your virtual environment:

```bash
source .venv/bin/activate
```

Then, start the crawler:

```bash
python run_spider.py
```

Upon running, the crawler will:

- Launch the Scrapy spider and Selenium headless browser
- Classify pages (catalogue or detail) dynamically
- Follow pagination links if available
- Save all outputs neatly into a timestamped folder (e.g., `output/2025-04-28_11-15-28/`), including:
  - `movies_{timestamp}.json` — structured movie metadata
  - `crawler_output_{timestamp}.log` — full crawl logs
  - `run_summary_{timestamp}.json` — summary stats of the crawl (items scraped, runtime, errors, etc.)

---

## Technologies Used

- Python 3.13
- Scrapy
- Selenium
- OpenAI API
- LXML, Parsel, HTTPX

---

## Lessons Learned

- **Web pages are messy**: Expect unpredictable HTML structures, broken links, missing data, and anti-bot measures.
- **Scrapy is extremely powerful**: But mastering its async nature, middlewares, and settings requires real-world practice.
- **Crawling ≠ Scraping**: Good crawlers focus heavily on *classification*, *navigation*, *retry logic*, not just pulling data.
- **Error handling matters**: Small crashes compound in crawlers. Proper try/except handling + warnings tracking = essential.
- **OpenAI integration is practical**: GPT models can assist in ambiguous scraping tasks (e.g., picking the right content block).
- **Run Summaries are underrated**: Generating a `run_summary.json` helps in diagnosing crawl quality without inspecting raw output manually.
- **Project structure matters**: Keeping `items.py`, `middlewares.py`, `settings.py`, and `spiders/` clean makes scaling easier later.
- **Virtual environments protect you**: Avoid polluting system Python. Treat `.venv` management seriously.
- **Scrapy + Selenium hybrid setups**: Allow flexible rendering, but come at a resource cost — balance headless browsing carefully.
- **Don't just scrape — engineer pipelines**: Treat crawled data as if you'll be shipping it into a database, ML system, or public API.

---

## License

This project is licensed under the MIT License.  
Feel free to use, modify, and distribute — attribution appreciated but not required.

---