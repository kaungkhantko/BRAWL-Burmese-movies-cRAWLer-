"""
Header mapping utilities for table extraction.
"""
import logging
from typing import Dict, List, Tuple, Optional

from burmese_movies_crawler.utils.exceptions import TableProcessingError
from burmese_movies_crawler.utils.field_matcher import FieldMatcher

logger = logging.getLogger(__name__)


class HeaderMapper:
    """
    Maps table headers to field names using fuzzy matching.
    """
    
    def __init__(self, field_matcher: FieldMatcher):
        """
        Initialize the header mapper with a field matcher.
        
        Args:
            field_matcher: The field matcher to use for matching headers to fields
        """
        self.field_matcher = field_matcher
        self._header_map_cache: Dict[Tuple[str, ...], Dict[str, str]] = {}
    
    def map(self, headers: List[str]) -> Dict[str, str]:
        """
        Map table headers to field names.
        
        Args:
            headers: List of header strings from a table
            
        Returns:
            Dictionary mapping header strings to field names
            
        Raises:
            TableProcessingError: If an error occurs during header mapping
        """
        try:
            if not headers:
                return {}
                
            results = {}
            headers_key = None
            use_cache = True
            
            try:
                # Create a cache key for this set of headers
                headers_key = tuple(str(h) for h in headers if h)
                
                # Check if we already processed these headers
                try:
                    if headers_key in self._header_map_cache:
                        return dict(self._header_map_cache[headers_key])
                except Exception as e:
                    logger.warning(f"Error checking headers cache: {str(e)}")
                    use_cache = False
            except Exception as e:
                logger.warning(f"Error creating headers cache key: {str(e)}")
                use_cache = False
                
            # Process each header
            for head in headers:
                try:
                    if not head:
                        continue
                    
                    # Check if this header is already in the cache
                    if use_cache:
                        try:
                            header_key = tuple([head])
                            if header_key in self._header_map_cache:
                                cached_result = self._header_map_cache[header_key]
                                if head in cached_result:
                                    results[head] = cached_result[head]
                                    continue
                        except Exception:
                            # Ignore cache errors and continue with matching
                            pass
                    
                    # Find best match for this header
                    field, score = self.field_matcher.match(head)
                    if field:
                        results[head] = field
                        # Cache individual header mapping if caching is enabled
                        if use_cache:
                            try:
                                header_key = tuple([head])
                                self._header_map_cache[header_key] = {head: field}
                            except Exception:
                                # Ignore cache errors
                                pass
                except Exception as e:
                    logger.warning(f"Error processing header '{head}': {str(e)}")
                    # Propagate the error as TableProcessingError
                    raise TableProcessingError(f"Failed to process header '{head}': {str(e)}") from e
                    
            # Cache the mapping for these headers if caching is enabled
            if use_cache and headers_key:
                try:
                    self._header_map_cache[headers_key] = dict(results)
                except Exception as e:
                    logger.warning(f"Error caching header mapping: {str(e)}")
                
            return results
            
        except TableProcessingError:
            # Re-raise TableProcessingError without wrapping
            raise
        except Exception as e:
            logger.error(f"Header mapping error: {str(e)}")
            raise TableProcessingError(f"Failed to map headers: {str(e)}") from e