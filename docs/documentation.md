````markdown
# 📑 Burmese Movies Catalogue – Developer Documentation

## 📌 Scope

This document supports developers working on the **Burmese Movies Catalogue crawler** by outlining its validation pipeline, mock mode, and test strategy.

It complements the following key documents:

- [`README.md`](../README.md) — high-level project vision, features, usage
- [`architecture.md`](architecture.md) — current & future system design, diagrams, pain-points
- [`business_requirements.yaml`](business_requirements.yaml) — functional goals, constraints, KPIs

---

## 🧪 Pydantic-Based Validation

All scraped items are validated using **Pydantic** before being stored or exported.

### 📋 Key Validation Rules

- `title` is required and cannot be blank
- `year` must fall between 1900 and 2100
- `poster_url` and `streaming_link` must be valid URLs
- `cast` must be either a comma-separated string or list of strings
- `synopsis` must be ≤ 1000 characters
- Leading/trailing whitespace is stripped from all string fields

### 📁 Schema Location

- **Definition**: `burmese_movies_crawler/schema/item_schema.py`
- **Validation Logic**: `burmese_movies_crawler/pipelines/burmese_pipeline.py`

---

## 🧪 Validation Flow Summary

```text
🕷️  Crawl (Scrapy Spider)
      ↓
🧱  Parse HTML Content
      ↓
📦  Build Scrapy Item (BurmeseMoviesItem)
      ↓
✅  Pydantic Validation (MovieItem Schema)
    ├─ Valid → Pass to Pipeline
    └─ Invalid → Drop & Log Warning
      ↓
🧹  Transform / Normalize (optional enrichments)
      ↓
📝  Store in JSON / Database / Export Format
````

---

## 🧪 Unit Testing Coverage

Validation logic is tested under:

```text
tests/unit/test_item_schema.py
```

Includes edge case tests for:

* Empty or malformed fields
* Invalid URLs
* Incorrect data types
* Unicode normalization

Run tests with:

```bash
pytest tests/
```

---

## 🧪 Mock Mode (Offline Testing)

Mock Mode allows you to run the crawler entirely offline, simulating real runs using saved HTML files.

### 💡 Why Use It?

* Enables deterministic testing without network/Selenium
* CI-friendly and lightweight
* Useful for debugging extraction and selectors

### ▶️ How to Enable

```bash
MOCK_MODE=true python run_spider.py
```

### 📁 How It Works

* Replaces all network/Selenium requests with local files
* Matches saved HTML fixtures based on MD5 hash of original URL

### 🏷 Fixture Naming Convention

```python
import hashlib
print(hashlib.md5("https://example.com".encode()).hexdigest())
```

Save the corresponding file as:

```text
tests/fixtures/<md5_hash>.html
```

---

## 🔁 Related Files

* `run_spider.py` – Entry point for the crawler
* `tests/fixtures/` – Directory for local HTML test pages
* `tests/unit/` – Pytest unit tests for schema and parsing
* `output/` – Generated results from each run

---

## 🧭 What’s Not in This File

* Strategic rationale: see [`README.md`](../README.md)
* Architecture diagrams: see [`architecture.md`](architecture.md)
* System goals & KPIs: see [`requirements_strategy_execution.md`](requirements_strategy_execution.md)

---
