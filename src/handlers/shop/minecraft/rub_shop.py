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
from handlers.shop.minecraft.defs import ShopStates, create_shop_keyboard, get_item_key, calculate_item_price, get_user_inventory, update_user_inventory, clear_user_inventory, add_item_to_inventory
from kbds.inline import get_callback_btns

# Import the ShopCallback from callbacks
from handlers.components.callbacks import ShopCallback
from handlers.components.decorators import  protected_callback
from utils.json_engine import get_categories_data

minecraft_shop_rub_router = Router()
minecraft_shop_rub_router.callback_query(ShopCallback.filter(F.action == "show_shop"))


@minecraft_shop_rub_router.callback_query(ShopCallback.filter(F.action == "show_shop"))
# @minecraft_shop_rub_router.callback_query(F.data == "minecraft_shop")
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

async def create_categories_keyboard(user_id: int):
    """Create categories keyboard with user-specific callbacks"""
    builder = InlineKeyboardBuilder()
    categories = get_categories_data()
    
    for cat_id, cat_data in categories.items():
        builder.button(
            text=cat_data['name'],
            callback_data=ShopCallback(
                user_id=user_id,
                action="show_category_items",
                shop_type="minecraft",
                category_id=cat_id,
                item_id="",
                quantity=0
            ).pack()
        )
    
    # Back button
    builder.button(
        text="🔙 Назад",
        callback_data=ShopCallback(
            user_id=user_id,
            action="show_shop",
            shop_type="minecraft",
            category_id="",
            item_id="",
            quantity=0
        ).pack()
    )
    
    builder.adjust(1)
    return builder.as_markup()

@minecraft_shop_rub_router.callback_query(ShopCallback.filter(F.action == "show_categories"))
@minecraft_shop_rub_router.callback_query(F.data == "minecraft_categories")
async def show_minecraft_categories(callback: CallbackQuery, state: FSMContext, callback_data: ShopCallback = None):
    """Show all Minecraft item categories"""
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

async def create_items_keyboard(user_id: int, category_id: str):
    """Create items keyboard for a specific category"""
    builder = InlineKeyboardBuilder()
    categories = get_categories_data()
    category = categories.get(category_id)
    
    if not category:
        return None
    
    items = category.get('elems', {})
    
    for item_id, item_data in items.items():
        builder.button(
            text=f"{item_data['emoji']} {item_data['name']}",
            callback_data=ShopCallback(
                user_id=user_id,
                action="show_item",
                shop_type="minecraft",
                category_id=category_id,
                item_id=item_id,
                quantity=0
            ).pack()
        )
    
    # Back button
    builder.button(
        text="🔙 Назад",
        callback_data=ShopCallback(
            user_id=user_id,
            action="show_categories",
            shop_type="minecraft",
            category_id="",
            item_id="",
            quantity=0
        ).pack()
    )
    
    builder.adjust(1)
    return builder.as_markup()

@minecraft_shop_rub_router.callback_query(ShopCallback.filter(F.action == "show_category_items"))
@protected_callback
async def show_category_items(callback: CallbackQuery, state: FSMContext, callback_data: ShopCallback):
    """Show items in a specific category"""
    user_id = callback.from_user.id
    category_id = callback_data.category_id
    categories = get_categories_data()
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
        f"📦 <b>{category['name']}</b>\n\n"
        f"Выберите предмет:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

async def create_item_details_keyboard(user_id: int, category_id: str, item_id: str):
    """Create keyboard for item details with purchase options"""
    builder = InlineKeyboardBuilder()
    categories = get_categories_data()
    category = categories.get(category_id)
    
    if not category:
        return None
        
    item = category['elems'].get(item_id)
    if not item:
        return None
    
    # Add purchase buttons
    for quantity, emoji in [(1, "1️⃣"), (3, "3️⃣"), (10, "🔟")]:
        builder.button(
            text=f"{emoji} Купить {quantity}",
            callback_data=ShopCallback(
                user_id=user_id,
                action="purchase_item",
                shop_type="minecraft",
                category_id=category_id,
                item_id=item_id,
                quantity=quantity
            ).pack()
        )
    
    # Back button
    builder.button(
        text="🔙 Назад",
        callback_data=ShopCallback(
            user_id=user_id,
            action="show_category_items",
            shop_type="minecraft",
            category_id=category_id,
            item_id="",
            quantity=0
        ).pack()
    )
    
    builder.adjust(3, 1)
    return builder.as_markup()

