from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("credit_rating >= 0", name="ck_users_credit_rating_min"),
        CheckConstraint("credit_rating <= 100", name="ck_users_credit_rating_max"),
        CheckConstraint("balance >= 0", name="ck_users_balance_nonneg"),
        CheckConstraint("debt >= 0", name="ck_users_debt_nonneg"),
        CheckConstraint("deposit >= 0", name="ck_users_deposit_nonneg"),
        CheckConstraint("min_deposit >= 0", name="ck_users_min_deposit_nonneg"),
        CheckConstraint("max_loan >= 0", name="ck_users_max_loan_nonneg"),
        CheckConstraint("rub_balance >= 0", name="ck_users_rub_balance_nonneg"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)

    balance: Mapped[Decimal] = mapped_column(Numeric(15, 2, asdecimal=True), default=Decimal("60.00"), nullable=False)
    debt: Mapped[Decimal] = mapped_column(Numeric(15, 2, asdecimal=True), default=Decimal("0.00"), nullable=False)
    deposit: Mapped[Decimal] = mapped_column(Numeric(15, 2, asdecimal=True), default=Decimal("0.00"), nullable=False)
    credit_rating: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    min_deposit: Mapped[Decimal] = mapped_column(Numeric(15, 2, asdecimal=True), default=Decimal("0.00"), nullable=False)
    max_loan: Mapped[Decimal] = mapped_column(Numeric(15, 2, asdecimal=True), default=Decimal("0.00"), nullable=False)

    getbc_time: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    username: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    minecraft_username: Mapped[str | None] = mapped_column(String(16), nullable=True)

    date_create: Mapped[int] = mapped_column(BigInteger, nullable=False)
    date_update: Mapped[int] = mapped_column(BigInteger, nullable=False)

    last_interest_date: Mapped[str | None] = mapped_column(String(32), nullable=True)

    inventory: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    minecraft_goods_count_season: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    rub_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2, asdecimal=True), default=Decimal("0.00"), nullable=False)
    farm_minigame: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class SingletonKV(Base):
    """
    Универсальная "таблица-файл" для одиночных JSON-структур, которые раньше лежали в отдельных файлах:
    - admins_data.json
    - minecraft_goods.json
    - mini_game_farm.json
    - minecraft_donat_goods.json
    """

    __tablename__ = "singletons"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
