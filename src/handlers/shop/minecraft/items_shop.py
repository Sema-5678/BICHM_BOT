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
from handlers.shop.minecraft.defs import ShopStates, create_minecraft_shop_keyboard, get_item_key, calculate_item_price, get_user_inventory, minecraft_shop, update_user_inventory, clear_user_inventory, add_item_to_inventory, create_inventory_keyboard, create_item_details_keyboard, create_items_keyboard, create_categories_keyboard
# Import the MinecraftShopCallback from callbacks
from handlers.components.callbacks import  MinecraftShopCallback, ShopCallback
from handlers.components.decorators import  protected_callback
from utils.sqlite_storage import get_categories_data

minecraft_items_shop_router = Router()
# minecraft_items_shop_router.callback_query(ShopCallback.filter(F.shop_type == "0"))
minecraft_items_shop_router.callback_query.filter(
    MinecraftShopCallback.filter(F.shop_type == "items")
)

# minecraft_items_shop_router.callback_query(MinecraftShopCallback.filter(F.shop_type == "items"))




# @minecraft_items_shop_router.callback_query(MinecraftShopCallback.filter(F.action == "show_shop"))
# @protected_callback
# async def minecraft_shop(callback: CallbackQuery | Message, state: FSMContext):
#     """Show Minecraft shop main menu"""
#     await state.set_state(ShopStates.viewing_categories)
#     await state.update_data(user_id=callback.from_user.id)
#     # categories = get_categories_data()
    
#     # if not categories:
#     #     await callback.answer("В магазине пока нет товаров.")
#     #     return
    
#     keyboard = await create_minecraft_shop_keyboard(callback.from_user.id)
#     text = ("🛒 <b>Minecraft Магазин</b>\n\n"
#             "Выберите категорию товаров:")

#     await send_msg_call(callback, text=text, reply_markup=keyboard)
    
#     # if isinstance(callback, CallbackQuery):
#     #     await callback.message.edit_text(
#     #         text,
#     #         reply_markup=keyboard,
#     #         parse_mode='HTML'
#     #     )
#     # else:
#     #     await callback.answer(
#     #         text,
#     #         reply_markup=keyboard,
#     #         parse_mode='HTML' 
#     #     )



@minecraft_items_shop_router.callback_query(MinecraftShopCallback.filter(F.action == "show_categories"))
# @minecraft_items_shop_router.callback_query(F.data == "minecraft_categories")
@protected_callback
async def show_minecraft_categories(callback: CallbackQuery, state: FSMContext, callback_data: MinecraftShopCallback = None):
    """Show all Minecraft item categories"""
    print(callback_data)
    user_id = callback.from_user.id
    
    if callback_data:
        if callback_data.user_id != user_id:
            await callback.answer("Эта кнопка не для вас!")
            return
        user_id = callback_data.user_id
    
    await state.set_state(ShopStates.viewing_categories)
    
    await callback.message.edit_text(
        "📦 <b>Категории предметов</b>\n\n"
        "Выберите категорию:",
        reply_markup=await create_categories_keyboard(user_id),
        parse_mode='HTML'
    )

