import logging
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
from config import MIN_POSITIVE_NUM
from handlers.common_funcs import send_msg_call
from handlers.components.functions import get_user_data, update_user_data, format_money
from kbds.inline import get_callback_btns

# Import the ShopCallback from callbacks
from handlers.components.callbacks import MinecraftShopCallback, ShopCallback
from handlers.components.decorators import  protected_callback
from utils.json_engine import get_categories_data
from utils.rcon import rcon_manager



logger = logging.getLogger(__name__)



# def create_bc_callback_data( user_id: int, action=None, category_id=None, item_id=None, quantity=0):
#     callback_data=ShopCallback(
#             user_id=user_id,
#             action=action,
#             shop_type="BC",
#             category_id=category_id,
#             item_id=item_id,
#             quantity=quantity
#         ).pack()

#     return callback_data


# States for shop navigation
class ShopStates(StatesGroup):
    viewing_categories = State()
    viewing_items = State()
    viewing_item = State()
    viewing_inventory = State()
    awaiting_minecraft_username = State()



# Helper functions
def get_item_key(category_id: str, item_id: str) -> str:
    """Generate a unique key for an item in inventory"""
    return f"{category_id}_{item_id}"

def calculate_item_price(base_price: Decimal, price_growth: Decimal, quantity: int, start_index: int = 0) -> Decimal:
    """Calculate total price for items with price growth starting from start_index"""
    if quantity <= 0:
        return Decimal('0')

    base = Decimal(str(base_price))
    growth = Decimal(str(price_growth))

    total_price = Decimal('0')
    for i in range(start_index, start_index + quantity):
        total_price += base * (growth ** i)

    return total_price.quantize(MIN_POSITIVE_NUM)

def get_user_inventory(user_id: int) -> dict:
    """Get user's inventory"""
    inventory = get_user_data(user_id, 'inventory')
    return inventory

def update_user_inventory(user_id: int, inventory: dict):
    """Update user's inventory"""
    user_data = get_user_data(user_id)
    user_data['inventory'] = inventory
    update_user_data(user_id, user_data)

def clear_user_inventory(user_id: int):
    """Clear user's inventory"""
    user_data = get_user_data(user_id)
    if 'inventory' in user_data:
        user_data['inventory'] = {}
        update_user_data(user_id, user_data)
        return True
    return False

def add_item_to_inventory(user_id: int, category_id: str, item_id: str, quantity: int = 1):
    """Add item to user's inventory"""
    user_data = get_user_data(user_id)
    if 'inventory' not in user_data:
        user_data['inventory'] = {}
    
    item_key = f"{category_id}_{item_id}"
    if item_key in user_data['inventory']:
        user_data['inventory'][item_key] += quantity
    else:
        user_data['inventory'][item_key] = quantity
    
    update_user_data(user_id, user_data)
    return True