@minecraft_shop_rub_router.callback_query(ShopCallback.filter(F.action == "show_item"))
@protected_callback
async def show_item_details(callback: CallbackQuery, state: FSMContext, callback_data: ShopCallback):
    """Show item details and purchase options"""
    user_id = callback.from_user.id
    category_id = callback_data.category_id
    item_id = callback_data.item_id
    
    categories = get_categories_data()
    category = categories.get(category_id)
    
    if not category:
        await callback.answer("Категория не найдена")
        return
    
    item = category['elems'].get(item_id)
    if not item:
        await callback.answer("Предмет не найден")
        return
    
    await state.update_data(current_item=item_id, current_category=category_id)
    await state.set_state(ShopStates.viewing_item)
    
    user_data = get_user_data(user_id)
    season_counts = user_data.get('minecraft_goods_count_season', {})
    item_key = get_item_key(category_id, item_id)
    previous_purchases = int(season_counts.get(item_key, 0))

    # Calculate prices for different quantities
    price_1 = calculate_item_price(item['base_price'], item['price_growth'], 1, previous_purchases)
    price_3 = calculate_item_price(item['base_price'], item['price_growth'], 3, previous_purchases)
    price_10 = calculate_item_price(item['base_price'], item['price_growth'], 10, previous_purchases)
    
    text = (
        f"🔹 <b>{item['name']} {item['emoji']}</b>\n\n"
        f"📝 {item['description']}\n\n"
        f"💵 Цена за 1: {format_money(price_1)}\n"
        f"💰 Цена за 3: {format_money(price_3)}\n"
        f"💎 Цена за 10: {format_money(price_10)}\n\n"
        f"📦 Макс. в стаке: {item['max_stack']}\n"
        f"🆔 Minecraft ID: {item.get('minecraft_id', 'Не указан')}"
    )
    
    keyboard = await create_item_details_keyboard(user_id, category_id, item_id)
    if not keyboard:
        await callback.answer("Ошибка загрузки информации о предмете")
        return
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@minecraft_shop_rub_router.callback_query(ShopCallback.filter(F.action == "purchase_item"))
@protected_callback
async def buy_item(callback: CallbackQuery, state: FSMContext, callback_data: ShopCallback):
    """Handle item purchase"""
    user_id = callback.from_user.id
    category_id = callback_data.category_id
    item_id = callback_data.item_id
    quantity = callback_data.quantity
    
    categories = get_categories_data()
    category = categories.get(category_id)
    
    if not category:
        await callback.answer("Категория не найдена")
        return
    
    item = category['elems'].get(item_id)
    if not item:
        await callback.answer("Предмет не найден")
        return
    
    user_data = get_user_data(user_id)
    season_counts = user_data.setdefault('minecraft_goods_count_season', {})
    item_key = get_item_key(category_id, item_id)
    previous_purchases = int(season_counts.get(item_key, 0))

    total_price = calculate_item_price(item['base_price'], item['price_growth'], quantity, previous_purchases)
    
    if user_data['balance'] < total_price:
        await callback.answer("❌ Недостаточно средств")
        return
    
    # Deduct money and add item to inventory
    user_data['balance'] = user_data['balance'] - total_price
    season_counts[item_key] = previous_purchases + quantity
    update_user_data(user_id, user_data)
    
    add_item_to_inventory(user_id, category_id, item_id, quantity)
    
    # Show success message
    await callback.answer(f"✅ Успешно куплено {quantity}x {item['name']} за {format_money(total_price)}")
    
    # Update the message to show the item was purchased
    await show_item_details(callback, state, callback_data)