@minecraft_items_shop_router.callback_query(MinecraftShopCallback.filter(F.action == "show_category_items"))
@protected_callback
async def show_category_items(callback: CallbackQuery, state: FSMContext, callback_data: MinecraftShopCallback):
    """Show items in a specific category"""
    user_id = callback.from_user.id
    category_id = callback_data.category_id
    categories = await get_categories_data()
    category = categories.get(category_id)

    if not category:
        await callback.answer("Категория не найдена")
        return
    
    await state.update_data(current_category=category_id)
    await state.set_state(ShopStates.viewing_items)
    
    keyboard = await create_items_keyboard(user_id, category_id)
    if not keyboard:
        await callback.answer("Ошибка загрузки предметов")
        return
    
    await callback.message.edit_text(
        f"<b>{category['name']}</b>\n\n"
        f"Выберите предмет:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@minecraft_items_shop_router.callback_query(MinecraftShopCallback.filter(F.action == "show_item"))
@protected_callback
async def show_item_details(callback: CallbackQuery, state: FSMContext, callback_data: MinecraftShopCallback):
    """Show item details and purchase options"""
    user_id = callback.from_user.id
    category_id = callback_data.category_id
    item_id = callback_data.item_id
    
    categories = await get_categories_data()
    category = categories.get(category_id)
    
    if not category:
        await callback.answer("Категория не найдена")
        return
    
    item = category['elems'].get(item_id)
    if not item:
        await callback.answer("Предмет не найден")
        return
    
    currency = item['currency']  # Теперь будет ошибка если ключа нет
    currency_text = " BC" if currency == "bc" else "💵 Рубли"
    
    user_data = await get_user_data(user_id)
    
    # Get user balance for the current currency
    if currency == 'bc':
        balance = user_data['balance']
    else:
        balance = user_data['rub_balance']
    
    balance_text = f"{format_money(balance, currency)}"
    
    await state.update_data(current_item=item_id, current_category=category_id, current_currency=currency)
    await state.set_state(ShopStates.viewing_item)
    
    season_counts = user_data.get('minecraft_goods_count_season', {})
    item_key = get_item_key(category_id, item_id)
    previous_purchases = int(season_counts.get(item_key, 0))

    # Calculate prices and build buttons with error handling
    price_lines = []
    builder = InlineKeyboardBuilder()
    quantities = [1, 3, 10, 64, 128, 256]
    
    for qty in quantities:
        try:
            price = calculate_item_price(item['base_price'], item['price_growth'], qty, previous_purchases)
            emoji = "💵" if qty == 1 else "💰" if qty == 3 else "💎"
            price_lines.append(f"{emoji} Цена за {qty}: {format_money(price, currency)}")
            
            # Add purchase button for this quantity
            builder.button(
                text=f"+ {qty}",
                callback_data=MinecraftShopCallback(
                    user_id=user_id,
                    action="purchase_item",
                    shop_type="items",
                    category_id=category_id,
                    item_id=item_id,
                    quantity=qty
                ).pack()
            )
        except:
            continue
    
    # Add back button
    builder.button(
        text="⬅ Назад",
        callback_data=MinecraftShopCallback(
            user_id=user_id,
            shop_type="items",
            action="show_category_items",
            category_id=category_id
        ).pack()
    )
    
    builder.adjust(3, repeat=True)
    
    # Build message text with balance info
    text_lines = [
        f"{item['emoji']} <b>{item['name']}</b>",
        f"📝 {item['description']}",
        "",
        f"🌟 <b>Валюта покупки:</b> {currency_text}",
        f"💰 <b>Ваш баланс:</b> {balance_text}",
        ""
    ] + price_lines + [
        "",
        f"📦 Макс. в стаке: {item['max_stack']}",
        f"🆔 Minecraft ID: {item.get('minecraft_id', 'Не указан')}"
    ]
    
    await callback.message.edit_text(
        "\n".join(text_lines),
        reply_markup=builder.as_markup(),
        parse_mode='HTML'
    )

@minecraft_items_shop_router.callback_query(MinecraftShopCallback.filter(F.action == "purchase_item"))
@protected_callback
async def buy_item(callback: CallbackQuery, state: FSMContext, callback_data: MinecraftShopCallback):
    """Handle item purchase"""
    user_id = callback.from_user.id
    category_id = callback_data.category_id
    item_id = callback_data.item_id
    quantity = callback_data.quantity
    
    state_data = await state.get_data()
    currency = state_data.get('current_currency')
    
    categories = await get_categories_data()
    category = categories.get(category_id)
    
    if not category:
        await callback.answer("Категория не найдена")
        return
    
    item = category['elems'].get(item_id)
    if not item:
        await callback.answer("Предмет не найден")
        return
    
    user_data = await get_user_data(user_id)
    season_counts = user_data.setdefault('minecraft_goods_count_season', {})
    item_key = get_item_key(category_id, item_id)
    previous_purchases = int(season_counts.get(item_key, 0))

    total_price = calculate_item_price(item['base_price'], item['price_growth'], quantity, previous_purchases)
    
    # Check balance based on currency
    if currency == 'rub':
        if user_data['rub_balance'] < total_price:
            await callback.answer("❌ Недостаточно рублей")
            return
    else:
        if user_data['balance'] < total_price:
            await callback.answer("❌ Недостаточно BC")
            return
    
    # Deduct money based on currency
    if currency == 'rub':
        user_data['rub_balance'] = user_data['rub_balance'] - total_price
    else:
        user_data['balance'] = user_data['balance'] - total_price
    
    season_counts[item_key] = previous_purchases + quantity
    await update_user_data(user_id, user_data)
    
    add_item_to_inventory(user_id, category_id, item_id, quantity)
    
    currency_text = "рублей" if currency == "rub" else "BC"
    await callback.answer(f"✅ Успешно куплено {quantity}x {item['name']} за {format_money(total_price)} {currency_text}")
    
    # Update the message to show the item was purchased
    await show_item_details(callback, state, callback_data)
