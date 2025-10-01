import asyncio
import logging

from aiogram import F, types, Router, Bot
from aiogram.filters import CommandStart, StateFilter,  Command
from aiogram.fsm.state import State, StatesGroup,  default_state

from aiogram.fsm.context import FSMContext
from filters.chat_types import ChatTypeFilter
from handlers.components.functions import start_msg
from kbds.inline import  get_callback_btns
from aiogram.types import CallbackQuery, Message
from common.data_for_bot import TEXTS


user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(["private"]))


logger = logging.getLogger(__name__)


GROUP_CHAT_ID = -1002603387943




@user_private_router.message(CommandStart(), StateFilter("*"))
async def start_cmd(message: Message, state: FSMContext):
    await message.answer(text=TEXTS["static"]["prompts"]["enter_city"])


@user_private_router.callback_query(F.data == "start")
@user_private_router.message(CommandStart(), StateFilter("*"))
async def start_cmd(event, state: FSMContext):
    await start_msg(event, state)


