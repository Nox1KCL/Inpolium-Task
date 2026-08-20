from contextlib import asynccontextmanager
import urllib.parse

from loguru import logger
from playwright.async_api import async_playwright
from typing_extensions import Any

from task.config.config import AppConfig
from task.schemas.schemas import BasicResult, SteamItem


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

@asynccontextmanager
async def get_browser_page(headless: bool):
    async with async_playwright() as p:
        logger.debug("Playwright initialized")
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            locale="uk-UA",
        )
        await context.add_cookies([{
            "name": "birthtime", "value": "283993201", "domain": "store.steampowered.com", "path": "/"
        }])

        page = await context.new_page()
        try:
            logger.debug("Giving page to caller")
            yield page
        finally:
            await browser.close()
            logger.info("Browser closed")
