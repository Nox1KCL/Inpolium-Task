from typing_extensions import Any

from task.schemas.schemas import HeadlessResult, Review
from task.config.config import AppConfig
from task.scrapers.utils import parse_review_card, url_with_params, get_browser_page


async def headless_search(cfg: AppConfig, app_id: int, params: dict[str, Any], reviews_count: int = 3):
    async with get_browser_page(headless=True) as page:
        url = url_with_params(app_id, cfg.steam_base_url, params)
        _ = await page.goto(url)

        name = await page.locator(".apphub_AppName").inner_text()
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

        reviews_anchor = page.locator("#AppUserReviews, .user_reviews_scroll_area").first
        await reviews_anchor.scroll_into_view_if_needed()

        sort_dropdown = page.get_by_text("Показ", exact=True)
        if await sort_dropdown.count() > 0:
            await sort_dropdown.first.click()

        async with page.expect_response(
            lambda r: "ajaxappreviews" in r.url and r.status == 200
        ) as resp_info:
            await reviews_anchor.scroll_into_view_if_needed()
            await page.locator('input[name="review_context"][value="recent"]').check()

        _ = await resp_info.value

        review_list = page.locator('[role="list"]').filter(has_text="Додано").first
        cards = review_list.locator('div[role="button"]')
        await cards.first.wait_for(state="visible")

        count = await cards.count()
        review_cards = []
        for i in range(min(count, reviews_count)):
            card_text = await cards.nth(i).inner_text()
            review_cards.append(card_text)

        reviews: list[Review] = []
        for raw in review_cards:
            reviews.append(parse_review_card(raw))

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
