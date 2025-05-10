# 📚 BRAWL Web Crawler – Requirements & Execution Strategy

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

| **Strategy**                  | **Implication** | **Implementation Summary**                               | **Acceptance Criteria** | **KPIs**                                              |
| ----------------------------- | --------------- | -------------------------------------------------------- | ----------------------- | ----------------------------------------------------- |
| **Research-first accuracy**   | Focus on canonical data (e.g., awards, verified credits) | Use authoritative sources; enable human validation loop | • Collect data from trusted sources (IMDb, TMDb, Wikipedia)<br>• Field-level provenance must be present<br>• Editorial review exists for high-value fields | • metadata_certified_rate: % of entries with award/certified data<br>• editorial_review_coverage: % of high-confidence entries reviewed |
| **Breadth over depth**        | Crawl more films, even with minimal metadata | Accept sparse entries and flag for enrichment | • Accept entries with only a title<br>• Flag incomplete entries for enrichment pipeline | • weekly_title_only_additions: # of title-only entries/week<br>• enrichment_uplift_rate: % of partial entries upgraded monthly |
| **Provenance per field**      | Store origin for each metadata field independently | Include source tag alongside each field in DB/JSON | • Field-level provenance shown in exports and editorial UI | • provenance_tag_coverage: % of fields with valid source tags<br>• avg_sources_per_film: Average unique sources per film |
| **Free domain crawling**      | Flexible, deep crawling of sites | Allow all internal links unless explicitly blacklisted | • Crawler respects domain boundary but explores freely inside | • domain_crawl_success_rate: % of pages fetched successfully<br>• crawl_depth_median: Median link depth |
| **Selective JS rendering**    | Conserve compute; only render when needed | Use Selenium selectively via domain allowlist | • Rendering turned on only for specific domains | • selenium_render_ratio: % of pages requiring JS rendering<br>• avg_render_time: Seconds per JS-rendered page |
| **Multi-source merging**      | Single record per film with unified metadata | Use fuzzy logic to merge fields by priority | • Records with same title/year merged<br>• Conflicts resolved using trust score or source priority | • merged_entry_rate: % of entries with fields from multiple sources<br>• avg_fields_per_merged_entry: Fields per enriched record |
| **"Title-only" records**      | Do not reject sparse data | Store minimal entries and mark for enrichment | • Entries with only `title` are stored with `enrichment_needed: true` | • title_only_ratio: % of new entries that are title-only<br>• enrichment_backlog_size: # of entries needing enrichment |
| **End-to-end mock mode**      | End-to-end testing offline | Run parse → extract → store using saved HTML | • MOCK_MODE executes full flow with local fixtures | • mock_pipeline_pass_rate: % of mock tests passing<br>• fixture_coverage: % of unit tests using mock HTML |
| **Retry queues for failures** | Increase resilience and success rate | Store failed URLs with retry metadata | • Failed crawls added to retry queue<br>• Max retry attempts enforced | • retry_success_rate: % of failed pages recovered after retries<br>• avg_retry_delay: Avg. delay before retrying |
| **Editor enrichment support** | Manual review and correction pipeline | Admin tool or interface for external users | • External UI supports editing key metadata | • avg_editor_time: Minutes per enriched record<br>• weekly_records_edited: # of edited records per week |
| **Modular field sets by domain** | Prepare for multi-domain expansion (games, tech stacks) | Field schemas per content type (film/game/tech) | • Schema is modular and domain-aware | • schema_coverage_rate: % of valid fields covered by schema<br>• parse_error_rate: % of entries failing schema validation |
| **Backend-first API**         | Focus on internal workflows with optional external integration | Build flexible backend; expose GET/PATCH via REST | • REST API exposes film lookup and update routes<br>• Auto-generated OpenAPI docs post-stabilization | • api_uptime: % availability of public/private API<br>• film_lookup_response_time: Avg. ms for GET /film/:id |

---

## 🧩 Next Steps

* Build and test mock-mode pipelines
* Set up retry queue and enrichment flag logic
* Draft schema registry and modular field extractors
* Begin scaffolding lightweight API layer with FastAPI or Flask

---