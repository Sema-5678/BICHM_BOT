from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Literal

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Path, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, update

from database.engine import create_db, session_maker
from database.models import User
from database.orm import (
    orm_get_or_create_user,
    orm_get_singleton,
    orm_set_singleton,
    orm_update_user_fields,
)

logger = logging.getLogger("api")


class _Model(BaseModel):
    model_config = ConfigDict(json_encoders={Decimal: lambda v: str(v)})


# -------------------------
# Auth
# -------------------------


def _require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    expected = os.getenv("API_KEY")
    if not expected:
        raise HTTPException(status_code=500, detail="API_KEY is not set on server")
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")


# -------------------------
# Helpers
# -------------------------


def _quantize_money(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _validate_amount(v: Decimal) -> Decimal:
    try:
        v = Decimal(v)
    except (InvalidOperation, TypeError):
        raise HTTPException(status_code=422, detail="Invalid decimal amount")
    return _quantize_money(v)


def _max_bc() -> Decimal:
    try:
        return Decimal(str(int(os.getenv("MAX_BALANCE", "1000000"))))
    except Exception:
        return Decimal("1000000")


def _max_rub() -> Decimal:
    try:
        return Decimal(str(int(os.getenv("MAX_RUB_BALANCE", "100000000"))))
    except Exception:
        return Decimal("100000000")


def _user_to_card(user: User) -> "UserCardOut":
    return UserCardOut(
        id=int(user.id),
        username=user.username or "",
        minecraft_username=user.minecraft_username,
        balance=Decimal(str(user.balance)),
        rub_balance=Decimal(str(user.rub_balance)),
        deposit=Decimal(str(user.deposit)),
        debt=Decimal(str(user.debt)),
        credit_rating=int(user.credit_rating),
        date_create=int(user.date_create),
        date_update=int(user.date_update),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _default_farm_minigame() -> dict[str, Any]:
    now = int(time.time())
    field = [
        [{"plant": None, "status": None}, {"plant": None, "status": None}, {"plant": None, "status": None}],
        [{"plant": None, "status": None}, {"plant": None, "status": None}, {"plant": None, "status": None}],
        [{"plant": None, "status": None}, {"plant": None, "status": None}, {"plant": None, "status": None}],
    ]
    return {
        "field": field,
        "fc_balance": 0,
        "last_care_day": None,
        "missed_days": 0,
        "field_size": 3,
        "inventory": {},
        "boosts": {},
        "last_visit": now,
    }


# -------------------------
# Schemas
# -------------------------


class BalanceChangeIn(_Model):
    amount: Decimal = Field(..., description="Delta (default) or target value, up to 2 decimals.")
    mode: str = Field("delta", description="delta | set")


class BalanceChangeOut(_Model):
    user_id: int
    currency: str
    mode: str
    amount: Decimal
    new_balance: Decimal


class UserCardOut(_Model):
    id: int
    username: str
    minecraft_username: str | None
    balance: Decimal
    rub_balance: Decimal
    deposit: Decimal
    debt: Decimal
    credit_rating: int
    date_create: int
    date_update: int
    created_at: datetime
    updated_at: datetime


class UsersListOut(_Model):
    items: list[UserCardOut]
    limit: int
    offset: int
    total: int


class UserBalancesOut(_Model):
    id: int
    balance: Decimal
    rub_balance: Decimal
    deposit: Decimal
    debt: Decimal
    credit_rating: int


class UserPatchIn(_Model):
    username: str | None = None
    minecraft_username: str | None = None


class InventoryOut(_Model):
    id: int
    inventory: dict[str, Any]


class FarmOut(_Model):
    id: int
    farm_minigame: dict[str, Any]


class InventoryChangeIn(_Model):
    category_id: str
    item_id: str
    quantity: int = Field(..., ge=1, le=10_000)


class StatsUsersCountOut(_Model):
    users: int


class StatsTopItem(_Model):
    id: int
    total: Decimal
    balance: Decimal
    deposit: Decimal


class StatsTopOut(_Model):
    items: list[StatsTopItem]


class StatsAgg(_Model):
    sum: Decimal
    avg: Decimal


class StatsSummaryOut(_Model):
    bc: StatsAgg
    rub: StatsAgg
    deposit: StatsAgg
    debt: StatsAgg


class StatsActiveOut(_Model):
    days: int
    active_users: int


class InventoryTopItem(_Model):
    item_key: str
    total_qty: int


class InventoryTopOut(_Model):
    items: list[InventoryTopItem]


class ConfigOut(_Model):
    key: str
    value: dict[str, Any]


class ConfigPatchOp(_Model):
    op: str
    category_id: str | None = None
    item_id: str | None = None
    field: str | None = None
    value: Any | None = None
    data: dict[str, Any] | None = None


# -------------------------
# Core operations
# -------------------------


async def _apply_balance_change(
    telegram_id: int,
    *,
    field_name: str,
    currency: str,
    payload: BalanceChangeIn,
) -> BalanceChangeOut:
    amount = _validate_amount(payload.amount)
    mode = payload.mode.strip().lower()
    if mode not in {"delta", "set"}:
        raise HTTPException(status_code=422, detail="mode must be 'delta' or 'set'")

    max_value = _max_bc() if field_name == "balance" else _max_rub()

    async with session_maker() as session:
        await orm_get_or_create_user(session, telegram_id)

        result = await session.execute(select(User).where(User.id == telegram_id))
        user = result.scalar_one()
        current = Decimal(str(getattr(user, field_name)))

        new_value = amount if mode == "set" else (current + amount)
        if new_value < 0:
            new_value = Decimal("0.00")
        if new_value > max_value:
            new_value = _quantize_money(max_value)
        new_value = _quantize_money(new_value)

        await session.execute(update(User).where(User.id == telegram_id).values({field_name: new_value}))
        await session.commit()

        return BalanceChangeOut(
            user_id=telegram_id,
            currency=currency,
            mode=mode,
            amount=amount,
            new_balance=new_value,
        )


# -------------------------
# App
# -------------------------


app = FastAPI(title="Bot API", version="0.1.0")


@app.on_event("startup")
async def _startup() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    try:
        from dotenv import find_dotenv, load_dotenv  # type: ignore
    except Exception:
        logger.warning("python-dotenv is not available; .env will not be loaded")
    else:
        load_dotenv(find_dotenv())

    await create_db()


# -------------------------
# 1) Health / Meta
# -------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    try:
        async with session_maker() as session:
            await session.execute(select(func.count()).select_from(User))
    except Exception:
        raise HTTPException(status_code=503, detail="db is not ready")
    return {"db": "ok", "migrations": "unknown"}


@app.get("/version")
async def version() -> dict[str, str]:
    return {"api_version": app.version or "0.0.0", "alembic_head": "0001_create_core_tables"}


# -------------------------
# Existing balance endpoints
# -------------------------


@app.post(
    "/v1/users/{telegram_id}/balance/bc",
    response_model=BalanceChangeOut,
    dependencies=[Depends(_require_api_key)],
)
async def change_balance_bc(
    telegram_id: int = Path(..., ge=1),
    payload: BalanceChangeIn = ...,
) -> BalanceChangeOut:
    return await _apply_balance_change(telegram_id, field_name="balance", currency="BC", payload=payload)


@app.post(
    "/v1/users/{telegram_id}/balance/rub",
    response_model=BalanceChangeOut,
    dependencies=[Depends(_require_api_key)],
)
async def change_balance_rub(
    telegram_id: int = Path(..., ge=1),
    payload: BalanceChangeIn = ...,
) -> BalanceChangeOut:
    return await _apply_balance_change(telegram_id, field_name="rub_balance", currency="RUB", payload=payload)


# -------------------------
# 2) Users (read)
# -------------------------


@app.get(
    "/v1/users/{telegram_id}",
    response_model=UserCardOut,
    dependencies=[Depends(_require_api_key)],
)
async def get_user(telegram_id: int = Path(..., ge=1)) -> UserCardOut:
    async with session_maker() as session:
        result = await session.execute(select(User).where(User.id == telegram_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return _user_to_card(user)


@app.get(
    "/v1/users/{telegram_id}/balances",
    response_model=UserBalancesOut,
    dependencies=[Depends(_require_api_key)],
)
async def get_user_balances(telegram_id: int = Path(..., ge=1)) -> UserBalancesOut:
    async with session_maker() as session:
        result = await session.execute(select(User).where(User.id == telegram_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return UserBalancesOut(
            id=int(user.id),
            balance=Decimal(str(user.balance)),
            rub_balance=Decimal(str(user.rub_balance)),
            deposit=Decimal(str(user.deposit)),
            debt=Decimal(str(user.debt)),
            credit_rating=int(user.credit_rating),
        )


@app.get(
    "/v1/users",
    response_model=UsersListOut,
    dependencies=[Depends(_require_api_key)],
)
async def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort: Literal["balance", "rub_balance", "date_create", "date_update"] = Query("date_update"),
    order: Literal["asc", "desc"] = Query("desc"),
) -> UsersListOut:
    sort_col = getattr(User, sort)
    sort_col = sort_col.asc() if order == "asc" else sort_col.desc()

    async with session_maker() as session:
        total = await session.scalar(select(func.count()).select_from(User))
        result = await session.execute(select(User).order_by(sort_col).offset(offset).limit(limit))
        items = [_user_to_card(u) for u in result.scalars().all()]
        return UsersListOut(items=items, limit=limit, offset=offset, total=int(total or 0))


@app.get(
    "/v1/users/search",
    response_model=UsersListOut,
    dependencies=[Depends(_require_api_key)],
)
async def search_users(
    id: int | None = Query(default=None, ge=1),
    username: str | None = Query(default=None, min_length=1),
    minecraft_username: str | None = Query(default=None, min_length=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> UsersListOut:
    stmt = select(User)
    if id is not None:
        stmt = stmt.where(User.id == id)
    if username:
        stmt = stmt.where(User.username.ilike(f"%{username}%"))
    if minecraft_username:
        stmt = stmt.where(User.minecraft_username.ilike(f"%{minecraft_username}%"))

    async with session_maker() as session:
        total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
        result = await session.execute(stmt.offset(offset).limit(limit))
        items = [_user_to_card(u) for u in result.scalars().all()]
        return UsersListOut(items=items, limit=limit, offset=offset, total=int(total or 0))


@app.get(
    "/v1/users/{telegram_id}/inventory",
    response_model=InventoryOut,
    dependencies=[Depends(_require_api_key)],
)
async def get_user_inventory_api(telegram_id: int = Path(..., ge=1)) -> InventoryOut:
    async with session_maker() as session:
        result = await session.execute(select(User).where(User.id == telegram_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return InventoryOut(id=int(user.id), inventory=dict(user.inventory or {}))


@app.get(
    "/v1/users/{telegram_id}/farm",
    response_model=FarmOut,
    dependencies=[Depends(_require_api_key)],
)
async def get_user_farm_api(telegram_id: int = Path(..., ge=1)) -> FarmOut:
    async with session_maker() as session:
        result = await session.execute(select(User).where(User.id == telegram_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return FarmOut(id=int(user.id), farm_minigame=dict(user.farm_minigame or {}))


# -------------------------
# 3) Users (write)
# -------------------------


@app.patch(
    "/v1/users/{telegram_id}",
    response_model=UserCardOut,
    dependencies=[Depends(_require_api_key)],
)
async def patch_user(
    telegram_id: int = Path(..., ge=1),
    payload: UserPatchIn = ...,
) -> UserCardOut:
    fields: dict[str, Any] = {}
    if payload.username is not None:
        fields["username"] = payload.username
    if payload.minecraft_username is not None or payload.minecraft_username is None:
        fields["minecraft_username"] = payload.minecraft_username

    if not fields:
        raise HTTPException(status_code=422, detail="No fields to update")

    async with session_maker() as session:
        await orm_get_or_create_user(session, telegram_id)
        await orm_update_user_fields(session, telegram_id, **fields)
        result = await session.execute(select(User).where(User.id == telegram_id))
        return _user_to_card(result.scalar_one())


@app.post(
    "/v1/users/{telegram_id}/inventory/add",
    response_model=InventoryOut,
    dependencies=[Depends(_require_api_key)],
)
async def inventory_add(
    telegram_id: int = Path(..., ge=1),
    payload: InventoryChangeIn = ...,
) -> InventoryOut:
    key = f"{payload.category_id}_{payload.item_id}"
    async with session_maker() as session:
        await orm_get_or_create_user(session, telegram_id)
        result = await session.execute(select(User).where(User.id == telegram_id))
        user = result.scalar_one()
        inv = dict(user.inventory or {})
        inv[key] = int(inv.get(key, 0)) + int(payload.quantity)
        await orm_update_user_fields(session, telegram_id, inventory=inv)
        return InventoryOut(id=telegram_id, inventory=inv)


@app.post(
    "/v1/users/{telegram_id}/inventory/remove",
    response_model=InventoryOut,
    dependencies=[Depends(_require_api_key)],
)
async def inventory_remove(
    telegram_id: int = Path(..., ge=1),
    payload: InventoryChangeIn = ...,
) -> InventoryOut:
    key = f"{payload.category_id}_{payload.item_id}"
    async with session_maker() as session:
        await orm_get_or_create_user(session, telegram_id)
        result = await session.execute(select(User).where(User.id == telegram_id))
        user = result.scalar_one()
        inv = dict(user.inventory or {})
        cur = int(inv.get(key, 0))
        new_val = cur - int(payload.quantity)
        if new_val <= 0:
            inv.pop(key, None)
        else:
            inv[key] = new_val
        await orm_update_user_fields(session, telegram_id, inventory=inv)
        return InventoryOut(id=telegram_id, inventory=inv)


@app.post(
    "/v1/users/{telegram_id}/inventory/clear",
    response_model=InventoryOut,
    dependencies=[Depends(_require_api_key)],
)
async def inventory_clear(telegram_id: int = Path(..., ge=1)) -> InventoryOut:
    async with session_maker() as session:
        await orm_get_or_create_user(session, telegram_id)
        inv: dict[str, Any] = {}
        await orm_update_user_fields(session, telegram_id, inventory=inv)
        return InventoryOut(id=telegram_id, inventory=inv)


@app.post(
    "/v1/users/{telegram_id}/farm/reset",
    response_model=FarmOut,
    dependencies=[Depends(_require_api_key)],
)
async def farm_reset(
    telegram_id: int = Path(..., ge=1),
    confirm: bool = Body(False, embed=True),
) -> FarmOut:
    if confirm is not True:
        raise HTTPException(status_code=422, detail="confirm=true is required")
    async with session_maker() as session:
        await orm_get_or_create_user(session, telegram_id)
        farm = _default_farm_minigame()
        await orm_update_user_fields(session, telegram_id, farm_minigame=farm)
        return FarmOut(id=telegram_id, farm_minigame=farm)


# -------------------------
# 4) Stats / Analytics
# -------------------------


@app.get(
    "/v1/stats/users/count",
    response_model=StatsUsersCountOut,
    dependencies=[Depends(_require_api_key)],
)
async def stats_users_count() -> StatsUsersCountOut:
    async with session_maker() as session:
        total = await session.scalar(select(func.count()).select_from(User))
        return StatsUsersCountOut(users=int(total or 0))


@app.get(
    "/v1/stats/balances/top",
    response_model=StatsTopOut,
    dependencies=[Depends(_require_api_key)],
)
async def stats_top(limit: int = Query(10, ge=1, le=100)) -> StatsTopOut:
    async with session_maker() as session:
        stmt = select(User).order_by((User.balance + User.deposit).desc()).limit(limit)
        result = await session.execute(stmt)
        items: list[StatsTopItem] = []
        for u in result.scalars().all():
            total = Decimal(str(u.balance)) + Decimal(str(u.deposit))
            items.append(
                StatsTopItem(
                    id=int(u.id),
                    total=_quantize_money(total),
                    balance=Decimal(str(u.balance)),
                    deposit=Decimal(str(u.deposit)),
                )
            )
        return StatsTopOut(items=items)


@app.get(
    "/v1/stats/balances/summary",
    response_model=StatsSummaryOut,
    dependencies=[Depends(_require_api_key)],
)
async def stats_summary() -> StatsSummaryOut:
    async with session_maker() as session:
        bc_sum, bc_avg = await session.one(select(func.sum(User.balance), func.avg(User.balance)))
        rub_sum, rub_avg = await session.one(select(func.sum(User.rub_balance), func.avg(User.rub_balance)))
        dep_sum, dep_avg = await session.one(select(func.sum(User.deposit), func.avg(User.deposit)))
        debt_sum, debt_avg = await session.one(select(func.sum(User.debt), func.avg(User.debt)))

        def agg(sum_v, avg_v) -> StatsAgg:
            return StatsAgg(
                sum=_quantize_money(Decimal(str(sum_v or 0))),
                avg=_quantize_money(Decimal(str(avg_v or 0))),
            )

        return StatsSummaryOut(
            bc=agg(bc_sum, bc_avg),
            rub=agg(rub_sum, rub_avg),
            deposit=agg(dep_sum, dep_avg),
            debt=agg(debt_sum, debt_avg),
        )


@app.get(
    "/v1/stats/active",
    response_model=StatsActiveOut,
    dependencies=[Depends(_require_api_key)],
)
async def stats_active(days: int = Query(7, ge=1, le=365)) -> StatsActiveOut:
    cutoff = int(time.time()) - days * 86400
    async with session_maker() as session:
        total = await session.scalar(select(func.count()).where(User.date_update >= cutoff))
        return StatsActiveOut(days=days, active_users=int(total or 0))


@app.get(
    "/v1/stats/inventory/top-items",
    response_model=InventoryTopOut,
    dependencies=[Depends(_require_api_key)],
)
async def stats_inventory_top_items(limit: int = Query(50, ge=1, le=200)) -> InventoryTopOut:
    async with session_maker() as session:
        result = await session.execute(select(User.inventory))
        counter: dict[str, int] = {}
        for inv in result.scalars().all():
            if not isinstance(inv, dict):
                continue
            for k, v in inv.items():
                try:
                    counter[str(k)] = counter.get(str(k), 0) + int(v)
                except Exception:
                    continue
        items = sorted(counter.items(), key=lambda kv: kv[1], reverse=True)[:limit]
        return InventoryTopOut(items=[InventoryTopItem(item_key=k, total_qty=v) for k, v in items])


# -------------------------
# 5) Singletons / Config (minecraft_goods, mini_game_farm)
# -------------------------


@app.get(
    "/v1/config/minecraft_goods",
    response_model=ConfigOut,
    dependencies=[Depends(_require_api_key)],
)
async def get_minecraft_goods() -> ConfigOut:
    async with session_maker() as session:
        value = await orm_get_singleton(session, "minecraft_goods")
        return ConfigOut(key="minecraft_goods", value=value)


@app.put(
    "/v1/config/minecraft_goods",
    response_model=ConfigOut,
    dependencies=[Depends(_require_api_key)],
)
async def put_minecraft_goods(payload: dict[str, Any] = Body(...)) -> ConfigOut:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="body must be an object")
    async with session_maker() as session:
        await orm_set_singleton(session, "minecraft_goods", payload)
        return ConfigOut(key="minecraft_goods", value=payload)


@app.patch(
    "/v1/config/minecraft_goods",
    response_model=ConfigOut,
    dependencies=[Depends(_require_api_key)],
)
async def patch_minecraft_goods(op: ConfigPatchOp) -> ConfigOut:
    async with session_maker() as session:
        goods = await orm_get_singleton(session, "minecraft_goods")
        if not isinstance(goods, dict):
            goods = {}

        if op.op == "set_category":
            if not op.category_id or not isinstance(op.data, dict):
                raise HTTPException(status_code=422, detail="category_id and data required")
            goods[str(op.category_id)] = op.data
        elif op.op == "set_item":
            if not op.category_id or not op.item_id or not isinstance(op.data, dict):
                raise HTTPException(status_code=422, detail="category_id, item_id and data required")
            cat = goods.setdefault(str(op.category_id), {})
            if not isinstance(cat, dict):
                raise HTTPException(status_code=422, detail="category must be object")
            elems = cat.setdefault("elems", {})
            if not isinstance(elems, dict):
                raise HTTPException(status_code=422, detail="category.elems must be object")
            elems[str(op.item_id)] = op.data
        elif op.op == "set_item_field":
            if not op.category_id or not op.item_id or not op.field:
                raise HTTPException(status_code=422, detail="category_id, item_id and field required")
            cat = goods.get(str(op.category_id))
            if not isinstance(cat, dict):
                raise HTTPException(status_code=404, detail="category not found")
            elems = cat.get("elems")
            if not isinstance(elems, dict):
                raise HTTPException(status_code=422, detail="category.elems must be object")
            item = elems.get(str(op.item_id))
            if not isinstance(item, dict):
                raise HTTPException(status_code=404, detail="item not found")
            item[str(op.field)] = op.value
        elif op.op == "delete_item":
            if not op.category_id or not op.item_id:
                raise HTTPException(status_code=422, detail="category_id and item_id required")
            cat = goods.get(str(op.category_id))
            if not isinstance(cat, dict):
                raise HTTPException(status_code=404, detail="category not found")
            elems = cat.get("elems")
            if not isinstance(elems, dict):
                raise HTTPException(status_code=422, detail="category.elems must be object")
            elems.pop(str(op.item_id), None)
        else:
            raise HTTPException(status_code=422, detail="unsupported op")

        await orm_set_singleton(session, "minecraft_goods", goods)
        return ConfigOut(key="minecraft_goods", value=goods)


@app.get(
    "/v1/config/mini_game_farm",
    response_model=ConfigOut,
    dependencies=[Depends(_require_api_key)],
)
async def get_mini_game_farm() -> ConfigOut:
    async with session_maker() as session:
        value = await orm_get_singleton(session, "mini_game_farm")
        return ConfigOut(key="mini_game_farm", value=value)


@app.put(
    "/v1/config/mini_game_farm",
    response_model=ConfigOut,
    dependencies=[Depends(_require_api_key)],
)
async def put_mini_game_farm(payload: dict[str, Any] = Body(...)) -> ConfigOut:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="body must be an object")
    async with session_maker() as session:
        await orm_set_singleton(session, "mini_game_farm", payload)
        return ConfigOut(key="mini_game_farm", value=payload)

