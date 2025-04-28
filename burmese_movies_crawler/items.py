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


# --- Field to selector mapping ---
FIELD_SELECTORS = {
    "title": ["h2.title::text", "div.movie-title::text", "span.title::text"],
    "year": ["span.year::text", "div.release-year::text"],
    "director": ["span.director::text", "div.director-name::text"],
    "cast": ["span.cast::text", "div.actor-list::text"],
    "genre": ["span.genre::text", "div.genre-tag::text"],
    "synopsis": ["p.synopsis::text", "div.synopsis-text::text"],
    "poster_url": ["img.poster::attr(src)", "img.cover::attr(src)"],
    "streaming_link": ["a.watch-link::attr(href)", "a.stream-now::attr(href)"],
}