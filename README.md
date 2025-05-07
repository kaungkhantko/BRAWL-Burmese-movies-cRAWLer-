# Burmese Movies Catalogue Crawler 🎥

A smart, self-improving web crawler for building a structured catalogue of Burmese movies from various online sources.

Built with [Scrapy](https://scrapy.org/), [Selenium](https://www.selenium.dev/), and enhanced by [OpenAI](https://openai.com/) for intelligent content block selection.

---

## 🧠 Project Vision

Originally launched as a **learning project**, this crawler has grown into a modular framework aimed at:
- Cataloguing Burmese cinema across fragmented, low-structure sources
- Powering a searchable frontend with built-in analytics
- Scaling into a metadata aggregator for other domains (e.g., video games)

See [`docs/documentation.md`](docs/documentation.md) for an in-depth breakdown of components and design decisions.

---

## ⚙️ Features

- **Dynamic Page Classification**: Automatically detects catalogue vs detail pages using rule-based scoring.
- **Link Filtering + Retry Logic**: Skips invalid links (`javascript:`, fragments, etc.) and retries failed requests.
- **Fuzzy Extraction**: Extracts movie data using fuzzy logic and universal selectors — no site-specific hardcoding.
- **OpenAI Fallbacks**: GPT-powered selection helps extract ambiguous or semi-structured blocks.
- **Paginated Crawling**: Follows next-page links when available.
- **Field Provenance**: Tracks where each piece of data was extracted from.
- **Timestamped Output**: Organized crawl outputs (`JSON`, `log`, `summary`) in per-run folders.

---

## 🚀 Installation

```bash
git clone https://github.com/yourusername/burmese-movies-crawler.git
cd burmese-movies-crawler
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
````

---

## 🕹 Usage

```bash
source .venv/bin/activate
python run_spider.py
```

The crawler will:

* Classify page types
* Extract and follow valid links
* Scrape and enrich movie fields
* Save all outputs to `output/{timestamp}/`

Output includes:

* `movies_*.json`: structured data
* `run_summary_*.json`: runtime stats
* `crawler_output_*.log`: logging output
* `invalid_links_*.json`: skipped URLs with reasons

---

## 💡 Lessons Learnt

* Writing resilient crawlers, not just scrapers
* Handling malformed, inconsistent HTML at scale
* Modularizing extraction logic for reuse
* Using OpenAI to augment crawling
* Designing data pipelines with summary/logging layers
* Building towards analytics-ready, source-aware datasets

---

## 📘 Further Reading

* [docs/architecture.md](docs/architecture.md): Internal structure, data flow, planned extensions
* `tests/`: Growing test suite for validation and classification logic

---

## 📝 License

MIT — free to use, remix, or build upon.

---

> Built solo as an educational, ethical, and technical exploration of how to preserve and promote Burmese film metadata at scale.