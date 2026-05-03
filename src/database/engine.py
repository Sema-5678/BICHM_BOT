from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base


def _default_sqlite_url() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    db_path = repo_root / "data" / "sqlite_database" / "bot.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+aiosqlite:///{db_path.as_posix()}"


DB_URL = os.getenv("DB_LITE") or os.getenv("DB_URL") or _default_sqlite_url()

engine = create_async_engine(DB_URL, echo=False)
session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_maker() as session:
        yield session

