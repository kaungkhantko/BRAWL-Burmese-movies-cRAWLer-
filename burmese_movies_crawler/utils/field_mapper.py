"""
Field mapping utilities for data extraction.
"""
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

from burmese_movies_crawler.utils.exceptions import InitializationError

logger = logging.getLogger(__name__)

# Default confidence threshold
DEFAULT_THRESHOLD = 70


def load_field_mapping(content_type: str = "movies") -> dict:
    """
    Load field mapping for a given content type from the YAML config.

    Args:
        content_type: The content type to load mappings for (e.g., "movies", "games")

    Returns:
        Dictionary of field mappings for the specified content type

    Raises:
        ValueError: If the content type is not found in the mappings
    """
    # Path to the YAML file (relative to this file's location)
    path = Path(__file__).parent.parent / "resources" / "field_mapping.yaml"

    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    all_mappings = config.get("content_types", {})
    if content_type not in all_mappings:
        raise ValueError(f"Unknown content_type '{content_type}'. Available types: {list(all_mappings.keys())}")

    return all_mappings[content_type]


class FieldMapper:
    """
    Loads and provides access to field mappings with labels and thresholds.
    """
    
    def __init__(self, content_type: str = "movies"):
        """
        Initialize the field mapper with mappings for the specified content type.
        
        Args:
            content_type: The type of content to load mappings for (default: "movies")
            
        Raises:
            InitializationError: If field mappings cannot be loaded
        """
        try:
            # Load field mappings with error handling
            self.label_mapping = load_field_mapping(content_type)
            
            # Pre-compute field patterns for faster matching
            self._field_patterns = {}
            for field, meta in self.label_mapping.items():
                if not isinstance(meta, dict) or 'labels' not in meta:
                    logger.warning(f"Invalid field mapping for {field}, skipping")
                    continue
                    
                self._field_patterns[field] = {
                    'labels': meta['labels'],
                    'threshold': meta.get('confidence_threshold', DEFAULT_THRESHOLD)
                }
                
            if not self._field_patterns:
                logger.warning("No valid field patterns found")
                
        except Exception as e:
            logger.error(f"Failed to load field mapping for {content_type}: {str(e)}")
            raise InitializationError(f"Failed to load field mapping: {str(e)}") from e
    
    def get_labels_for(self, field: str) -> List[str]:
        """
        Get the list of labels for a specific field.
        
        Args:
            field: The field name to get labels for
            
        Returns:
            List of label strings for the field
        """
        pattern = self._field_patterns.get(field, {})
        return pattern.get('labels', [])
    
    def get_threshold_for(self, field: str) -> int:
        """
        Get the confidence threshold for a specific field.
        
        Args:
            field: The field name to get threshold for
            
        Returns:
            Confidence threshold value (0-100)
        """
        pattern = self._field_patterns.get(field, {})
        return pattern.get('threshold', DEFAULT_THRESHOLD)
    
    def get_all_fields(self) -> List[str]:
        """
        Get all available field names.
        
        Returns:
            List of field names
        """
        return list(self._field_patterns.keys())
    
    def get_field_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all field patterns with their labels and thresholds.
        
        Returns:
            Dictionary of field patterns
        """
        return self._field_patterns