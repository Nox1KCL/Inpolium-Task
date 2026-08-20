from typing import Any

from pydantic import BaseModel, ConfigDict


class Review(BaseModel):
    text: str
    recommended: bool
    release_date: str | None
    in_game_time: str | None

class Basis(BaseModel):
    app_id: int
    name: str
    url: str
    price: float | str

class BasicResult(Basis):
    currency: str
    discount: float
    platforms: list[str]

class HeadlessResult(Basis):
    developer: str
    producer: str
    release_date: str
    description: str
    users_summary_rating: str
    review: list[Review]

class NonHeadlessResult(Basis):
    status: str

class HistoryResponse(BaseModel):
    id: int
    method: str
    query: str
    status: str
    start_time: float
    finish_time: float
    result: list[dict[str, Any]] | None

    model_config = ConfigDict(from_attributes=True)


class SteamPrice(BaseModel):
    currency: str
    final: int
    discount_percent: int = 0

class SteamPlatforms(BaseModel):
    windows: bool
    mac: bool
    linux: bool

class SteamItem(BaseModel):
    id: int
    name: str
    tiny_image: str
    platforms: SteamPlatforms
    price: SteamPrice | None = None

    def to_basic(self) -> BasicResult:

        final_price = self.price.final if self.price else "Free"
        currency = self.price.currency if self.price else "N/A"
        discount = self.price.discount_percent if self.price else 0

        if isinstance(final_price, int):
            final_price /= 100

        return BasicResult(
            app_id=self.id,
            name=self.name,
            url=f"https://store.steampowered.com/app/{self.id}/",
            price=final_price,
            currency=currency,
            discount=discount,
            platforms=[p for p, v in self.platforms.model_dump().items() if v],
        )

class SteamAPIResult(BaseModel):
    total: int
    items: list[SteamItem]
