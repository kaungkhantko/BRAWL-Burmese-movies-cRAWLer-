# Burmese Movies Catalogue – Architecture Overview

## Purpose

The Burmese Movies Catalogue is a modular, extensible web crawling platform that collects, normalizes, and enriches metadata on Burmese cinema — including films that are:
- In Burmese language,
- Directed by Burmese filmmakers,
- Feature Burmese cast, or
- Shot in Myanmar.

It is designed to evolve into a broader **metadata aggregation and analytics system** that includes other verticals such as **video games**, while supporting a **searchable frontend** and **built-in analytics** dashboard.

---

## Architecture Layers

### 1. **Crawler Engine**
- Built with Scrapy and Selenium (headless Chrome)
- Periodic runs with retry logic and resumption support
- Accuracy-focused over speed; scalable to parallelization
- Logs failed attempts and invalid links

### 2. **Link & Structure Classifier**
- Uses heuristics and fuzzy logic to:
  - Filter invalid links
  - Distinguish between catalogue, detail, and unknown pages
  - Score catalogue likelihood using modular rule sets

### 3. **Field Extractor**
- Applies universal selectors across domains
- Uses `fuzzywuzzy` to associate HTML snippets with fields like:
  - Title
  - Genre
  - Synopsis
  - Director
- Supports OpenAI-assisted fallback parsing (via `openai_selector.py`)

### 4. **Site Profiles**
- Maintains evolving per-domain behavior
- Centralized control with future override system
- Supports differences in site layout and quality

### 5. **Output Layer**
- Outputs JSON with UTF-8 encoding
- Tracks source provenance (field → URL → selector)
- Run summaries include scrape count, duration, and error/warning logs

### 6. **Analytics & Frontend** *(Planned)*
- Searchable frontend powered by metadata
- Built-in dashboards for field completeness, tag frequency, and trend analysis
- Cloud-hosted dashboard in the future

---

## Data Flow

```text
[Start URLs]
     ↓
[Crawler Engine] → [Retry / Resume Manager]
     ↓
[Page Type Classifier]
     ↓
  ┌────────────┐
  │ Catalogue? │─────→ [Extract Links → Follow]
  └─────┬──────┘
        ↓
  [Detail Page?]
        ↓
[Field Extractor + Provenance Tracker]
        ↓
[Output JSON + Summary Log]
````

---

## Design Principles

* **Centralized logic, modular inputs**: One crawler, many sites.
* **Flexible schema**: Output adapts to what is extractable.
* **Source-aware**: Each data point carries where it came from.
* **Extensible foundation**: Future-proofed for new verticals and analytics.
* **Retry-resilient**: Can resume partial scrapes and retry failing URLs.

---

## Future Enhancements

* [ ] Parallelized crawl orchestration
* [ ] Schema drift detection (site layout changes)
* [ ] Dynamic throttling / rate control
* [ ] OpenAI-based labelers or normalizers
* [ ] Cloud deployment + scheduling (e.g., GitHub Actions, Airflow, or Lambda)
* [ ] Frontend filtering + faceted search (e.g., genre, year, director)

---

## Author

Built and maintained by a solo developer dedicated to ethical, inclusive technology that preserves and promotes Burmese creative work.
