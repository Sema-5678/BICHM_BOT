

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
from handlers.shop.minecraft import minecraft_shop_router
from kbds.inline import get_callback_btns
from handlers.shop.minecraft.defs import ShopStates, create_shop_keyboard, get_item_key, calculate_item_price, get_user_inventory, update_user_inventory, clear_user_inventory, add_item_to_inventory
# Import the ShopCallback from callbacks
from handlers.components.callbacks import MinecraftShopCallback, ShopCallback
from handlers.components.decorators import  protected_callback
from utils.json_engine import get_categories_data





shop_router = Router()
shop_router.include_router(minecraft_shop_router)




# Shop handlers
async def create_shop_keyboard(user_id: int, back_callback: str = None):
    """Create shop keyboard with user-specific callbacks"""
    builder = InlineKeyboardBuilder()
    
    # Shop main menu buttons
    builder.button(
        text="🛒 Предметы за BC",
        callback_data=ShopCallback(
            user_id=user_id,
            action="show_categories",
            shop_type="BC",
            # category_id="",
            # item_id="",
            # quantity=0
        ).pack()
    )
    
    builder.button(
        text="🎒 Мой инвентарь",
        callback_data=ShopCallback(
            user_id=user_id,
            action="minecraft_inventory",
            # shop_type=Т,
            # category_id="",
            # item_id="",
            # quantity=0
        ).pack()
    )

    builder.button(
        text="🛒 Предметы за Рубли",
        callback_data=ShopCallback(
            user_id=user_id,
            action="show_categories",
            shop_type="rub",
            # category_id="",
            # item_id="",
            # quantity=0
        ).pack()
    )
    
    if back_callback:
        builder.button(
            text="🔙 Назад",
            callback_data=back_callback
        )
    
    builder.adjust(1)
    return builder.as_markup()







@shop_router.callback_query(ShopCallback.filter(F.action == "show_shop"))
# @shop_router.callback_query(F.data == "minecraft_shop")
@protected_callback
async def minecraft_shop(callback: CallbackQuery | Message, state: FSMContext):
    """Show Minecraft shop main menu"""
    await state.set_state(ShopStates.viewing_categories)
    await state.update_data(user_id=callback.from_user.id)
    categories = get_categories_data()
    
    if not categories:
        await callback.answer("В магазине пока нет товаров.")
        return
    
    keyboard = await create_shop_keyboard(callback.from_user.id)
    
    if isinstance(callback, CallbackQuery):
        await callback.message.edit_text(
            "🛒 <b>Minecraft Магазин</b>\n\n"
            "Выберите категорию товаров:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    else:
        await callback.answer(
            "🛒 <b>Minecraft Магазин</b>\n\n"
            "Выберите категорию товаров:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )