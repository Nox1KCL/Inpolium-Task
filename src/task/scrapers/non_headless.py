from loguru import logger

from task.scrapers.utils import get_browser_page


async def non_headless_search(url: str):
    logger.bind(url=url).info("Non-headless browser opened")
    async with get_browser_page(headless=False) as page:
        _ = await page.goto(url)

        # REST API тут не буде зависати, бо endpoint відправляє
        # цю функцію у background_task
        _ = await page.wait_for_event("close")
        logger.bind(url=url).info("Page closed")