async def create_inventory_keyboard(user_id: int):
    """Create keyboard for inventory actions"""
    builder = InlineKeyboardBuilder()
    
    # Transfer items button
    builder.button(
        text="🎮 Выдать предметы в игру",
        callback_data=ShopCallback(
            user_id=user_id,
            action="transfer_items",
            shop_type="minecraft",
            category_id="",
            item_id="",
            quantity=0
        ).pack()
    )
    
    # Back to shop button
    builder.button(
        text="🛒 В магазин",
        callback_data=ShopCallback(
            user_id=user_id,
            action="show_shop",
            shop_type="minecraft",
            category_id="",
            item_id="",
            quantity=0
        ).pack()
    )
    
    builder.adjust(1, 1)
    return builder.as_markup()

# @minecraft_shop_rub_router.callback_query(ShopCallback.filter(F.action == "show_inventory"))
# @protected_callback
# async def show_inventory(callback: CallbackQuery, state: FSMContext, callback_data: ShopCallback):
#     """Show user's inventory"""
#     user_id = callback.from_user.id
#     if callback_data.user_id != user_id:
#         await callback.answer("Эта кнопка не для вас!")
#         return
    
#     inventory = get_user_inventory(user_id)
#     categories = get_categories_data()
    
#     if not inventory:
#         keyboard = await create_inventory_keyboard(user_id)
#         await callback.message.edit_text(
#             "🎒 <b>Ваш инвентарь пуст</b>\n\n"
#             "Отправляйтесь в магазин, чтобы что-нибудь купить!",
#             reply_markup=keyboard,
#             parse_mode='HTML'
#         )
#         return
    
#     # Group items by category
#     items_by_category = {}
#     for item_key, quantity in inventory.items():
#         if "_" in item_key:
#             category_id, item_id = item_key.split("_", 1)
#             if category_id not in items_by_category:
#                 items_by_category[category_id] = []
#             items_by_category[category_id].append((item_id, quantity))
    
#     # Build inventory text
#     inventory_text = "🎒 <b>Ваш инвентарь</b>\n\n"
    
#     for category_id, items in items_by_category.items():
#         category = categories.get(category_id, {})
#         category_name = category.get('name', 'Неизвестная категория')
#         inventory_text += f"<b>📁 {category_name}</b>\n"
        
#         for item_id, quantity in items:
#             item = category.get('elems', {}).get(item_id, {})
#             item_name = item.get('name', 'Неизвестный предмет')
#             item_emoji = item.get('emoji', '❓')
#             inventory_text += f"{item_emoji} {item_name}: {quantity} шт.\n"
        
#         inventory_text += "\n"
    
#     keyboard = await create_inventory_keyboard(user_id)
#     await callback.message.edit_text(
#         inventory_text,
#         reply_markup=keyboard,
#         parse_mode='HTML'
#     )

@minecraft_shop_rub_router.callback_query(ShopCallback.filter(F.action == "transfer_items"))
@protected_callback
async def transfer_items_to_game(callback: CallbackQuery, state: FSMContext, callback_data: ShopCallback):
    """Transfer items to the game"""
    user_id = callback.from_user.id
    # if callback_data.user_id != user_id:
    #     await callback.answer("Эта кнопка не для вас!")
    #     return
    
    inventory = get_user_inventory(user_id)
    
    if not inventory:
        await callback.answer("Ваш инвентарь пуст!")
        return
    
    # Here you would implement the actual transfer logic to your game
    # For now, we'll just simulate it
    
    # Get the Minecraft username from user data
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
                    callback_data=ShopCallback(
                        user_id=user_id,
                        action="minecraft_inventory",
                        shop_type="minecraft",
                        category_id="",
                        item_id="",
                        quantity=0
                    ).pack()
                )
            ]])
        )
        await callback.answer()
        return
    
    # Clear the inventory after successful transfer
    clear_user_inventory(user_id)
    
    # Notify user of successful transfer
    await callback.answer("✅ Предметы успешно переданы в игру!")
    
    # Show inventory again (which should now be empty)
    await show_inventory(callback, state, callback_data)

