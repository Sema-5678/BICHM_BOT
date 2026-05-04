from __future__ import annotations

import logging
import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from fastapi import Depends, FastAPI, Header, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy import select, update

from database.engine import create_db, session_maker
from database.models import User
from database.orm import orm_get_or_create_user

logger = logging.getLogger("api")


class BalanceChangeIn(BaseModel):
    amount: Decimal = Field(..., description="Delta (default) or target value, up to 2 decimals.")
    mode: str = Field("delta", description="delta | set")


class BalanceChangeOut(BaseModel):
    user_id: int
    currency: str
    mode: str
    amount: Decimal
    new_balance: Decimal


def _require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    expected = os.getenv("API_KEY")
    if not expected:
        raise HTTPException(status_code=500, detail="API_KEY is not set on server")
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")


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


async def _apply_change(
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


@app.post(
    "/v1/users/{telegram_id}/balance/bc",
    response_model=BalanceChangeOut,
    dependencies=[Depends(_require_api_key)],
)
async def change_balance_bc(
    telegram_id: int = Path(..., ge=1),
    payload: BalanceChangeIn = ...,
) -> BalanceChangeOut:
    return await _apply_change(telegram_id, field_name="balance", currency="BC", payload=payload)


@app.post(
    "/v1/users/{telegram_id}/balance/rub",
    response_model=BalanceChangeOut,
    dependencies=[Depends(_require_api_key)],
)
async def change_balance_rub(
    telegram_id: int = Path(..., ge=1),
    payload: BalanceChangeIn = ...,
) -> BalanceChangeOut:
    return await _apply_change(telegram_id, field_name="rub_balance", currency="RUB", payload=payload)
