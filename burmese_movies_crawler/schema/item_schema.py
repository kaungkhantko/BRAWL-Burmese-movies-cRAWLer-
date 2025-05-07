from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import Optional, List, Union

class MovieItem(BaseModel):
    title: str = Field(..., min_length=1)
    year: int
    director: str = Field(..., min_length=1)
    cast: Optional[List[str]] = None
    genre: Optional[str] = None
    synopsis: Optional[str] = Field(default=None, max_length=1000)
    poster_url: Optional[HttpUrl] = None
    streaming_link: Optional[HttpUrl] = None

    @field_validator("year")
    def year_must_be_reasonable(cls, v):
        if not (1900 <= v <= 2100):
            raise ValueError("Year must be between 1900 and 2100")
        return v

    @field_validator("title", "director", mode="before")
    def strip_text_fields(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("cast", mode="before")
    def split_and_strip_cast(cls, v: Union[str, List[str]]):
        if isinstance(v, str):
            # Convert comma-separated string
            v = v.split(",")
        if isinstance(v, list):
            # Strip each entry and remove empty ones
            return [name.strip() for name in v if isinstance(name, str) and name.strip()]
        return None

    @field_validator("synopsis", mode="before")
    def clean_synopsis(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v.lower() in {"n/a", "not available", "no synopsis", ""}:
                return None
        return v

    @field_validator("synopsis", mode="before")
    def check_synopsis_length(cls, v):
        if v and isinstance(v, str) and len(v) > 1000:
            raise ValueError("Synopsis too long (max 1000 characters)")
        return v

