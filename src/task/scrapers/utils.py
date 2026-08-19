from contextlib import asynccontextmanager
import urllib.parse
import re

from loguru import logger
from playwright.async_api import async_playwright
from typing_extensions import Any

from task.config.config import AppConfig
from task.schemas.schemas import BasicResult, Review, SteamItem


def create_api_url(cfg: AppConfig, term: str, country_code: str, language: str) -> tuple[str, dict[str, str]]:
    url = cfg.steam_api_url
    params = {
        "term": term,
        "cc": country_code,
        "l": language
    }
    return url, params

def unified_game(item: SteamItem) -> BasicResult:
    return item.to_basic()

def url_with_params(app_id: int, url: str, params: dict[str, Any]) -> str:
    url_with_id = f"{url}{app_id}/"
    return f"{url_with_id}?{urllib.parse.urlencode(params)}"

def parse_review_card(raw_text: str) -> Review:
    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]

    recommended = any("recommend" in l.lower() or "рекоменд" in l.lower() for l in lines)

    date_match = re.search(r"Додано:\s*(.+)", raw_text)
    posted_date = date_match.group(1).strip() if date_match else None

    hours_match = re.search(r"([\d,.]+)\s*(hrs|год)", raw_text)
    playtime = hours_match.group(1) if hours_match else None

    service_markers = ("posted", "додано", "helpful", "корисн", "recommend", "рекоменд")
    body_candidates = [
        l for l in lines
        if len(l) > 20 and not any(m in l.lower() for m in service_markers)
    ]
    review_text = max(body_candidates, key=len) if body_candidates else ""

    return Review(
        text=review_text,
        recommended=recommended,
        release_date=posted_date,
        in_game_time=playtime,
    )

@asynccontextmanager
async def get_browser_page(headless: bool):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            locale="uk-UA",
        )
        await context.add_cookies([{
            "name": "birthtime", "value": "283993201", "domain": "store.steampowered.com", "path": "/"
        }])

        page = await context.new_page()
        try:
            yield page
        finally:
            await browser.close()
            logger.info("Browser has been closed successfully")
