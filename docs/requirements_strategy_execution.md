# 📚 BRAWL Web Crawler – Business Requirements & Execution Strategy

This document outlines the **functional goals**, **data constraints**, **strategic priorities**, and **operational expectations** for the BRAWL Web Crawler project, designed to power the **Burmese Movies Catalogue** — a searchable and research-oriented film metadata platform.

---

## 🧭 Project Overview

* **Project Name**: Burmese Movies Catalogue
* **Version**: 1.1
* **Owner**: Kaung Khant Ko
* **Last Updated**: 2025-05-08

### 🎯 Mission

To create a **comprehensive and searchable catalogue of Burmese films**, including feature films, documentaries, and series, to **support academic research** and **promote the Burmese film industry**.

---

## 👥 Intended Users & Outcomes

### Primary Users:

* General Public
* Researchers and Scholars
* Internal Analytics and Reporting Teams

### Key Outcomes:

* Searchable metadata catalogue of Burmese-related audiovisual works
* Exportable dataset for academic research
* Future-proofed API integration
* Human validation and enrichment workflow for data integrity

---

## 🎬 Content Scope

### Included Media Types:

* Feature Films
* Documentaries
* TV Series
* Short Films

### Excluded:

* User-generated content (e.g., YouTube clips, TikToks)

### Inclusion Criteria:

* Language: Burmese, Zawgyi, or Unicode Mixed
* Origin: Myanmar productions, co-productions, or significant Burmese creative involvement
* Cast/Director: Must include at least one Burmese national

### Field Requirements:

* **Required**: `title`
* **Optional**: year, director, cast, genre, synopsis, poster URL, awards, reviews, production company, runtime, language, subtitles, country, related links

**Note**: Entries with only a title are accepted but must be flagged for future enrichment. All fields must store their **individual source provenance**.

---

## 🔍 Source Strategy

### Discovery Methods:

* Curated Source List
* Automated Link Discovery (within domain boundaries)

### Initial Source Pool:

* IMDb, TMDb, Wikipedia
* Burmese film databases
* Wathan Film Festival, Asian Film Archive

### Supported Source Types:

* Streaming sites
* News portals
* Wiki-style directories
* Blogspot / WordPress pages
* Social media (Facebook, Instagram)
* Film awards and festival listings
* Professional film associations

### Technical Support:

* Multilingual text handling
* Unicode normalization (Zawgyi/Unicode aware)

---

## 🕸 Crawl Strategy

* Weekly refresh cycles
* Max 500 pages per domain
* Scale target: 50,000+ pages
* Domain-specific JS rendering via Selenium (only when needed)
* Deep link-following allowed within domain boundaries
* Deduplication and crawl resume functionality
* `MOCK_MODE` flag for full offline testing
* Merging logic for multi-source film entries

---

## ✅ Data Validation & Enrichment

* Prioritize accuracy over completeness
* Allow partial records
* Each field must include a source tag
* Human review loop required for high-impact fields
* Retry queues for failed crawls
* Editor-facing tools to enable metadata enrichment and correction

---

## 🛡 Compliance

* Respects `robots.txt`
* No exemptions for blocked domains
* Posters and images must be copyright-safe
* Custom user-agent: `BRAWL-Crawler (+contact_url)`

---

## 🔁 Extensibility & Future-Proofing

### Future Expansion:

* Game metadata cataloguing
* Tech stack profiling (e.g., StackShare scraping)
* Cross-referencing with IMDb/TMDb datasets

### Downstream Features:

* Search frontend
* Recommendation engine
* Trend analytics dashboard

### Schema Design:

* Modular field sets per domain (e.g., `film_fields`, `game_fields`)

---

## 🚀 Deployment & API Strategy

### Environments:

* Development: Localhost (with mock mode)
* Production: Cloud or VPS environment

### Job Scheduling:

* Cron-based for now
* Kubernetes batch job support (future)

### API Strategy:

* Backend-first, REST API with optional PATCH endpoints
* Designed to support OpenAPI spec and editing UI

---

## 📊 Strategy Alignment Map (Execution Overview)

| **Strategy**                  | **Implementation Summary**                               | **KPIs**                                              |
| ----------------------------- | -------------------------------------------------------- | ----------------------------------------------------- |
| **Research-first accuracy**   | Use authoritative sources, editorial validation          | ≥ 30% award-tagged entries, 100% key fields reviewed  |
| **Breadth over depth**        | Accept sparse data; enrich later                         | ≤ 60% title-only entries, ≥ 20% upgraded monthly      |
| **Provenance per field**      | Source stored per field in DB/JSON                       | ≥ 95% provenance coverage, ≥ 2 sources per film       |
| **Free domain crawling**      | No link restrictions within a domain                     | ≥ 90% crawl success, median depth 3–5                 |
| **Selective JS rendering**    | Render only on whitelisted domains                       | ≤ 10% of pages rendered, < 8s render time             |
| **Multi-source merging**      | Combine entries using fuzzy logic and trust weighting    | ≥ 50% merged, ≥ 6 fields per enriched record          |
| **“Title-only” records**      | Allow minimal records; flag for enrichment               | Backlog < 1,000, `enrichment_needed: true` for all    |
| **End-to-end mock mode**      | Full pipeline works with local HTML fixtures             | 100% mock test pass rate, ≥ 80% fixture test coverage |
| **Retry queue for failures**  | Store retry metadata, reattempt later                    | ≥ 70% retry recovery, < 48h retry lag                 |
| **Editorial tools support**   | Admin UI for reviewing and editing metadata              | < 3 min avg. edit time, ≥ 100 entries/week edited     |
| **Modular schemas by domain** | Maintain separate but interoperable field sets           | ≥ 90% schema coverage, < 2% validation error rate     |
| **Backend-first API**         | Lightweight REST layer + OpenAPI docs + editor interface | 99.5% uptime, < 300ms lookup latency                  |

---

## 🧩 Next Steps

* Build and test mock-mode pipelines
* Set up retry queue and enrichment flag logic
* Draft schema registry and modular field extractors
* Begin scaffolding lightweight API layer with FastAPI or Flask

---