@minecraft_shop_rub_router.message(ShopStates.awaiting_minecraft_username)
async def process_minecraft_username(message: Message, state: FSMContext):
    """Process Minecraft username input"""
    user_id = message.from_user.id
    minecraft_username = message.text.strip()
    
    # Update user data with Minecraft username
    user_data = get_user_data(user_id)
    user_data['minecraft_username'] = minecraft_username
    update_user_data(user_id, user_data)
    
    # Clear the state
    await state.clear()
    
    # Get the inventory to transfer
    inventory = get_user_inventory(user_id)
    if not inventory:
        await message.answer("❌ Ваш инвентарь пуст!")
        return
    
    # Here you would implement the actual transfer logic to your game
    # For now, we'll just simulate it
    
    # Clear the inventory after successful transfer
    clear_user_inventory(user_id)
    
    # Notify user of successful transfer
    await message.answer(
        f"✅ Предметы успешно переданы игроку {minecraft_username} в игру!"
    )
    
    # Show the shop menu
    await minecraft_shop(message, state)

@minecraft_shop_rub_router.callback_query(F.data == "minecraft_inventory")
async def show_inventory(callback: CallbackQuery, state: FSMContext):
    """Show user's inventory"""
    inventory = get_user_inventory(callback.from_user.id)
    categories = get_categories_data()
    
    if not inventory:
        await callback.message.edit_text(
            "🎒 <b>Ваш инвентарь пуст</b>\n\n"
            "Здесь будут отображаться купленные вами предметы.",
            reply_markup=get_callback_btns(
                btns={"🛒 В магазин": "minecraft_shop"},
                sizes=(1,)
            ),
            parse_mode='HTML'
        )
        return
    
    # Group items by category
    items_by_category = {}
    for item_key, quantity in inventory.items():
        if quantity <= 0:
            continue
            
        category_id, item_id = item_key.split('_', 1)
        if category_id not in items_by_category:
            items_by_category[category_id] = {}
        
        items_by_category[category_id][item_id] = quantity
    
    # Build inventory text
    text = "🎒 <b>Ваш инвентарь</b>\n\n"
    
    for category_id, items in items_by_category.items():
        category = categories.get(category_id, {'name': 'Неизвестная категория'})
        text += f"📦 <b>{category['name']}</b>\n"
        
        for item_id, quantity in items.items():
            item = category.get('elems', {}).get(item_id, {'name': 'Неизвестный предмет', 'emoji': '❓'})
            text += f"  • {item['emoji']} {item['name']} ×{quantity}\n"
        
        text += "\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_callback_btns(
            btns={
                "🛒 В магазин": "minecraft_shop",
                "🎮 В игру": "minecraft_send_to_game"
            },
            sizes=(2,)
        ),
        parse_mode='HTML'
    )

# @minecraft_shop_rub_router.callback_query(F.data == "minecraft_send_to_game")
# async def send_to_game(callback: CallbackQuery, state: FSMContext):
#     """Handle sending items to the game"""
#     # This would be connected to your Minecraft server
#     # For now, just show a message
#     await callback.answer("Функция отправки в игру будет реализована позже")

# Handle back buttons
# @minecraft_shop_rub_router.callback_query(F.data == "shop")
# async def back_to_shop(callback: CallbackQuery, state: FSMContext):
#     """Go back to main shop menu"""
#     await state.clear()
#     await callback.message.edit_text(
#         "🛒 <b>Магазин</b>\n\n"
#         "Выберите категорию товаров:",
#         reply_markup=get_callback_btns(
#             btns={"🎮 Майнкрафт": "minecraft_shop"},
#             sizes=(1,)
#         ),
#         parse_mode='HTML'
#     )
