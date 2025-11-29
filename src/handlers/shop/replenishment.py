from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from decimal import Decimal

from common.data_for_bot import TEXTS
from handlers.components.functions import get_user_data, update_user_data, format_money
# from handlers.shop.minecraft.shop import minecraft_shop
from handlers.common_funcs import send_msg_call
from kbds.inline import get_callback_btns
from handlers.shop.minecraft.defs import ShopStates, create_minecraft_shop_keyboard, create_replenishment_keyboard, get_item_key, calculate_item_price, get_user_inventory, minecraft_shop, update_user_inventory, clear_user_inventory, add_item_to_inventory, create_inventory_keyboard, create_item_details_keyboard, create_items_keyboard, create_categories_keyboard
# Import the MinecraftShopCallback from callbacks
from handlers.components.callbacks import  MinecraftShopCallback, ShopCallback
from handlers.components.decorators import  protected_callback
from utils.json_engine import get_categories_data

replenishment_router = Router()
replenishment_router.callback_query(ShopCallback)



@replenishment_router.callback_query(ShopCallback.filter(F.action == "replenishment"))
@protected_callback
async def replenishment(callback: CallbackQuery, state: FSMContext):
    """Show user's inventory"""
    # user_id = callback.from_user.id
    # if callback_data.user_id != user_id:
    #     await callback.answer("Эта кнопка не для вас!")
    #     return
    reply_markup = await create_replenishment_keyboard(callback.from_user.id)
    await send_msg_call(callback, text=TEXTS['static']['replenishment'], reply_markup=reply_markup)