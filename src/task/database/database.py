from collections.abc import AsyncGenerator
from typing import Any
from loguru import logger
from pydantic import ConfigDict
from sqlalchemy import JSON, String
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from task.database.db_config import DB_Config


DATABASE_URL = DB_Config().get_db_url # pyright: ignore[reportCallIssue]

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class DB_History(Base):
    __tablename__ = "history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    method: Mapped[str] = mapped_column(String(50), index=True)
    query: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20))
    start_time: Mapped[float] = mapped_column()
    finish_time: Mapped[float] = mapped_column()
    result: Mapped[list[dict[str, Any]] | None]  = mapped_column(JSON, nullable=True)

async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        logger.info("DBSession opened")
        try:
            yield session
        finally:
            logger.info("DBSession closed")
