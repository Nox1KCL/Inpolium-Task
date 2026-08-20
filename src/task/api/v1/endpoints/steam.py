import time
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from opentelemetry import metrics
from opentelemetry.metrics import Counter, Histogram
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import BackgroundTasks
from task.config.config import Config
from task.database.database import DB_History, get_db_session
from task.schemas.schemas import BasicResult, HeadlessResult, HistoryResponse, NonHeadlessResult
from task.scrapers.basic import basic_search
from task.scrapers.headless import headless_search
from task.scrapers.non_headless import non_headless_search
from task.scrapers.utils import url_with_params

meter = metrics.get_meter("steam.scraper.api")

counter: Counter = meter.create_counter(
    "api.requests",
    description="Counting total count of errors, valuable events",
    unit="1"
)

histogram: Histogram = meter.create_histogram(
    "api.request.duration",
    description="Calculating total time for some durationals event",
    unit="ms"
)

router = APIRouter(
    prefix="/steam/api/v1",
    tags=["Steam_Games"]
)

DBSession = Annotated[AsyncSession, Depends(get_db_session)]
ConfigSession = Annotated[Config, Depends(Config.load_config)]

@router.post("/games/search/basic")
async def basic(term: str, results_limit: int, db: DBSession, cfg: ConfigSession) -> list[BasicResult] | str:
    start = time.time()
    method = "http"
    status = ""
    data = None

    try:
        results = await basic_search(cfg.app, term, results_limit, "UA", "ukrainian", )
        if results is None or len(results) == 0:
            raise HTTPException(status_code=404, detail="Results is empty")

        status = "success"
        data: list[dict[str, Any]] | None = [r.model_dump() for r in results]

    except Exception as e:
        counter.add(1, {"method": method, "stage": "basic", "type": "errors.count"})
        logger.bind(method=method, term=term).error("Search error: {}", e)

        data = [{"error": str(e)}]
        status = "error"
        raise

    finally:
        duration = (time.time() - start) * 1000
        histogram.record(duration, {"method": method, "stage": "basic", "type": "spent.time"})

        db.add(DB_History(
            method=method,
            query=term,
            status=status,
            start_time=start,
            finish_time=time.time(),
            result=data,
        ))
        await db.commit()

    counter.add(1, {"method": method, "stage": "basic", "type": "success.count"})
    return results

@router.post("/games/search/expanded")
async def expanded(term: str, reviews_count: int, params: dict[str, str], db: DBSession, cfg: ConfigSession) -> HeadlessResult:
    start = time.time()
    method = "headless"
    status = ""
    data = None

    try:
        basic = await basic_search(cfg.app, term)
        if basic is None or len(basic) == 0:
            raise HTTPException(status_code=404, detail="Results is empty")
        id = basic[0].app_id

        result = await headless_search(cfg.app, id, params, reviews_count)
        data: list[dict[str, Any]] | None = [result.model_dump()]

        status = "success"

    except Exception as e:
        counter.add(1, {"method": method, "stage": "expanded", "type": "errors.count"})
        logger.bind(method=method, term=term).error("Search error: {}", e)

        data = [{"error": str(e)}]
        status = "error"
        raise

    finally:
        duration = (time.time() - start) * 1000
        histogram.record(duration, {"method": method, "stage": "expanded", "type": "spent.time"})

        db.add(DB_History(
            method=method,
            query=term,
            status=status,
            start_time=start,
            finish_time=time.time(),
            result=data,
        ))
        await db.commit()

    counter.add(1, {"method": method, "stage": "expanded", "type": "success.count"})
    return result

@router.post("/games/open")
async def open(term: str, params: dict[str, str], db: DBSession, cfg: ConfigSession, background_tasks: BackgroundTasks) -> NonHeadlessResult:
    start = time.time()
    method = "non_headless"
    status = ""
    data = None

    try:
        basic = await basic_search(cfg.app, term)
        if basic is None or len(basic) == 0:
            raise HTTPException(status_code=404, detail="Results is empty")
        id = basic[0].app_id

        url = url_with_params(id, cfg.app.steam_base_url, params)
        background_tasks.add_task(non_headless_search, url)

        status = "success"
        result = NonHeadlessResult(
            app_id=id,
            url=url,
            status=status,
            name=basic[0].name,
            price=basic[0].price,
        )
        data = [result.model_dump()]

    except Exception as e:
        counter.add(1, {"method": method, "stage": "open", "type": "errors.count"})
        logger.bind(method=method, term=term).error("Open error: {}", e)

        data = [{"error": str(e)}]
        status = "error"
        raise

    finally:
        duration = (time.time() - start) * 1000
        histogram.record(duration, {"method": method, "stage": "open", "type": "spent.time"})

        db.add(DB_History(
            method=method,
            query=term,
            status=status,
            start_time=start,
            finish_time=time.time(),
            result=data,
        ))
        await db.commit()

    counter.add(1, {"method": method, "stage": "open", "type": "success.count"})
    return result

@router.get("/history")
async def history(skip: int,  db: DBSession, limit: int = 50) -> list[HistoryResponse]:
    start = time.time()

    stmt = select(DB_History).order_by(DB_History.id.desc()).offset(skip).limit(limit)
    results = await db.execute(stmt)
    records = results.scalars().all()

    duration = (time.time() - start) * 1000
    histogram.record(duration, {"method": "history/all", "stage": "history/all", "type": "spent.time"})

    return [HistoryResponse.model_validate(r) for r in records]

@router.get("/history/{history_id}")
async def get_history_by_id(history_id: int, db: DBSession) -> HistoryResponse:
    start = time.time()

    stmt = select(DB_History).where(DB_History.id == history_id)
    history = await db.scalar(stmt)
    if history is None:
        raise HTTPException(status_code=404, detail="Record not found")

    duration = (time.time() - start) * 1000
    histogram.record(duration, {"method": "history/id", "stage": "history/id", "type": "spent.time"})

    return HistoryResponse.model_validate(history)
