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


def _normalize_sqlite_url(url: str) -> str:
    """
    Ensures that for file-based sqlite URLs:
    - path is absolute (anchored at repo root if relative)
    - parent directory exists
    """
    prefix = "sqlite+aiosqlite:///"
    if not url.startswith(prefix):
        return url

    raw_path = url[len(prefix) :]
    if raw_path in {":memory:", ""}:
        return url

    repo_root = Path(__file__).resolve().parents[2]

    if raw_path.startswith("./") or raw_path.startswith(".\\"):
        path = repo_root / raw_path[2:]
    else:
        candidate = Path(raw_path)
        if candidate.is_absolute() or (len(raw_path) >= 3 and raw_path[1:3] == ":/"):
            path = candidate
        else:
            path = repo_root / raw_path

    path.parent.mkdir(parents=True, exist_ok=True)
    return f"{prefix}{path.as_posix()}"


DB_URL = os.getenv("DB_LITE") or os.getenv("DB_URL") or _default_sqlite_url()
DB_URL = _normalize_sqlite_url(DB_URL)

engine = create_async_engine(DB_URL, echo=False)
session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        if engine.url.get_backend_name() == "sqlite":
            cols = set()
            try:
                result = await conn.exec_driver_sql("PRAGMA table_info(users)")
                for row in result:
                    cols.add(row[1])
            except Exception:
                cols = set()

            if "minecraft_username" not in cols:
                await conn.exec_driver_sql("ALTER TABLE users ADD COLUMN minecraft_username VARCHAR(16)")


async def drop_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_maker() as session:
        yield session
