from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Any, AsyncIterator

from database.engine import session_maker
from database.orm import (
    orm_get_or_create_user,
    orm_list_users,
    orm_get_singleton,
    orm_set_singleton,
    orm_update_user_fields,
)


_USER_LOCKS: dict[int, asyncio.Lock] = {}
_LOCKS_GUARD = asyncio.Lock()


async def _user_lock(user_id: int) -> asyncio.Lock:
    async with _LOCKS_GUARD:
        lock = _USER_LOCKS.get(user_id)
        if lock is None:
            lock = asyncio.Lock()
            _USER_LOCKS[user_id] = lock
        return lock


def _initial_field() -> list[list[dict[str, Any]]]:
    return [
        [{"plant": None, "status": None}, {"plant": None, "status": None}, {"plant": None, "status": None}],
        [{"plant": None, "status": None}, {"plant": None, "status": None}, {"plant": None, "status": None}],
        [{"plant": None, "status": None}, {"plant": None, "status": None}, {"plant": None, "status": None}],
    ]


def _default_user_dict(user_id: int) -> dict[str, Any]:
    now = int(time.time())
    return {
        "balance": Decimal("60.00"),
        "debt": Decimal("0.00"),
        "deposit": Decimal("0.00"),
        "credit_rating": 100,
        "min_deposit": Decimal("0.00"),
        "max_loan": Decimal("0.00"),
        "getbc_time": 0,
        "username": "",
        "minecraft_username": None,
        "date_create": now,
        "date_update": now,
        "last_interest_date": None,
        "inventory": {},
        "minecraft_goods_count_season": {},
        "rub_balance": Decimal("0.00"),
        "farm_minigame": {
            "field": _initial_field(),
            "fc_balance": 0,
            "last_care_day": None,
            "missed_days": 0,
            "field_size": 3,
            "inventory": {},
            "boosts": {},
            "last_visit": now,
        },
    }


def _user_to_dict(user) -> dict[str, Any]:
    return {
        "balance": user.balance,
        "debt": user.debt,
        "deposit": user.deposit,
        "credit_rating": user.credit_rating,
        "min_deposit": user.min_deposit,
        "max_loan": user.max_loan,
        "getbc_time": user.getbc_time,
        "username": user.username or "",
        "minecraft_username": user.minecraft_username,
        "date_create": user.date_create,
        "date_update": user.date_update,
        "last_interest_date": user.last_interest_date,
        "inventory": dict(user.inventory or {}),
        "minecraft_goods_count_season": dict(user.minecraft_goods_count_season or {}),
        "rub_balance": user.rub_balance,
        "farm_minigame": dict(user.farm_minigame or {}),
    }


def _coerce_decimal_fields(data: dict[str, Any]) -> None:
    for key in ("balance", "debt", "deposit", "min_deposit", "max_loan", "rub_balance"):
        v = data.get(key)
        if isinstance(v, Decimal):
            continue
        if v is None:
            data[key] = Decimal("0.00")
        else:
            data[key] = Decimal(str(v))


@asynccontextmanager
async def session_scope() -> AsyncIterator[Any]:
    async with session_maker() as session:
        try:
            yield session
        finally:
            pass


async def get_user_data(user_id: int, data_key: str | None = None) -> Any:
    """
    Async replacement for utils/json_engine.get_user_data().
    Returns a dict compatible with the old code (Decimals + nested dicts).
    """
    lock = await _user_lock(int(user_id))
    async with lock:
        async with session_scope() as session:
            user = await orm_get_or_create_user(session, int(user_id))
            data = _user_to_dict(user)

            defaults = _default_user_dict(int(user_id))
            for k, v in defaults.items():
                data.setdefault(k, v)

            _coerce_decimal_fields(data)

            if data_key is not None:
                return data.get(data_key)
            return data


async def update_user_data(user_id: int, data: dict[str, Any]) -> None:
    """
    Async replacement for utils/json_engine.update_user_data().
    Uses per-user lock to prevent lost updates inside one process.
    """
    lock = await _user_lock(int(user_id))
    async with lock:
        payload = dict(data)
        _coerce_decimal_fields(payload)
        payload["date_update"] = int(time.time())

        async with session_scope() as session:
            await orm_get_or_create_user(session, int(user_id), username=str(payload.get("username") or ""))
            await orm_update_user_fields(
                session,
                int(user_id),
                balance=payload.get("balance"),
                debt=payload.get("debt"),
                deposit=payload.get("deposit"),
                credit_rating=int(payload.get("credit_rating") or 0),
                min_deposit=payload.get("min_deposit"),
                max_loan=payload.get("max_loan"),
                getbc_time=int(payload.get("getbc_time") or 0),
                username=str(payload.get("username") or ""),
                minecraft_username=payload.get("minecraft_username"),
                date_update=int(payload.get("date_update") or int(time.time())),
                last_interest_date=payload.get("last_interest_date"),
                inventory=payload.get("inventory") or {},
                minecraft_goods_count_season=payload.get("minecraft_goods_count_season") or {},
                rub_balance=payload.get("rub_balance"),
                farm_minigame=payload.get("farm_minigame") or {},
            )


async def get_admins_data() -> dict[str, Any]:
    async with session_scope() as session:
        data = await orm_get_singleton(session, "admins_data")
        if not data:
            return {"admins_ids": []}
        if "admins_ids" not in data:
            data["admins_ids"] = []
        return data


async def update_admins_data(data: dict[str, Any]) -> None:
    async with session_scope() as session:
        await orm_set_singleton(session, "admins_data", data)


async def get_categories_data() -> dict[str, Any]:
    async with session_scope() as session:
        return await orm_get_singleton(session, "minecraft_goods")


async def update_categories_data(data: dict[str, Any]) -> None:
    async with session_scope() as session:
        await orm_set_singleton(session, "minecraft_goods", data)


async def get_farm_data() -> dict[str, Any]:
    async with session_scope() as session:
        return await orm_get_singleton(session, "mini_game_farm")


async def update_farm_data(data: dict[str, Any]) -> None:
    async with session_scope() as session:
        await orm_set_singleton(session, "mini_game_farm", data)


async def get_donat_goods_data() -> dict[str, Any]:
    async with session_scope() as session:
        return await orm_get_singleton(session, "minecraft_donat_goods")


async def update_donat_goods_data(data: dict[str, Any]) -> None:
    async with session_scope() as session:
        await orm_set_singleton(session, "minecraft_donat_goods", data)


async def get_all_users():
    """
    Async replacement for utils/json_engine.get_all_users().
    Returns list of tuples: (user_id, user_dict)
    """
    async with session_scope() as session:
        users = await orm_list_users(session)
        out = []
        for user in users:
            out.append((int(user.id), _user_to_dict(user)))
        return out
