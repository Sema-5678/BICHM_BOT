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
from handlers.components.functions import get_user_data, update_user_data, format_money
from kbds.inline import get_callback_btns

# Import the ShopCallback from callbacks
from handlers.components.callbacks import ShopCallback
from handlers.components.decorators import  protected_callback
from utils.json_engine import get_categories_data



logger = logging.getLogger(__name__)



def create_bc_callback_data( user_id: int, action=None, category_id=None, item_id=None, quantity=0):
    callback_data=ShopCallback(
            user_id=user_id,
            action=action,
            shop_type="BC",
            category_id=category_id,
            item_id=item_id,
            quantity=quantity
        ).pack()

    return callback_data


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

    return total_price.quantize(Decimal('0.01'))

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