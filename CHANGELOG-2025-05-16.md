# Changelog: May 16, 2025

## Summary

This changelog documents bug fixes and improvements made to the modular extraction system. Work was completed in collaboration with Amazon Q during a focused development session.

## Bug Fixes

### LinkExtractor

* Fixed URL validation to properly filter out base URLs and URLs ending with `/None`
* Improved handling of protocol-relative URLs (`//example.com/page`)
* Added proper validation for empty URLs and fragment-only links

### HeaderMapper

* Fixed caching mechanism to properly reuse cached header mappings
* Improved error handling during cache operations
* Added proper exception propagation as `TableProcessingError`

### MainFieldExtractor

* Enhanced extraction of nested tags using XPath selectors
* Added support for extracting text from elements with nested HTML structure
* Fixed handling of protocol-relative URLs in iframe sources

### ParagraphExtractor

* Fixed extraction of paragraphs with empty tags
* Improved text extraction from HTML paragraphs with nested elements
* Enhanced error handling for malformed paragraph content

### TableExtractor

* Fixed handling of tables without `<thead>` tags
* Improved empty cell handling to correctly map values to fields
* Fixed cell processing error handling to avoid recursion issues
* Added validation to ensure fields exist in item before assignment

### FieldMatcher

* Fixed multiple matches handling to correctly select the field with highest score
* Improved error handling to properly raise `ProcessingError`

### TextCleaner

* Fixed regex error handling to avoid issues with read-only regex pattern objects

### Integration Tests

* Updated tests to match actual URL format returned by extractors
* Fixed test expectations for protocol-relative URLs

## Other Improvements

* Added validation for year values in item schema (1800-2030)
* Fixed GitHub issue synchronization to handle missing fields gracefully
* Enhanced error handling throughout the codebase

## Benefits

* More robust extraction from various HTML structures
* Better handling of edge cases in web content
* Improved error reporting and logging
* More reliable test suite

---