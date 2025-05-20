# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

# Field selectors for extracting data from pages
FIELD_SELECTORS = {
    'title': ['h1', '.movie-title', '.title', 'header h1'],
    'year': ['.year', '.release-date', '.movie-year'],
    'director': ['.director', '.directed-by', '.movie-director'],
    'cast': ['.cast', '.actors', '.movie-cast'],
    'genre': ['.genre', '.categories', '.movie-genre'],
    'synopsis': ['.synopsis', '.plot', '.description', '.movie-description'],
    'poster_url': ['.poster img', '.movie-poster img', '.cover img'],
    'streaming_link': ['.watch-button', '.stream-link', '.play-button']
}

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