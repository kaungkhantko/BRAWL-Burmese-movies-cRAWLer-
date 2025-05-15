"""
Table extraction module for web content.
"""
import logging
from typing import Generator, Dict, List, Any

from burmese_movies_crawler.items import BurmeseMoviesItem
from burmese_movies_crawler.utils.exceptions import TableProcessingError
from burmese_movies_crawler.utils.header_mapper import HeaderMapper

logger = logging.getLogger(__name__)


class TableExtractor:
    """
    Extracts structured data from tables in HTML responses.
    """
    
    def __init__(self, header_mapper: HeaderMapper):
        """
        Initialize the table extractor with a header mapper.
        
        Args:
            header_mapper: The header mapper to use for mapping table headers to fields
        """
        self.header_mapper = header_mapper
        self.items_scraped = 0
    
    def extract(self, response, table) -> Generator[BurmeseMoviesItem, None, None]:
        """
        Extract structured data from a table in a response.
        
        Args:
            response: Scrapy response object
            table: Table element from the response
            
        Yields:
            BurmeseMoviesItem objects with extracted data
            
        Raises:
            TableProcessingError: If an error occurs during table extraction
        """
        try:
            if not response or not table:
                logger.error("No response or table object provided")
                raise TableProcessingError("No response or table object provided")
                
            # Extract headers once and validate
            try:
                headers = [h.strip() for h in table.css('thead th::text, thead td::text').getall()]
                if not headers:
                    # Fallback if <thead> is missing
                    headers = [h.strip() for h in table.css('tr:first-child th::text, tr:first-child td::text').getall()]
            except Exception as e:
                logger.error(f"Failed to extract table headers: {str(e)}")
                raise TableProcessingError(f"Failed to extract table headers: {str(e)}") from e
            
            if not headers:
                logger.warning("No headers found in table, skipping extraction")
                return
                
            # Map headers to fields
            try:
                header_map = self.header_mapper.map(headers)
            except Exception as e:
                logger.error(f"Failed to map headers: {str(e)}")
                raise TableProcessingError(f"Failed to map headers: {str(e)}") from e
            
            # Process rows in batches
            try:
                rows = table.css('tbody tr')
            except Exception as e:
                logger.error(f"Failed to get table rows: {str(e)}")
                raise TableProcessingError(f"Failed to get table rows: {str(e)}") from e
            
            for row in rows:
                try:
                    cells = [c.strip() for c in row.css('td::text, td *::text').getall() if c.strip()]
                    
                    # Handle partial matches gracefully
                    if cells:
                        item = self._create_item(cells, headers, header_map)
                        if any(item.values()):
                            yield item
                            self.items_scraped += 1
                except Exception as e:
                    logger.warning(f"Error processing table row: {str(e)}")
                    # Continue with next row
                    
        except Exception as e:
            if not isinstance(e, TableProcessingError):
                logger.error(f"Table extraction error: {str(e)}")
                raise TableProcessingError(f"Failed to process table: {str(e)}") from e
            raise
    
    def _create_item(self, cells: List[str], headers: List[str], header_map: Dict[str, str]) -> BurmeseMoviesItem:
        """
        Create a BurmeseMoviesItem from table cells and header mapping.
        
        Args:
            cells: List of cell values from a table row
            headers: List of header strings from the table
            header_map: Dictionary mapping header strings to field names
            
        Returns:
            BurmeseMoviesItem with mapped fields
        """
        item = BurmeseMoviesItem()
        
        # Map available cells to headers
        for i, value in enumerate(cells):
            if i < len(headers):
                field = header_map.get(headers[i])
                if field:
                    item[field] = value
        
        return item