# tests/unit/utils/test_item_schema.py
import pytest
from burmese_movies_crawler.schema.item_schema import MovieItem
from pydantic import ValidationError

def test_valid_movie_item():
    item = MovieItem(title="The Road", year=2008, director="John Hillcoat", genre="Drama")
    assert item.title == "The Road"

def test_invalid_year():
    with pytest.raises(ValidationError):
        MovieItem(title="Future Movie", year=3000, director="AI Director")

@pytest.mark.parametrize("bad_year", [1799, 2200, -1, 9999])
def test_invalid_year(bad_year):
    with pytest.raises(ValidationError):
        MovieItem(title="Invalid Year", year=bad_year, director="X")

@pytest.mark.parametrize("raw,expected", [
    ("  The Test Title ", "The Test Title"),
    ("\nTabbed\n", "Tabbed"),
])
def test_title_trimmed(raw, expected):
    item = MovieItem(title=raw, year=2000, director="Dir")
    assert item.title == expected

@pytest.mark.parametrize("raw,expected", [
    (" John Doe ", "John Doe"),
    ("\tJane\t", "Jane"),
])
def test_director_trimmed(raw, expected):
    item = MovieItem(title="X", year=2000, director=raw)
    assert item.director == expected

@pytest.mark.parametrize("cast_input,expected", [
    ("Actor One, Actor Two , Actor Three  ", ["Actor One", "Actor Two", "Actor Three"]),
    ("A,,B,, ,C", ["A", "B", "C"]),
    ("", []),
])
def test_cast_string_splits_to_list(cast_input, expected):
    item = MovieItem(title="Cast Test", year=2010, director="Jane", cast=cast_input)
    assert item.cast == expected

@pytest.mark.parametrize("bad_synopsis", ["N/A", "no synopsis", "Not Available", ""])
def test_synopsis_na_converts_to_none(bad_synopsis):
    item = MovieItem(title="No Synopsis Test", year=1999, director="Someone", synopsis=bad_synopsis)
    assert item.synopsis is None

@pytest.mark.parametrize("bad_url", [
    "not-a-url",
    "ftp://poster.jpg",
    "example.com/poster.jpg",
])
def test_invalid_poster_url_format(bad_url):
    with pytest.raises(ValidationError):
        MovieItem(title="Bad URL", year=2010, director="Dev", poster_url=bad_url)

@pytest.mark.parametrize("long_text", ["A" * 1001, " " * 1500])
def test_synopsis_exceeds_max_length(long_text):
    with pytest.raises(ValidationError):
        MovieItem(title="Too Long", year=2020, director="Editor", synopsis=long_text)

@pytest.mark.parametrize("valid_year", [1800, 2030])
def test_year_at_bounds(valid_year):
    item = MovieItem(title="Boundary Year", year=valid_year, director="Year Master")
    assert item.year == valid_year

@pytest.mark.parametrize("input_list,expected", [
    ([" Alice ", "Bob", "  Charlie  "], ["Alice", "Bob", "Charlie"]),
    (["", " ", "\t", "John"], ["John"]),
    ([], []),
])
def test_cast_list_cleaned(input_list, expected):
    item = MovieItem(title="Cast Clean", year=2022, director="Cleaner", cast=input_list)
    assert item.cast == expected
