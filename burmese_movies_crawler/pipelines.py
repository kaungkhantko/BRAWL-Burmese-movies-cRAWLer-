# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from burmese_movies_crawler.schema.item_schema import MovieItem
import logging
from scrapy.exceptions import DropItem


class BurmeseMoviesPipeline:
    def process_item(self, item, spider):
        try:
            validated = MovieItem(**dict(item))
            return item
        except Exception as e:
            spider.logger.warning(f"Dropping invalid item: {e}")
            raise DropItem("Validation failed")
