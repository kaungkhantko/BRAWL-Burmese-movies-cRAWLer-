# BRAWL - Burmese Movies Crawler

A web crawler for Burmese movies information.

## Overview

BRAWL (Burmese movies cRAWLer) is a specialized web crawler built with Scrapy to extract information about Burmese movies from various online sources.

## Features

- Extracts movie details including title, year, director, cast, and more
- Supports both normal and mock modes for testing
- Handles different page types (catalogues and detail pages)
- Provides detailed run summaries and logs

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/BRAWL-Burmese-movies-cRAWLer-.git
   cd BRAWL-Burmese-movies-cRAWLer-
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

## Usage

### Running the Crawler

To run the crawler in normal mode:
```
python run_crawler.py
```

To run the crawler in mock mode:
```
python run_crawler.py --mock
```

### Command Line Options

- `--mock`: Run in mock mode using fixtures instead of making real HTTP requests
- `--fixture FIXTURE`: Specify a fixture to use for the first URL (only in mock mode)
- `--compare-golden`: Compare output with golden file (only in mock mode)
- `--update-golden`: Update the golden file with current output (only in mock mode)
- `--timeout SECONDS`: Set the timeout in seconds (default: 90)

## Project Structure

```
burmese_movies_crawler/
├── core/                   # Core functionality
│   ├── io_utils.py         # I/O utilities
│   ├── link_utils.py       # Link handling utilities
│   ├── mock_utils.py       # Mock mode utilities
│   ├── orchestrator.py     # Page processing orchestrator
│   ├── page_classifier.py  # Page classification
│   ├── process_utils.py    # Process handling utilities
│   └── selenium_manager.py # Selenium WebDriver management
├── extractors/             # Data extraction modules
├── resources/              # Resource files
├── schema/                 # Data schemas
├── spiders/                # Scrapy spiders
└── utils/                  # Utility modules
tests/
├── fixtures/               # Test fixtures
├── integrated/             # Integration tests
└── unit/                   # Unit tests
```

## Testing

Run the tests with:
```
pytest
```

## Mock Mode

Mock mode allows running the crawler without making real HTTP requests. It uses pre-recorded HTML fixtures instead. This is useful for testing and development.

To learn more about mock mode, see [MOCK_MODE.md](MOCK_MODE.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.