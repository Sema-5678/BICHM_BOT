from decimal import Decimal
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from filters.chat_types import ChatTypeFilter
from common.data_for_bot import TEXTS
from handlers.bank_handlers import bank_router
from handlers.shop_handlers import shop_router
from handlers.components.functions import format_money
from config import (
    TOP_RICH_COUNT,
    BLACKJACK_BET,
    AMATEUR_BLACKJACK_BET,
    BASE_ROBBERY_CHANCE,
    INTEREST_CREDIT_RATE,
    INTEREST_DEPOSIT_RATE,
)
from handlers.components.functions import get_user_data, calculate_max_loan
from handlers.games import games_router


common_router = Router()


common_router.include_router(bank_router)
common_router.include_router(games_router)
common_router.include_router(shop_router)



@common_router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(TEXTS["static"]["help_text"])


# Команда /shop теперь обрабатывается в shop_handlers.py


@common_router.message(Command("games"))
async def cmd_games(message: Message):
    text = TEXTS["bank"]["games_list"].format(
        blackjack_bet=format_money(BLACKJACK_BET),
        amateur_bet=format_money(AMATEUR_BLACKJACK_BET),
        base_robbery=BASE_ROBBERY_CHANCE,
    )
    await message.answer(text)


@common_router.message(Command("bank"))
async def cmd_bank(message: Message):
    user_data = get_user_data(message.from_user.id)
    max_loan = calculate_max_loan(user_data["credit_rating"])
    text = TEXTS["bank"]["info"].format(
        balance=format_money(user_data['balance']),
        debt=format_money(user_data['debt']),
        deposit=format_money(user_data['deposit']),
        credit_rating=user_data['credit_rating'],
        max_loan=format_money(max_loan),
        interest_credit=f"{INTEREST_CREDIT_RATE*100:.2f}",
        interest_deposit=f"{INTEREST_DEPOSIT_RATE*100:.2f}",
        top_count=TOP_RICH_COUNT,
    )
    await message.answer(text)


