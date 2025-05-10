# 📑 Burmese Movies Catalogue – Developer Documentation

## 📌 Scope

This document supports developers working on the **Burmese Movies Catalogue crawler** by outlining its validation pipeline, mock mode, and test strategy.

It complements the following key documents:

- [`README.md`](../README.md) — high-level project vision, features, usage
- [`architecture.md`](architecture.md) — current & future system design, diagrams, pain-points
- [`requirements_strategy_execution.md`](requirements_strategy_execution.md) — functional goals, constraints, KPIs

---

## 🧪 Pydantic-Based Validation

All scraped items are validated using **Pydantic** before being stored or exported.

### 📋 Key Validation Rules

- `title` is required and cannot be blank
- `year` must be <= current year + 5 years 
- `poster_url` and `streaming_link` must be valid URLs
- `cast` must be either a comma-separated string or list of strings
- `synopsis` must be ≤ 1000 characters
- Leading/trailing whitespace is stripped from all string fields

### 📁 Schema Location

- **Validation Logic**: `burmese_movies_crawler/schema/item_schema.py`

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
📝  Store
````

---

## 🧪 Testing

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
* `tests/` – Test files
* `output/` – Generated results from each run

---

## 🧭 What’s Not in This File

* Strategic rationale: see [`README.md`](../README.md)
* Architecture diagrams: see [`architecture.md`](architecture.md)
* System goals & KPIs: see [`requirements_strategy_execution.md`](requirements_strategy_execution.md)

---

## Next Steps (For this documentation file)

1. **Expand Validation Documentation**
   * Add examples of common validation errors and troubleshooting
   * Document custom validators and field transformers
   * Create validation rule reference table with rationale

2. **Enhance Mock Mode Guide**
   * Add step-by-step tutorial for creating new fixtures
   * Document fixture organization best practices
   * Include examples of fixture-based test cases

3. **Add Developer Workflow Section**
   * Local development setup instructions
   * Code contribution guidelines
   * PR review process

4. **Create Troubleshooting Guide**
   * Common extraction failures and solutions
   * Debugging validation pipeline issues
   * Performance optimization tips

5. **Add API Documentation**
   * Document crawler output formats (JSON, CSV)
   * Explain field normalization rules
   * Provide sample output schemas

6. **Include CI/CD Pipeline Documentation**
   * Test coverage requirements
   * Automated validation checks
   * Release process