from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def _setup_import_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    sys.path.insert(0, str(src_path))


async def main() -> None:
    _setup_logging()
    log = logging.getLogger("db_smoke_test")

    _setup_import_path()
    try:
        from dotenv import find_dotenv, load_dotenv  # type: ignore
    except Exception:
        logging.getLogger("db_smoke_test").warning(
            "python-dotenv не установлен — пропускаю загрузку .env (использую переменные окружения процесса)."
        )
    else:
        load_dotenv(find_dotenv())

    from database.engine import DB_URL, create_db, drop_db, session_maker
    from database.orm import (
        orm_delete_singleton,
        orm_delete_user,
        orm_get_admins_ids,
        orm_get_or_create_user,
        orm_get_singleton,
        orm_get_user,
        orm_set_admins_ids,
        orm_set_singleton,
        orm_update_user_fields,
    )

    log.info("DB_URL=%s", DB_URL)
    if not (os.getenv("DB_LITE") or os.getenv("DB_URL")):
        log.info("ENV: DB_LITE/DB_URL не задан — использую дефолтный путь из database.engine")

    log.info("1) drop_db()")
    await drop_db()
    log.info("2) create_db()")
    await create_db()

    test_user_id = 123456789
    singleton_key = "admins_data"

    async with session_maker() as session:
        log.info("3) Cleanup before assertions")
        await orm_delete_user(session, test_user_id)
        await orm_delete_singleton(session, singleton_key)

        log.info("4) orm_get_user() -> None")
        user = await orm_get_user(session, test_user_id)
        assert user is None, "Expected user to be absent after cleanup"

        log.info("5) orm_get_or_create_user() creates user")
        user = await orm_get_or_create_user(session, test_user_id, username="tester")
        assert user.id == test_user_id
        assert user.username == "tester"
        assert int(user.date_create) > 0
        assert int(user.date_update) > 0

        log.info("6) orm_update_user_fields() updates balance + username")
        await orm_update_user_fields(session, test_user_id, balance="99.50", username="tester2")
        user2 = await orm_get_user(session, test_user_id)
        assert user2 is not None
        assert str(user2.balance) in {"99.50", "99.5"}
        assert user2.username == "tester2"

        log.info("7) Singletons: set/get admins_data")
        await orm_set_admins_ids(session, [1, 2, 3])
        admins = await orm_get_admins_ids(session)
        assert admins == [1, 2, 3]

        log.info("8) Singletons: generic set/get")
        await orm_set_singleton(session, "minecraft_goods", {"a": 1, "b": {"c": 2}})
        data = await orm_get_singleton(session, "minecraft_goods")
        assert data == {"a": 1, "b": {"c": 2}}

        log.info("9) Delete user + singleton and verify")
        await orm_delete_user(session, test_user_id)
        await orm_delete_singleton(session, "minecraft_goods")
        assert await orm_get_user(session, test_user_id) is None
        assert await orm_get_singleton(session, "minecraft_goods") == {}

    log.info("OK: smoke tests passed")


if __name__ == "__main__":
    asyncio.run(main())
