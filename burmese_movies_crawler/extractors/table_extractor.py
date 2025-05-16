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
            headers = []
            try:
                # First try to get headers from thead
                headers = [h.strip() for h in table.css('thead th::text, thead td::text').getall()]
                
                # If no headers found, try the first row
                if not headers:
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
            
            # Process rows
            try:
                # First try tbody rows
                rows = table.css('tbody tr')
                
                # If no tbody or no rows in tbody, try all rows except the first one (which contains headers)
                if not rows:
                    all_rows = table.css('tr')
                    if len(all_rows) > 1:  # Skip the header row
                        rows = all_rows[1:]
            except Exception as e:
                logger.error(f"Failed to get table rows: {str(e)}")
                raise TableProcessingError(f"Failed to get table rows: {str(e)}") from e
            
            for row in rows:
                try:
                    # Get all text from cells, including nested elements
                    cell_texts = []
                    for i, cell in enumerate(row.css('td')):
                        # Get all text from this cell
                        cell_text = ' '.join([t.strip() for t in cell.css('::text').getall() if t.strip()])
                        cell_texts.append(cell_text)
                    
                    # Handle partial matches gracefully
                    if any(cell_texts):  # At least one cell has content
                        item = self._create_item(cell_texts, headers, header_map)
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
                if field and field in item.fields and value.strip():  # Check if field exists in item and value is not empty
                    item[field] = value
        
        return item