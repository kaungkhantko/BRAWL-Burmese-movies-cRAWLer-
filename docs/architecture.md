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

## 📐 Data Validation

To ensure consistent and high-quality data throughout the scraping pipeline, the project uses **Pydantic-based validation** before any item is persisted or exported.

## ✅ Implementation

* The schema is defined in [`burmese_movies_crawler/schema/item_schema.py`](../burmese_movies_crawler/schema/item_schema.py).
* Validation is performed in the item pipeline (`BurmeseMoviesPipeline`) using the Pydantic `MovieItem` model.
* Invalid items are automatically dropped and logged with a warning message.
* The `MovieItem` schema enforces:

  * Non-empty `title` and `director` fields
  * Reasonable `year` bounds (1900–2100)
  * Optional `cast` field that supports both comma-separated strings and cleaned lists
  * Auto-stripping of whitespace in strings and list elements
  * Rejection of overly long `synopsis` entries (max 1000 characters)
  * Validation of proper URL formats for `poster_url` and `streaming_link`

### 🧪 Testing

* Validation logic is tested under `tests/unit/test_item_schema.py` using `pytest`.
* Edge cases are included, such as:

  * Empty or whitespace-only fields
  * Malformed URLs
  * Unexpected formats in `cast` and `synopsis`

---

### Validation FLow


🕷️  Crawl (Scrapy Spider)
      |
      v
🧱  Parse HTML Content
      |
      v
📦  Build Scrapy Item (BurmeseMoviesItem)
      |
      v
✅  Pydantic Validation (MovieItem Schema)
    ├─ Valid → Pass to Pipeline
    └─ Invalid → Drop & Log Warning
      |
      v
🧹  Transform / Normalize (optional enrichments)
      |
      v
📝  Store in JSON / Database / Export Format


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