# Shop handlers
async def create_shop_keyboard(user_id: int, back_callback: str = None):
    """Create shop keyboard with user-specific callbacks"""
    builder = InlineKeyboardBuilder()
    
    # Shop main menu buttons
    builder.button(
        text="🎮 Майнкрафт",
        callback_data=MinecraftShopCallback(
            user_id=user_id,
            action="show_shop",
            # shop_type="BC",
            # category_id="",
            # item_id="",
            # quantity=0
        ).pack()
    )

    builder.button(
        text="💸 Пополнить",
        callback_data=ShopCallback(
            user_id=user_id,
            action="replenishment",
            # shop_type="BC",
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





# Shop handlers
async def create_minecraft_shop_keyboard(user_id: int, back_callback: str = None):
    """Create shop keyboard with user-specific callbacks"""
    builder = InlineKeyboardBuilder()
    
    # Shop main menu buttons
    builder.button(
        text="🛒 Предметы",
        callback_data=MinecraftShopCallback(
            user_id=user_id,
            action="show_categories",
            # shop_type="BC",
            # category_id="",
            # item_id="",
            # quantity=0
        ).pack()
    )

    builder.button(
        text="🤡 Пранки",
        callback_data=MinecraftShopCallback(
            user_id=user_id,
            action="show_pranks",
            # shop_type="BC",
            # category_id="",
            # item_id="",
            # quantity=0
        ).pack()
    )
    
    builder.button(
        text="🎒 Мой инвентарь",
        callback_data=MinecraftShopCallback(
            user_id=user_id,
            action="show_inventory",
            # shop_type=Т,
            # category_id="",
            # item_id="",
            # quantity=0
        ).pack()
    )

    builder.button(
        text="🔙 Назад",
        callback_data=ShopCallback(
            user_id=user_id,
            action="show_shop",
            
        ).pack()
    )

    # builder.button(
    #     text="🛒 Предметы за Рубли",
    #     callback_data=MinecraftShopCallback(
    #         user_id=user_id,
    #         action="show_categories",
    #         # shop_type="rub",
    #         # category_id="",
    #         # item_id="",
    #         # quantity=0
    #     ).pack()
    # )
    
    if back_callback:
        builder.button(
            text="🔙 Назад",
            callback_data=back_callback
        )
    
    builder.adjust(1)
    return builder.as_markup()



async def create_replenishment_keyboard(user_id: int):
    """Create shop keyboard with user-specific callbacks"""
    builder = InlineKeyboardBuilder()
    

    builder.button(
        text="🔙 Назад",
        callback_data=ShopCallback(
            user_id=user_id,
            action="show_shop",
            
        ).pack()
    )

    
    builder.adjust(1)
    return builder.as_markup()



async def minecraft_shop(callback: CallbackQuery | Message, state: FSMContext=None):
    """Show Minecraft shop main menu"""
    # await state.set_state(ShopStates.viewing_categories)
    # await state.update_data(user_id=callback.from_user.id)
    categories = get_categories_data()
    
    if not categories:
        await callback.answer("В магазине пока нет товаров.")
        return
    
    keyboard = await create_minecraft_shop_keyboard(callback.from_user.id)
    text =( "🛒 <b>Minecraft Магазин</b>\n\n"
            "Выберите категорию товаров:")
    await send_msg_call(callback, text=text, reply_markup=keyboard, parse_mode='HTML')





async def create_inventory_keyboard(user_id: int):
    """Create keyboard for inventory actions"""
    builder = InlineKeyboardBuilder()
    
    # Transfer items button
    builder.button(
        text="🎮 Выдать предметы в игру",
        callback_data=MinecraftShopCallback(
            user_id=user_id,
            action="transfer_items",
            
            category_id="",
            item_id="",
            quantity=0
        ).pack()
    )
    
    # Back to shop button
    builder.button(
        text="🛒 В магазин",
        callback_data=MinecraftShopCallback(
            user_id=user_id,
            action="show_shop",
            
            category_id="",
            item_id="",
            quantity=0
        ).pack()
    )
    
    builder.adjust(1, 1)
    return builder.as_markup()



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
            callback_data=MinecraftShopCallback(
                user_id=user_id,
                action="purchase_item",
                
                category_id=category_id,
                item_id=item_id,
                quantity=quantity
            ).pack()
        )
    
    # Back button
    builder.button(
        text="🔙 Назад",
        callback_data=MinecraftShopCallback(
            user_id=user_id,
            action="show_category_items",
            
            category_id=category_id,
            item_id="",
            quantity=0
        ).pack()
    )
    
    builder.adjust(3, 1)
    return builder.as_markup()




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
            callback_data=MinecraftShopCallback(
                user_id=user_id,
                action="show_item",
                
                category_id=category_id,
                item_id=item_id,
                quantity=0
            ).pack()
        )
    
    # Back button
    builder.button(
        text="🔙 Назад",
        callback_data=MinecraftShopCallback(
            user_id=user_id,
            action="show_categories",
            
            category_id="",
            item_id="",
            quantity=0
        ).pack()
    )
    
    builder.adjust(1)
    return builder.as_markup()




async def create_categories_keyboard(user_id: int):
    """Create categories keyboard with user-specific callbacks"""
    builder = InlineKeyboardBuilder()
    categories = get_categories_data()
    
    for cat_id, cat_data in categories.items():
        builder.button(
            text=cat_data['name'],
            callback_data=MinecraftShopCallback(
                user_id=user_id,
                action="show_category_items",
                
                category_id=cat_id,
                item_id="",
                quantity=0
            ).pack()
        )
    
    # Back button
    builder.button(
        text="🔙 Назад",
        callback_data=MinecraftShopCallback(
            user_id=user_id,
            action="show_shop",
            
            category_id="",
            item_id="",
            quantity=0
        ).pack()
    )
    
    builder.adjust(1)
    return builder.as_markup()














async def give_player_items_in_minecraft(minecraft_username: str, inventory: dict) -> bool:
    """Transfer all items from inventory to Minecraft player via RCON"""
    categories = get_categories_data()
    success = True
    err_text = ''
    
    for item_key, amount in inventory.items():
        try:
            category_id, item_id = item_key.split('_')
            category = categories.get(category_id)
            if not category:
                continue
                
            item = category['elems'].get(item_id)
            if not item:
                continue
                
            result = await rcon_manager.give_item(
                minecraft_username,
                item['minecraft_id'],
                amount
            )
            
            if "No player was found" in result:
                success = False
                err_text = 'игрок не на сервере'
                break

            elif 'Gave ' in result and 'to ' in result and minecraft_username in result:
                success = True
                continue
            
            else:
                success = False
                err_text = f'Ошибка {result}'
                break
                
        except Exception as e:
            # print(f"Error transferring item: {e}")
            err_text = f'непредвиденная ошибка, сообщите администратору {e}'
            success = False
            break
            
    return success, err_text


