from typing import Any

from loguru import logger

from task.config.config import AppConfig
from task.scrapers.utils import get_browser_page, url_with_params


async def non_headless_search(cfg: AppConfig, app_id: int, params: dict[str, Any]):
    async with get_browser_page(headless=False) as page:
        url = url_with_params(app_id, cfg.steam_base_url, params)
        _ = await page.goto(url)

        _ = await page.wait_for_event("close")
        logger.info(f"Page closed: {url}")
