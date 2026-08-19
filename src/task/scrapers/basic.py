import httpx
from loguru import logger

from task.config.config import AppConfig
from task.schemas.schemas import BasicResult, SteamAPIResult
from task.scrapers.utils import unified_game, create_api_url


async def basic_search(cfg: AppConfig, term: str, country_code: str, language: str, limit: int) -> list[BasicResult] | None:
    url, params = create_api_url(cfg, term, country_code, language)
    timeout = cfg.http_timeout
    results: list[BasicResult] = []

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=timeout)
            steam_result = SteamAPIResult(**response.json())
            for item in steam_result.items[:limit]:
                game = unified_game(item)
                results.append(game)

            return results

    except httpx.TimeoutException:
        logger.error(f"Steam API timeout error | timeout: {timeout}")
        raise
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP status error: {e.response.status_code} | {e.response.text}")
        raise
