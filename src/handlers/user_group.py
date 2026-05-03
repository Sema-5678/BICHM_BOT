import asyncio

from aiogram import F, Bot, types, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, MessageOriginUnion
from handlers.bank_handlers import bank_router
from handlers.games import games_router

from filters.chat_types import ChatTypeFilter

user_group_router = Router()


user_group_router = Router()
user_group_router.include_router(bank_router)
user_group_router.include_router(games_router)


user_group_router.message.filter(ChatTypeFilter(["group", "supergroup"]))
user_group_router.edited_message.filter(ChatTypeFilter(["group", "supergroup"]))
import random
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from filters.chat_types import ChatTypeFilter

games_router = Router()
games_router.message.filter(ChatTypeFilter(["group", "supergroup"]))


