# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BurmeseMoviesItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    year = scrapy.Field()
    director = scrapy.Field()
    cast = scrapy.Field()
    genre = scrapy.Field()
    synopsis = scrapy.Field()
    poster_url = scrapy.Field()
    streaming_link = scrapy.Field()
    pass
