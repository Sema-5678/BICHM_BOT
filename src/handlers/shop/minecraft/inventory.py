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
from handlers.shop.minecraft.defs import ShopStates, create_minecraft_shop_keyboard, get_item_key, calculate_item_price, get_user_inventory, give_player_items_in_minecraft, minecraft_shop, update_user_inventory, clear_user_inventory, add_item_to_inventory, create_inventory_keyboard
# Import the MinecraftShopCallback from callbacks
from handlers.components.callbacks import  MinecraftShopCallback
from handlers.components.decorators import  protected_callback
from utils.rcon import rcon_manager
from utils.json_engine import get_categories_data

minecraft_inventory_router = Router()
minecraft_inventory_router.callback_query(MinecraftShopCallback)



@minecraft_inventory_router.callback_query(MinecraftShopCallback.filter(F.action == "show_inventory"))
@protected_callback
async def show_inventory(callback: CallbackQuery, state: FSMContext):
    """Show user's inventory"""
    user_id = callback.from_user.id
    # if callback_data.user_id != user_id:
    #     await callback.answer("Эта кнопка не для вас!")
    #     return
    
    inventory = get_user_inventory(user_id)
    categories = get_categories_data()
    
    if not inventory:
        keyboard = await create_inventory_keyboard(user_id)
        await callback.message.edit_text(
            "🎒 <b>Ваш инвентарь пуст</b>\n\n"
            "Отправляйтесь в магазин, чтобы что-нибудь купить!",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return
    
    # Group items by category
    items_by_category = {}
    for item_key, quantity in inventory.items():
        if "_" in item_key:
            category_id, item_id = item_key.split("_", 1)
            if category_id not in items_by_category:
                items_by_category[category_id] = []
            items_by_category[category_id].append((item_id, quantity))
    
    # Build inventory text
    inventory_text = "🎒 <b>Ваш инвентарь</b>\n\n"
    
    for category_id, items in items_by_category.items():
        category = categories.get(category_id, {})
        category_name = category.get('name', 'Неизвестная категория')
        inventory_text += f"<b>{category_name}</b>\n"
        
        for item_id, quantity in items:
            item = category.get('elems', {}).get(item_id, {})
            item_name = item.get('name', 'Неизвестный предмет')
            item_emoji = item.get('emoji', '❓')
            inventory_text += f"{item_emoji} {item_name}: {quantity} шт.\n"
        
        inventory_text += "\n"
    
    keyboard = await create_inventory_keyboard(user_id)
    await callback.message.edit_text(
        inventory_text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )



@minecraft_inventory_router.callback_query(MinecraftShopCallback.filter(F.action == "transfer_items"))
@protected_callback
async def transfer_items_to_game(callback: CallbackQuery, state: FSMContext):
    """Transfer items to the game"""
    user_id = callback.from_user.id
    # if callback_data.user_id != user_id:
    #     await callback.answer("Эта кнопка не для вас!")
    #     return
    

    user_data = get_user_data(user_id)
    minecraft_username = user_data.get('minecraft_username')
    
    if not minecraft_username:
        # Ask for Minecraft username if not set
        await state.set_state(ShopStates.awaiting_minecraft_username)
        await callback.message.edit_text(
            "🔹 <b>Введите ваш ник в Minecraft:</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=MinecraftShopCallback(
                        user_id=user_id,
                        action="show_inventory",
                        
                        category_id="",
                        item_id="",
                        quantity=0
                    ).pack()
                )
            ]])
        )
        return
    
    inventory = get_user_inventory(user_id)
    if not inventory:
        await callback.answer("Ваш инвентарь пуст!")
        return



    clear_user_inventory(user_id)
    await callback.answer("Отправка предметов в игру...")
    await transfer_items_to_minecraft(callback.message, user_id,minecraft_username, inventory)
    

@minecraft_inventory_router.message(ShopStates.awaiting_minecraft_username)
async def process_minecraft_username(message: Message, state: FSMContext):
    """Process Minecraft username input"""
    user_id = message.from_user.id
    minecraft_username = message.text.strip()
    
    user_data = get_user_data(user_id)
    user_data['minecraft_username'] = minecraft_username
    update_user_data(user_id, user_data)
    
    # Clear the state
    await state.clear()
    await message.answer(f"✅ Minecraft ник {minecraft_username} успешно сохранён!")
    
    # # Get the inventory to transfer
    # inventory = get_user_inventory(user_id)
    # if not inventory:
    #     await message.answer("❌ Ваш инвентарь пуст!")
    #     return
    
    # await transfer_items_to_minecraft(message, user_id,minecraft_username, inventory)
    
    # await minecraft_shop(message, state)



























async def transfer_items_to_minecraft(message: Message, user_id: int, minecraft_username: str, inventory: dict) -> bool:

    success, err_text = await give_player_items_in_minecraft(minecraft_username, inventory)

    if success:
        await message.answer("✅ Все предметы успешно переданы в игру!")
        # await show_inventory(callback, state)
        await minecraft_shop(message)

    else:
        await message.answer(f"❌ {err_text}")
    