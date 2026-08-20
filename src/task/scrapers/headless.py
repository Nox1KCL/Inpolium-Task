import re

from loguru import logger
from typing_extensions import Any

from task.schemas.schemas import HeadlessResult, Review
from task.config.config import AppConfig
from task.scrapers.utils import url_with_params, get_browser_page

def parse_review_card(raw_text: str) -> Review:
    lines = []
    for line in raw_text.split("\n"):
        if line.strip() != "":
            lines.append(line.strip())

    recommended = False
    if "Рекомендовано" in raw_text and "Не рекомендовано" not in raw_text:
        recommended = True

    date_match = re.search(r"ДОДАНО:\s*(.+)", raw_text, re.IGNORECASE)
    if date_match:
        posted_date = date_match.group(1).strip()
    else:
        posted_date = None

    hours_match = re.search(r"([\d,.]+)\s*год", raw_text, re.IGNORECASE)
    if hours_match:
        playtime = hours_match.group(1)
    else:
        playtime = None

    added_idx = -1
    for i in range(len(lines)):
        if "ДОДАНО:" in lines[i].upper():
            added_idx = i
            break
            
    useful_idx = len(lines)
    for i in range(len(lines)):
        if "КОРИСНОЮ" in lines[i].upper():
            useful_idx = i
            break

    review_text = ""
    if added_idx != -1 and added_idx < useful_idx:
        text_lines = lines[added_idx + 1:useful_idx]
        review_text = "\n".join(text_lines)

    return Review(
        text=review_text.strip(),
        recommended=recommended,
        release_date=posted_date,
        in_game_time=playtime,
    )

async def extract_review_cards(page, reviews_count: int = 3) -> list[str]:
    cards = page.locator('[data-featuretarget="appreviews"] [role="button"]').filter(has=page.locator('[data-miniprofile]'))
    count = await cards.count()

    texts = []
    seen = set()

    for i in range(count):
        if len(texts) >= reviews_count:
            break

        text = await cards.nth(i).inner_text()
        if text not in seen:
            seen.add(text)
            texts.append(text)

    logger.info(f"Review cards extracted: {len(texts)}")
    return texts


async def scroll_to_reviews(page):
    total_height = await page.evaluate("document.body.scrollHeight")
    for pos in range(0, total_height, 500):
        await page.evaluate(f"window.scrollTo(0, {pos})")
        await page.wait_for_timeout(100)

    for attempt in range(15):
        await page.wait_for_timeout(1000)
        body_text = await page.locator("body").inner_text()
        if "ДОДАНО:" in body_text:
            logger.info(f"Reviews loaded after {attempt + 1}s")
            return
    logger.warning("Reviews did not load after 15s")


async def headless_search(cfg: AppConfig, app_id: int, params: dict[str, Any], reviews_count: int = 3):
    async with get_browser_page(headless=True) as page:
        url = url_with_params(app_id, cfg.steam_base_url, params)
        _ = await page.goto(url)

        name = await page.locator("#appHubAppName").inner_text()
        companies = await page.locator(".grid_content a").all_inner_texts()
        developer = companies[0] if len(companies) > 0 else "N/A"
        producer = companies[1] if len(companies) > 1 else "N/A"
        release_date = await page.locator(".grid_content.grid_date").inner_text()

        price_location = page.locator(".discount_final_price")
        if await price_location.count() > 0:
            price = await price_location.first.inner_text()
        else:
            price = "Free"

        description = await page.locator(".game_description_snippet").inner_text()
        summary = await page.locator(".game_review_summary").first.inner_text()

        await scroll_to_reviews(page)

        review_texts = await extract_review_cards(page, reviews_count)
        reviews = [parse_review_card(raw) for raw in review_texts]

        return HeadlessResult(
            app_id=app_id,
            name=name,
            url=url,
            price=price,
            description=description,
            developer=developer,
            producer=producer,
            release_date=release_date,
            users_summary_rating=summary,
            review=reviews,
        )
