

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
# from handlers.shop.minecraft import minecraft_shop_router
from handlers.shop.minecraft.items_shop import minecraft_items_shop_router
from handlers.shop.minecraft.inventory import minecraft_inventory_router
from handlers.shop.minecraft.custom_shop import minecraft_custom_shop_router
from kbds.inline import get_callback_btns
from handlers.shop.minecraft.defs import ShopStates, create_shop_keyboard, get_item_key, calculate_item_price, get_user_inventory, minecraft_shop, update_user_inventory, clear_user_inventory, add_item_to_inventory
# Import the ShopCallback from callbacks
from handlers.components.callbacks import MinecraftShopCallback, ShopCallback
from handlers.components.decorators import  protected_callback
from utils.json_engine import get_categories_data





# shop_router = Router()
# shop_router.include_router(minecraft_shop_router)


minecraft_shop_router = Router()




@minecraft_shop_router.callback_query(MinecraftShopCallback.filter(F.action == "show_shop"))
@protected_callback
async def show_shop(callback: CallbackQuery, state: FSMContext):
    """Show Minecraft shop main menu"""
    await minecraft_shop(callback, state)






minecraft_shop_router.include_router(minecraft_items_shop_router)
minecraft_shop_router.include_router(minecraft_inventory_router)
minecraft_shop_router.include_router(minecraft_custom_shop_router)


