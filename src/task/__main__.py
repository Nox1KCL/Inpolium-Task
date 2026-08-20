from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from fastapi.middleware.cors import CORSMiddleware
from task.config.config import Config
from task.database.database import engine, init_db
from task.api.v1.router import v1_router
from task.logger.logger import setup_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = Config.load_config()
    setup_logger(cfg.logger)

    logger.info("App Startup..")
    await init_db()

    yield

    logger.info("App Shutdown..")
    await engine.dispose()

app = FastAPI(
    title="Steam API Service",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)
