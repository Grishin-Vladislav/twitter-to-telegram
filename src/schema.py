from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def normalize_date(date: str) -> datetime:
    return datetime.strptime(date, "%a %b %d %H:%M:%S %z %Y")


class XUser(BaseModel):
    userName: str
    name: str
    profilePicture: str


class QuoteOrRetweet(BaseModel):
    type: str
    author: XUser
    text: str
    createdAt: datetime = Field(..., serialization_alias="created_at")

    normalize_date = field_validator("createdAt", mode="before")(normalize_date)


class Retweet(QuoteOrRetweet):
    pass


class Quote(QuoteOrRetweet):
    pass


class Tweet(BaseModel):
    author: XUser
    text: str
    url: str
    # reply_to_url: Optional[str] = None  # TODO
    isReply: bool
    isRetweet: bool
    isQuote: bool
    retweet: Retweet = None
    quote: Quote = None
    createdAt: datetime = Field(..., serialization_alias="created_at")

    normalize_date = field_validator("createdAt", mode="before")(normalize_date)
