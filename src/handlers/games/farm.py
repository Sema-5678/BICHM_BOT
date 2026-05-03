from decimal import Decimal
import time
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from filters.chat_types import ChatTypeFilter

# Import functions from farm_functions
from config import FarmConfig
from utils.json_engine import get_user_data, update_user_data

from .farm_functions import (
    parse_coordinates,
    get_cell_info,
    get_user_farm_data,
    show_farm_field,
    get_plants_keyboard,
    get_plant_info,
    get_farm_data,
    # update_farm_data
)
from .farm_functions import calculate_income_per_minute


BASE_SELL_DATA = {'plant': None, 'status': None}


class FarmStates(StatesGroup):
    in_farm = State()  # Состояние, когда пользователь находится в ферме


farm_router = Router()
farm_router.message.filter(ChatTypeFilter(["private"]))


@farm_router.message(Command("farm"))
@farm_router.callback_query(F.data == "back_to_field")
async def farm_start(message: Message | CallbackQuery, state: FSMContext):
    """Handle /farm command to show the farm field"""
    await state.set_state(FarmStates.in_farm)
    await show_farm_field(message, state)


@farm_router.message(StateFilter(FarmStates.in_farm))
async def handle_cell_selection(message: Message, state: FSMContext):
    """Handle cell selection when user is in farm mode"""
    # Check if it's a command
    if message.text and message.text.startswith('/'):
        return
    
    user_id = message.from_user.id
    user_field, soil_field, field_size = get_user_farm_data(user_id)
    
    # Parse coordinates
    coords = parse_coordinates(message.text, field_size)
    if coords is None:
        await show_farm_field(
            message, 
            state,
            "Некорректный формат координат. Используйте формат: `А1`, `б3` и т.д. У вас на поле нет такой клетки"
        )
        return
    
    row, col = coords
    
    # Get and display cell info
    cell_info = get_cell_info(user_field, soil_field, row, col)
    
    # Create buttons
    buttons = []
    cell = user_field[row][col]
    
    if cell.get('plant'):
        # Add dig up button if there's a plant
        buttons.append([
            InlineKeyboardButton(
                text="🗑️ Выкопать растение", 
                callback_data=f"dig_up_{row}_{col}"
            )
        ])
    else:
        # Add buy plant button if cell is empty
        buttons.append([
            InlineKeyboardButton(
                text="🌱 Купить растение", 
                callback_data=f"buy_plant_{row}_{col}"
            )
        ])
    
    # Add back button
    buttons.append([
        InlineKeyboardButton(
            text="↩️ Назад к полю", 
            callback_data="back_to_field"
        )
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(cell_info, reply_markup=keyboard, parse_mode="Markdown")


@farm_router.callback_query(F.data.startswith("buy_plant_"))
async def handle_buy_plant(callback: CallbackQuery, state: FSMContext):
    """Show available plants for purchase"""
    await callback.answer()
    
    # Extract row and column from callback data
    _, _, row, col = callback.data.split('_')
    row, col = int(row), int(col)
    
    # Get user's farm data
    user_id = callback.from_user.id
    user_field, soil_field, field_size = get_user_farm_data(user_id)
    
    # Check if the cell is still empty
    if user_field[row][col].get('plant'):
        await callback.message.answer("Эта клетка уже занята!")
        return
    
    # Show available plants
    keyboard = get_plants_keyboard(row, col)
    await callback.message.answer(
        "🌱 *Выберите растение для покупки:*\n"
        "Нажмите на растение, чтобы увидеть подробную информацию.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@farm_router.callback_query(F.data.startswith("select_plant_"))
async def handle_select_plant(callback: CallbackQuery, state: FSMContext):
    """Show details about selected plant and confirm purchase"""
    await callback.answer()
    
    # Extract plant_id, row, and column from callback data
    _, _, plant_id, row, col = callback.data.split('_')
    row, col = int(row), int(col)
    
    # Get plant info
    plant_info = get_plant_info(plant_id)
    
    # Create confirm purchase button
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Подтвердить покупку",
                callback_data=f"confirm_purchase_{plant_id}_{row}_{col}"
            ),
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data=f"back_to_plants_{row}_{col}"
            )
        ]
    ])
    
    await callback.message.edit_text(
        f"*Информация о растении:*\n\n{plant_info}\n\n"
        "Хотите купить это растение?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@farm_router.callback_query(F.data.startswith("confirm_purchase_"))
async def handle_confirm_purchase(callback: CallbackQuery, state: FSMContext):
    """Handle plant purchase confirmation"""
    await callback.answer()
    
    # Extract plant_id, row, and column from callback data
    _, _, plant_id, row, col = callback.data.split('_')
    plant_id = int(plant_id)
    row, col = int(row), int(col)
    
    user_id = callback.from_user.id
    user_data = get_user_data(user_id)
    farm_data = user_data['farm_minigame']
    user_field = farm_data.get('field', [])
    
    # Get plant price
    plant = FarmConfig.PLANT_TYPES.get(plant_id)
    if not plant:
        await callback.message.answer("Ошибка: растение не найдено")
        return
    
    # Check if user has enough money
    if user_data.get('balance', 0) < plant['cost_fc']:
        await callback.answer("❌ Недостаточно средств для покупки", show_alert=True)
        return
    
    # Deduct money and add plant
    farm_data['fc_balance'] = farm_data['fc_balance'] - plant['cost_fc']
    user_field[row][col] = {'plant': plant_id, "status":"good"}
    farm_data['field'] = user_field
    
    # Recalculate income per minute
    farm_data['income_per_minute'], user_field = str(calculate_income_per_minute(user_field))
    farm_data['field'] = user_field

    
    # Save changes
    update_user_data(user_id, user_data)
    
    # Show success message
    await callback.message.answer(
        f"✅ Вы успешно посадили {plant['name']} {plant['emoji']} в клетку "
        f"{chr(ord('А') + col)}{row + 1} за {plant['cost_fc']} FC"
    )
    
    # Show updated cell
    await show_farm_field(callback, state)


@farm_router.callback_query(F.data.startswith("dig_up_"))
async def handle_dig_up_plant(callback: CallbackQuery, state: FSMContext):
    """Handle plant removal from a cell"""
    await callback.answer()
    
    # Extract row and column from callback data
    _, _, row, col = callback.data.split('_')
    row, col = int(row), int(col)
    
    # Get user's data
    user_id = callback.from_user.id
    user_data = get_user_data(user_id)
    farm_data = user_data['farm_minigame']
    user_field, soil_field, field_size = get_user_farm_data(user_id)
    
    # Check if there's actually a plant to remove
    if not user_field[row][col].get('plant'):
        await callback.answer("На этой клетке нет растения!")
        return
    
    # Remove the plant
    plant_name = FarmConfig.PLANT_TYPES.get(user_field[row][col]['plant'], {}).get('name', 'растение')
    user_field[row][col] = BASE_SELL_DATA
    
    # Update user data
    user_data['farm_minigame']['field'] = user_field
    update_user_data(user_id, user_data)
    
    # Recalculate income per minute
    income_per_minute, field = calculate_income_per_minute(user_field)
    user_data['farm_minigame']['income_per_minute'] = str(income_per_minute)
    user_data['farm_minigame']['field'] = field
    update_user_data(user_id, user_data)
    
    # Show success message and return to cell view
    await callback.answer(f"Вы выкопали {plant_name}.")
    
    # Get updated cell info
    cell_info = get_cell_info(user_field, soil_field, row, col)
    
    # Update buttons - show buy plant button now
    buttons = [
        [InlineKeyboardButton(text="🌱 Купить растение", callback_data=f"buy_plant_{row}_{col}")],
        [InlineKeyboardButton(text="↩️ Назад к полю", callback_data="back_to_field")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(cell_info, reply_markup=keyboard, parse_mode="Markdown")


@farm_router.callback_query(F.data.startswith("back_to_cell_"))
async def handle_back_to_cell(callback: CallbackQuery, state: FSMContext):
    """Return to cell view from plant selection"""
    await callback.answer()
    
    # Extract row and column from callback data
    _, _, row, col = callback.data.split('_')
    row, col = int(row), int(col)
    
    # Get user's farm data
    user_id = callback.from_user.id
    user_field, soil_field, field_size = get_user_farm_data(user_id)
    
    # Show cell info
    cell_info = get_cell_info(user_field, soil_field, row, col)
    
    # Create buttons
    buttons = []
    cell = user_field[row][col]
    
    if cell.get('plant'):
        # Add dig up button if there's a plant
        buttons.append([
            InlineKeyboardButton(
                text="🗑️ Выкопать растение", 
                callback_data=f"dig_up_{row}_{col}"
            )
        ])
    else:
        # Add buy plant button if cell is empty
        buttons.append([
            InlineKeyboardButton(
                text="🌱 Купить растение", 
                callback_data=f"buy_plant_{row}_{col}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text="↩️ Назад к полю", 
            callback_data="back_to_field"
        )
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(cell_info, reply_markup=keyboard, parse_mode="Markdown")


@farm_router.callback_query(F.data.startswith("back_to_plants_"))
async def handle_back_to_plants(callback: CallbackQuery):
    """Return to plant selection from plant details"""
    await callback.answer()
    
    # Extract row and column from callback data
    _, _, row, col = callback.data.split('_')
    row, col = int(row), int(col)
    
    # Show plants keyboard again
    keyboard = get_plants_keyboard(row, col)
    await callback.message.edit_text(
        "🌱 *Выберите растение для покупки:*\n"
        "Нажмите на растение, чтобы увидеть подробную информацию.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )









@farm_router.callback_query(F.data == "back_to_plants")
async def handle_back_to_plants(callback: CallbackQuery):
    """Return to plant selection from plant details"""
    # Extract row and column from callback data
    _, row, col = callback.data.split('_')
    
    # Show plants keyboard again
    keyboard = get_plants_keyboard(int(row), int(col))
    await callback.message.edit_reply_markup(reply_markup=keyboard)


@farm_router.callback_query(F.data == "farm_shop")
async def handle_farm_shop(callback: CallbackQuery):
    """Handle farm shop button click"""
    await callback.answer("Функционал магазина будет добавлен в ближайшее время!")


@farm_router.callback_query(F.data == "donate_shop")
async def handle_donate_shop(callback: CallbackQuery):
    """Handle donate shop button click"""
    await callback.answer("Донат магазин будет доступен в ближайшее время!")


@farm_router.callback_query(F.data == "farmer_inventory")
async def handle_farmer_inventory(callback: CallbackQuery):
    """Handle farmer's inventory button click"""
    await callback.answer("Инвентарь фермера будет доступен в ближайшее время!")


@farm_router.callback_query(F.data == "upgrade_farm")
async def handle_upgrade_farm(callback: CallbackQuery):
    """Handle farm upgrade button click"""
    user_id = callback.from_user.id
    user_data = get_user_data(user_id)
    
    # Get current field size
    farm_minigame = user_data['farm_minigame']
    field_size = farm_minigame.get('field_size', 3)
    
    # Check if can upgrade (max 9x9)
    if field_size >= 9:
        await callback.answer("Достигнут максимальный размер фермы 9x9!")
        return
    
    # Calculate upgrade cost (example: 100 * (current_size - 2))
    upgrade_cost = 10_000 * (field_size - 2)
    
    # Check if user has enough FC
    balance = Decimal(str(farm_minigame.get('fc_balance', 0)))
    if balance < upgrade_cost:
        await callback.answer(f"Недостаточно FC для улучшения! Нужно {upgrade_cost} FC.")
        return
    
    # Update user's balance
    farm_minigame['fc_balance'] = str(balance - upgrade_cost)
    
    # Increase field size
    new_size = field_size + 1
    farm_minigame['field_size'] = new_size
    
    # Initialize field if it doesn't exist
    if 'field' not in farm_minigame:
        farm_minigame['field'] = []
    
    # Add new row if needed
    if len(farm_minigame['field']) < new_size:
        farm_minigame['field'].append([BASE_SELL_DATA for _ in range(new_size)])
    
    # Add new column to all existing rows
    for row in user_data['farm_minigame']['field']:
        if len(row) < new_size:
            row.append(BASE_SELL_DATA)
    
    # Update user data
    update_user_data(user_id, user_data)
    
    # Show success message
    await callback.answer(f"Ферма улучшена до {new_size}x{new_size}!", show_alert=True)
    
    # Refresh farm view
    await show_farm_field(callback, None)
