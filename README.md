
# Burmese Movies Catalogue Crawler

A smart, self-improving web crawler for building a structured catalogue of Burmese movies from various online sources.

---

## Project Vision

Originally launched as a **learning project**, this crawler has grown into a modular framework aimed at:

* Cataloguing Burmese cinema across fragmented, low-structure sources
* Powering a searchable frontend with built-in analytics
* Scaling into a metadata aggregator for other domains (e.g., video games)

---

## Mission & Goals

The mission of this crawler is to build a **comprehensive, research-grade** catalogue of Burmese films, including feature films, TV series, documentaries, and short films. It is designed to:

* Serve both the **general public** and **academic researchers**
* Enable **dataset export** for downstream analytics
* Offer **API access and human validation workflows**
* Respect multilingual and script variations (Zawgyi/Unicode)

All fields are tagged with **source-level provenance**, and entries can start sparse (e.g., title-only) and be enriched later.

---

## Features

* **Dynamic Page Classification**: Automatically detects catalogue vs detail pages using rule-based scoring
* **Link Filtering + Retry Logic**: Skips invalid links (`javascript:`, fragments, etc.) and queues failed requests
* **Fuzzy Extraction**: Universal field matching with fallback logic (e.g., for noisy headers like "Directed by")
* **Paginated Crawling**: Handles multi-page catalogue sections
* **Field-Level Provenance**: Tracks which source each field was extracted from
* **Timestamped Output**: JSON results and logs saved by run

---

## Strategic Design Pillars

**Research-first**: Prioritizes accuracy and provenance for fields like awards, director, and year.

**Breadth-first**: Accepts incomplete entries (e.g., title only) and enriches them over time.

**Merge and Resolve**: Combines film data from multiple sources using fuzzy matching and trust logic.

**Mock Mode**: Fully supports offline development using saved HTML fixtures.

**Retry Logic**: Failed URLs are retried in future runs for higher long-term coverage.

**Editor Enrichment**: Supports external interfaces for humans to validate and update metadata.

---

## Installation

```bash
git clone https://github.com/kaungkhantko/BRAWL-Burmese-movies-cRAWLer-
cd BRAWL-Burmese-movies-cRAWLer-
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

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

### Output Files

* `movies_*.json`: structured film data
* `run_summary_*.json`: crawl statistics
* `crawler_output_*.log`: runtime logs
* `invalid_links_*.json`: skipped URLs with reasons

---

## Further Reading

* [`Internal structure and modules`](docs/architecture.md)
* [`Full requirements + strategy map`](docs/requirements_strategy_execution.md)
* [` Documentation for developers`](docs/documentation.md)

---

## License

MIT — free to use, remix, or build upon.

---

> Built solo as an educational, ethical, and technical exploration of how to preserve and promote Burmese film metadata at scale.

