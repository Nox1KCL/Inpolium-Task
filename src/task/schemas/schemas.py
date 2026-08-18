from datetime import date, time

from pydantic import BaseModel
from pydantic_settings import BaseSettings

class Review(BaseModel):
    text: str
    rate: str
    release_date: date
    in_game_time: float

class Base(BaseModel):
    app_id: int
    name: str
    url: str
    price: float | str

class BasicResult(Base):
    currency: str
    discount: float
    platforms: list[str]

class HeadlessResult(Base):
    developer: str
    producer: str
    release_date: date
    description: str
    users_rating: float
    review: Review

class NonHeadlessResult(Base):
    status: str
