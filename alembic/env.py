from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _ensure_src_on_path() -> None:
    root = _repo_root()
    sys.path.insert(0, str(root / "src"))


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import find_dotenv, load_dotenv  # type: ignore
    except Exception:
        return
    load_dotenv(find_dotenv())


def _to_sync_url(url: str) -> str:
    # Alembic runs sync; convert async sqlite URLs to sync driver.
    if url.startswith("sqlite+aiosqlite:///"):
        return url.replace("sqlite+aiosqlite:///", "sqlite+pysqlite:///")
    return url


def get_url() -> str:
    _load_dotenv_if_available()
    url = os.getenv("ALEMBIC_DB_URL") or os.getenv("DB_LITE") or os.getenv("DB_URL")
    if not url:
        # fallback, aligned with src/database/engine.py default
        db_path = _repo_root() / "data" / "sqlite_database" / "bot.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite+pysqlite:///{db_path.as_posix()}"
    return _to_sync_url(url)


_ensure_src_on_path()
from database.models import Base  # noqa: E402

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

