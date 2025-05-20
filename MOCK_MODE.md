# Mock Mode Documentation

## Overview

Mock mode allows you to run the spider using local HTML fixtures instead of making live HTTP requests. This is useful for:

- Testing extraction logic
- Developing new features without hitting real websites
- Regression testing against known-good outputs
- Continuous integration testing

## How to Use Mock Mode

### Basic Usage

```bash
# Run the spider in mock mode
python run_mock.py
```

### Advanced Options

```bash
# Use a specific fixture for the first URL
python run_mock.py --fixture channelmyanmar_to_movies_81376cf1.html

# Compare output with golden file
python run_mock.py --compare-golden

# Update the golden file with current output
python run_mock.py --update-golden

# Set a custom timeout (default: 90 seconds)
python run_mock.py --timeout 60
```

## How Mock Mode Works

When you run the spider in mock mode:

1. The `MOCK_MODE=true` environment variable is set
2. All HTTP requests are intercepted in the `get_response_or_request()` function
3. Instead of making real HTTP requests, the spider loads local HTML fixtures
4. A mapping file (`fixture_mapping.json`) is used to match URLs to fixture files
5. The spider processes these fixtures as if they were real HTTP responses

## Adding New Fixtures

### Step 1: Create the HTML Fixture

Create an HTML file in the `tests/fixtures/` directory with a descriptive name following the convention:

```
domain_path_uniquehash.html
```

For example:
- `channelmyanmar_to_movies_81376cf1.html`
- `wikipedia_org_List_of_Burmese_films_a637815.html`

### Step 2: Update the Fixture Mapping

Update the `tests/fixtures/fixture_mapping.json` file to map URLs to your fixture names:

```json
{
  "https://www.channelmyanmar.to/movies/": "channelmyanmar_to_movies_81376cf1.html",
  "https://www.channelmyanmar.to/movies/the-golden-land": "mock_detail_page.html"
}
```

### Step 3: Test Your Fixture

Run the spider with your new fixture:

```bash
python run_mock.py --fixture your_new_fixture.html
```

## Adding Edge-Case Fixtures

Edge cases are important to test the robustness of your spider. The project includes several edge-case fixtures:

### Empty Catalogue

`empty_catalogue_fixture.html` - A page with no movies to test how the spider handles empty results.

```bash
python run_mock.py --fixture empty_catalogue_fixture.html
```

### Malformed HTML

`malformed_html_fixture.html` - A page with broken HTML to test the spider's error handling.

```bash
python run_mock.py --fixture malformed_html_fixture.html
```

### Multilingual/Unicode Content

`multilingual_unicode_fixture.html` - A page with Burmese Unicode characters to test internationalization.

```bash
python run_mock.py --fixture multilingual_unicode_fixture.html
```

### Creating Your Own Edge Cases

1. Identify a specific edge case you want to test
2. Create a fixture that represents this edge case
3. Add it to the fixture mapping
4. Run the spider with your fixture to verify behavior

## Reusing Fixtures Across Test Files

Fixtures can be reused across different test files:

### In Python Tests

```python
# Import the fixture path
from pathlib import Path

# Reference the fixture
fixture_path = Path("tests/fixtures/your_fixture.html")

# Load the fixture content
with open(fixture_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Use the fixture in your test
# ...
```

### In Command-Line Tests

```bash
# Run the spider with a specific fixture
python run_mock.py --fixture your_fixture.html

# Run a test script with a specific fixture
python your_test_script.py --fixture your_fixture.html
```

### In CI/CD Pipelines

```yaml
# Example GitHub Actions workflow
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.x'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests with fixtures
        run: |
          python run_mock.py --fixture channelmyanmar_to_movies_81376cf1.html --compare-golden
```

## Golden File Testing

Golden file testing allows you to compare the output of the spider against a known-good "golden" output file. This is useful for regression testing.

### Creating a Golden File

```bash
# Run the spider and update the golden file
python run_mock.py --update-golden
```

This will create or update the file at `tests/fixtures/golden_output/movies_golden.json`.

### Comparing with the Golden File

```bash
# Run the spider and compare with the golden file
python run_mock.py --compare-golden
```

If the output doesn't match the golden file, the test will fail.

## Automated Testing

The project includes automated tests for mock mode in `tests/test_spider_mock.py`. These tests verify:

- The spider runs successfully in mock mode
- The spider can use specific fixtures
- The output matches the expected golden output
- The spider handles edge cases correctly
- Data validation using Pydantic schemas

Run the tests with:

```bash
python -m unittest tests/test_spider_mock.py
```

## Troubleshooting

### Missing Fixtures

If you see an error like:

```
[MOCK_MODE] Fixture not found for https://example.com (tests/fixtures/abcdef1234.html)
```

You need to create the fixture file or update the fixture mapping.

### Output Doesn't Match Golden File

If the output doesn't match the golden file, check:

1. The fixture content matches what you expect
2. The extraction logic is working correctly
3. The golden file contains the expected output

### No Items Scraped

If no items are scraped, check:

1. The fixture contains the expected data
2. The spider's extraction logic can handle the fixture format
3. The page classifier is correctly identifying the page type

## Best Practices

1. Use descriptive names for fixtures
2. Keep fixtures small and focused
3. Update the golden file when you intentionally change the extraction logic
4. Add tests for new fixtures
5. Use mock mode during development to iterate quickly
6. Include edge cases in your test suite
7. Validate output data using schemas