"""
Centralized exception definitions for the extraction system.
"""
from typing import Optional


class FieldExtractorError(Exception):
    """Base exception for all extraction-related errors."""
    pass


class InitializationError(FieldExtractorError):
    """Error during initialization of extraction components."""
    pass


class ExtractionError(FieldExtractorError):
    """Error during data extraction from responses."""
    pass


class ProcessingError(FieldExtractorError):
    """Error during data processing or transformation."""
    pass


class TableProcessingError(FieldExtractorError):
    """Error during table extraction or processing."""
    pass