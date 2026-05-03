from __future__ import annotations

import time
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import SingletonKV, User


async def orm_get_user(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def orm_get_or_create_user(
    session: AsyncSession,
    user_id: int,
    *,
    username: str = "",
) -> User:
    user = await orm_get_user(session, user_id)
    if user is not None:
        if username and user.username != username:
            user.username = username
            user.date_update = int(time.time())
            await session.commit()
        return user

    now = int(time.time())
    user = User(
        id=user_id,
        username=username or "",
        date_create=now,
        date_update=now,
        last_interest_date=None,
        inventory={},
        minecraft_goods_count_season={},
        farm_minigame={},
    )
    session.add(user)
    await session.commit()
    return user


async def orm_update_user_fields(session: AsyncSession, user_id: int, **fields: Any) -> None:
    fields["date_update"] = int(time.time())
    await session.execute(update(User).where(User.id == user_id).values(**fields))
    await session.commit()


async def orm_delete_user(session: AsyncSession, user_id: int) -> None:
    user = await orm_get_user(session, user_id)
    if user is None:
        return
    await session.delete(user)
    await session.commit()


async def orm_get_singleton(session: AsyncSession, key: str) -> dict[str, Any]:
    result = await session.execute(select(SingletonKV).where(SingletonKV.key == key))
    row = result.scalar_one_or_none()
    return dict(row.value) if row else {}


async def orm_set_singleton(session: AsyncSession, key: str, value: dict[str, Any]) -> None:
    result = await session.execute(select(SingletonKV).where(SingletonKV.key == key))
    row = result.scalar_one_or_none()
    if row:
        row.value = value
    else:
        session.add(SingletonKV(key=key, value=value))
    await session.commit()


async def orm_delete_singleton(session: AsyncSession, key: str) -> None:
    result = await session.execute(select(SingletonKV).where(SingletonKV.key == key))
    row = result.scalar_one_or_none()
    if row is None:
        return
    await session.delete(row)
    await session.commit()


async def orm_get_admins_ids(session: AsyncSession) -> list[int]:
    data = await orm_get_singleton(session, "admins_data")
    ids = data.get("admins_ids", [])
    return [int(x) for x in ids] if isinstance(ids, list) else []


async def orm_set_admins_ids(session: AsyncSession, admin_ids: list[int]) -> None:
    await orm_set_singleton(session, "admins_data", {"admins_ids": [int(x) for x in admin_ids]})


async def orm_list_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User))
    return list(result.scalars().all())
