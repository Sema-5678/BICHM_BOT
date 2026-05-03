from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_create_core_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column("balance", sa.Numeric(15, 2), nullable=True),
        sa.Column("debt", sa.Numeric(15, 2), nullable=True),
        sa.Column("deposit", sa.Numeric(15, 2), nullable=True),
        sa.Column("credit_rating", sa.Integer(), nullable=False),
        sa.Column("min_deposit", sa.Numeric(15, 2), nullable=True),
        sa.Column("max_loan", sa.Numeric(15, 2), nullable=True),
        sa.Column("getbc_time", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("minecraft_username", sa.String(length=16), nullable=True),
        sa.Column("date_create", sa.BigInteger(), nullable=False),
        sa.Column("date_update", sa.BigInteger(), nullable=False),
        sa.Column("last_interest_date", sa.String(length=32), nullable=True),
        sa.Column("inventory", sa.JSON(), nullable=False),
        sa.Column("minecraft_goods_count_season", sa.JSON(), nullable=False),
        sa.Column("rub_balance", sa.Numeric(15, 2), nullable=True),
        sa.Column("farm_minigame", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("credit_rating >= 0", name="ck_users_credit_rating_min"),
        sa.CheckConstraint("credit_rating <= 100", name="ck_users_credit_rating_max"),
        sa.CheckConstraint("balance >= 0", name="ck_users_balance_nonneg"),
        sa.CheckConstraint("debt >= 0", name="ck_users_debt_nonneg"),
        sa.CheckConstraint("deposit >= 0", name="ck_users_deposit_nonneg"),
        sa.CheckConstraint("min_deposit >= 0", name="ck_users_min_deposit_nonneg"),
        sa.CheckConstraint("max_loan >= 0", name="ck_users_max_loan_nonneg"),
        sa.CheckConstraint("rub_balance >= 0", name="ck_users_rub_balance_nonneg"),
    )

    op.create_table(
        "singletons",
        sa.Column("key", sa.String(length=64), primary_key=True),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("singletons")
    op.drop_table("users")

