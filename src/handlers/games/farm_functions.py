"""Utility functions for the farm mini-game."""
from typing import Optional, Tuple, List, Dict, Any
from decimal import Decimal
import re

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from config import FarmConfig
import time
from datetime import datetime
from utils.sqlite_storage import get_farm_data, get_user_data, update_user_data
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers.common_funcs import send_msg_call

def parse_coordinates(coord_str: str, field_size: int) -> Optional[Tuple[int, int]]:
    """Parse coordinates from string like 'A1' to (row, col) indices."""
    if not coord_str or len(coord_str) < 2:
        return None
    
    # Extract letter and number parts (case insensitive, with optional spaces)
    match = re.match(r'^\s*([А-Яа-яA-Za-z])\s*(\d+)\s*$', coord_str.strip(), re.IGNORECASE)
    if not match:
        return None
    
    letter, number = match.groups()
    
    # Convert letter to column index (A=0, Б=1, ...)
    try:
        # Try Cyrillic first
        col = ord(letter.upper()) - ord('А')
        # If not Cyrillic, try Latin
        if col < 0 or col > 32:
            col = ord(letter.upper()) - ord('A')
    except (ValueError, TypeError):
        return None
    
    # Convert number to row index (1-based to 0-based)
    try:
        row = int(number) - 1
    except (ValueError, TypeError):
        return None
    
    # Check if coordinates are within field bounds
    if 0 <= row < field_size and 0 <= col < field_size:
        return row, col
    return None


def get_cell_info(user_field: List[List[Dict]], soil_field: List[List[int]], row: int, col: int) -> str:
    """Get detailed information about a specific cell."""
    cell = user_field[row][col]
    soil_type = soil_field[row][col]
    soil_info = FarmConfig.SOIL_TYPES.get(soil_type, FarmConfig.SOIL_TYPES[1])
    
    info = f"🔍 *Информация о клетке {chr(ord('А') + col)}{row + 1}:*\n"
    info += f"🌍 *Почва:* {soil_info['name']} {soil_info['emoji']}\n"
    info += f"📊 *Множитель урожая:* {soil_info['multiplier']}x\n\n"
    
    if cell.get('plant'):
        plant_id = cell['plant']
        plant_info = FarmConfig.PLANT_TYPES.get(plant_id, {})
        
        info += f"🌱 *Растение:* {plant_info.get('name', 'Неизвестное растение')} {plant_info.get('emoji', '')}\n"
        
        if cell.get('status') == 'wilted':
            info += "⚠️ *Состояние:* Увядшее 🥀\n"
        elif cell.get('status') == 'good':
            info += "✅ *Состояние:* Растёт\n"
        else:
            info += "✅ *Состояние:* ошибка\n"
        
        if 'base_income' in plant_info:
            # Calculate income per minute
            income_per_min = Decimal(str(plant_info['base_income']))
            income_per_hour = income_per_min * 60
            income_per_day = income_per_hour * 24
            
            # Calculate final income with soil multiplier
            final_income_per_min = income_per_min * Decimal(str(soil_info['multiplier']))
            final_income_per_hour = final_income_per_min * 60
            final_income_per_day = final_income_per_hour * 24
            
            # Add neighbor bonus information if available
            if cell.get('nabor_bonus_info'):
                bonuses = []
                conflicts = []
                
                # Separate bonuses (>=1.0) and conflicts (<1.0)
                for bonus_info in cell['nabor_bonus_info']:
                    try:
                        # Extract the multiplier value from the bonus info
                        # Format is "🌾 Пшеница - 1.2x"
                        multiplier = float(bonus_info.split(' ')[-1].rstrip('x'))
                        if multiplier >= 1.0:
                            bonuses.append(bonus_info)
                        else:
                            conflicts.append(bonus_info)
                    except (IndexError, ValueError):
                        # If we can't parse the multiplier, treat it as a bonus
                        bonuses.append(bonus_info)
                
                # Display bonuses first
                if bonuses:
                    info += "\n*Бонусы от соседей:*\n"
                    for bonus in bonuses:
                        info += f"• {bonus}\n"
                
                # Then display conflicts
                if conflicts:
                    # if bonuses:  # Add a newline if there were bonuses
                    info += "\n"
                    info += "*Конфликты с соседями:*\n"
                    for conflict in conflicts:
                        info += f"• {conflict}\n"
                info += "\n"  # Add an extra newline after all bonus info
            
            info += "*Доходность:*\n"
            info += f"• В минуту: {final_income_per_min:.2f} FC\n"
            info += f"• В час: {final_income_per_hour:.1f} FC\n"
            # Only show daily income if it's significant
            if final_income_per_hour > 0:
                info += f"• В день: {final_income_per_day:.0f} FC\n"
            
            # Show base income without multiplier for reference
            info += f"\n*Базовая доходность:* {income_per_min:.2f} FC/мин"
    else:
        info += "🌱 *На этом участке ничего не растёт*\n"
        info += "\n*Посадите растение, чтобы начать зарабатывать!*"
    
    return info


def format_field_display(user_field: List[List[Dict]], soil_field: List[List[int]], field_size: int) -> str:
    """Format the farm field into a readable string with coordinates."""
    # Add top border with column letters
    column_letters = [f"{chr(ord('А') + i)}" for i in range(field_size)]
    # print(column_letters)
    field_display = "🌱 *Ваше поле:*\n\n"
    # field_display += 5*" " + (1*" - ").join(column_letters) + "\n"

    field_display += 5*" " + (1*" - ").join(column_letters[:4]) + ' -  ' + (1*" - ").join(column_letters[4:]) + "\n"
    
    for i in range(field_size):
        # Add row number at the start of each row
        row_number = f"{i+1:2d}"
        row_display = [row_number]
        
        for j in range(field_size):
            # Get cell content
            cell_data = user_field[i][j]
            cell = ""
            if cell_data.get('plant'):
                plant_id = cell_data['plant']
                if cell_data.get('status') == 'wilted':
                    cell = '🥀'  # Wilted plant
                else:
                    plant_info = FarmConfig.PLANT_TYPES.get(plant_id, {})
                    cell = plant_info.get('emoji', '🌱')
            else:
                # Show soil type if no plant
                soil_type = soil_field[i][j]
                soil_info = FarmConfig.SOIL_TYPES.get(soil_type)
                cell = soil_info['emoji']
            
            row_display.append(f"{cell}")
        
        field_display += "".join(row_display) + "\n"
    
    return field_display


def get_plants_keyboard(row: int, col: int) -> InlineKeyboardMarkup:
    """Create a keyboard with available plants for purchase"""
    buttons = []
    for plant_id, plant in FarmConfig.PLANT_TYPES.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{plant['emoji']} {plant['name']} - {plant['cost_fc']} FC",
                callback_data=f"select_plant_{plant_id}_{row}_{col}"
            )
        ])
    
    # Add back button
    buttons.append([
        InlineKeyboardButton(
            text="↩️ Назад к клетке",
            callback_data=f"back_to_cell_{row}_{col}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_plant_info(plant_id: str) -> str:
    """Get formatted information about a plant"""
    plant_id = int(plant_id)
    plant = FarmConfig.PLANT_TYPES.get(plant_id, {})
    if not plant:
        return "Растение не найдено"
    
    info = (
        f"🌱 *{plant['name']}* {plant['emoji']}\n"
        f"💵 Цена: {plant['cost_fc']} FC\n"
        f"💰 Доход: {plant['base_income']} FC/мин\n"
        # f"📈 Множитель почвы: {plant.get('soil_multiplier', 1.0)}x\n"
       
    )
    info +=  f"📝 {plant.get('description', '')}" if plant.get('description') else ""
    
    return info


async def get_user_farm_data(user_id: int) -> tuple:
    """Get all necessary farm data for a user directly from JSON."""
    # Get user's farm data
    farm_data = await get_user_data(user_id, 'farm_minigame')
    user_field = farm_data.get('field')
    field_size = farm_data.get('field_size')  # Default to 3x3 if not set
    
    # Get the current farm field from mini_game_farm.json
    full_field = (await get_farm_data())['curr_field']
    
    # Get the bottom-left corner of the field based on user's field size
    start_row = len(full_field) - field_size
    soil_field = [row[:field_size] for row in full_field[start_row:]]
    
    return user_field, soil_field, field_size


def get_neighbor_bonus(field: List[List[dict]], row: int, col: int, plant_id: int, return_info: bool = False) -> Decimal:
    """Calculate bonus income from neighboring plants."""
    bonus = Decimal('1')
    rows = len(field)
    if rows == 0:
        return bonus
    cols = len(field[0])
    
    # Check all 4 directions: up, right, down, left
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    info = []
    
    for dr, dc in directions:
        r, c = row + dr, col + dc
        if 0 <= r < rows and 0 <= c < cols:
            neighbor = field[r][c]
            if neighbor and neighbor['plant']:
                neighbor_plant = neighbor['plant']
                # Get synergy bonus if exists, otherwise no bonus
                synergy = FarmConfig.PLANT_TYPES[plant_id]['synergies'].get(neighbor_plant, Decimal('1'))
                bonus *= Decimal(str(synergy))
                info.append(f"{FarmConfig.PLANT_TYPES[neighbor_plant]['emoji']} {FarmConfig.PLANT_TYPES[neighbor_plant]['name']} - {synergy}x")    
    return bonus if not return_info else (bonus, info)

def calculate_income_per_minute(field: List[List[dict]], return_nabor_bonus: bool = True) -> Decimal:
    """Calculate income per minute based on all planted crops and their neighbors."""
    income_per_minute = Decimal('0')
    data = []
    
    for i in range(len(field)):
        for j in range(len(field[i])):
            cell = field[i][j]
            if cell and cell['plant']:
                plant_id = cell['plant']
                plant_info = FarmConfig.PLANT_TYPES[plant_id]
                
                # Base income
                base_income = Decimal(str(plant_info['base_income']))
                
                # Calculate neighbor bonus
                neighbor_bonus, nabor_bonus_info = get_neighbor_bonus(field, i, j, plant_id, return_info=True)
                if return_nabor_bonus:
                    cell['nabor_bonus_info'] = nabor_bonus_info
                # Total income per minute for this plant
                income_per_minute += base_income * neighbor_bonus
    
    return income_per_minute.quantize(Decimal('0.01')) if not return_nabor_bonus else (income_per_minute.quantize(Decimal('0.01')), field)

def calculate_income(user_data: dict) -> Decimal:
    """Calculate income since last visit using stored income per minute."""
    farm_data = user_data['farm_minigame']
    last_visit = int(farm_data['last_visit'])  # Remove decimal part
    current_time = int(time.time())  # Current time without decimal part
    
    # Calculate time passed in minutes
    minutes_passed = Decimal(str((current_time - last_visit) / 60))
    
    # Get stored income per minute or calculate if not exists
    if 'income_per_minute' not in farm_data:
        income_per_minute, farm_data['field'] = calculate_income_per_minute(farm_data['field'])
        farm_data['income_per_minute'] = str(income_per_minute)
    
    income_per_minute = Decimal(farm_data['income_per_minute'])
    total_income = income_per_minute * minutes_passed
    
    # Update last visit time (without decimal part)
    farm_data['last_visit'] = current_time
    
    return total_income.quantize(Decimal('0.01'))


async def show_farm_field(message: Message | CallbackQuery, state: FSMContext, error: str = None) -> None:
    """Display the farm field to the user with navigation buttons."""
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)
    farm_data = user_data['farm_minigame']
    user_field, soil_field, field_size = await get_user_farm_data(user_id)
    
    # Calculate income since last visit
    income = calculate_income(user_data)
    if income > 0:
        # Add income to user's FC balance in farm_minigame
        fc_balance = Decimal(farm_data['fc_balance'])
        farm_data['fc_balance'] = str(fc_balance + income)
        await update_user_data(user_id, user_data)
    
    # Format income message
    income_message = f"\n💰 Вы получили {income:.2f} FC за время отсутствия!" if income > 0 else ""
    
    # Format the field display
    field_display = format_field_display(user_field, soil_field, field_size)
    
    # Add income message to the display
    if income > 0:
        field_display += income_message
    
    # Create inline keyboard
    keyboard = []
    
    # Add shop buttons
    shop_row = [
        InlineKeyboardButton(text="🛒 Магазин", callback_data="farm_shop"),
        InlineKeyboardButton(text="💎 Донат магазин", callback_data="donate_shop")
    ]
    keyboard.append(shop_row)
    
    # Add inventory button
    inventory_row = [
        InlineKeyboardButton(text="🎒 Инвентарь фермера", callback_data="farmer_inventory")
    ]
    keyboard.append(inventory_row)
    
    # Add upgrade button only if field size is less than 9x9
    if field_size < 9:
        upgrade_row = [
            InlineKeyboardButton(
                text=f"🆙 Улучшить ферму ({field_size}x{field_size} → {field_size+1}x{field_size+1})",
                callback_data="upgrade_farm"
            )
        ]
        keyboard.append(upgrade_row)
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    # Add instructions
    instructions = (
        "\n*ℹ️ Как использовать:*\n"
        "• Введите координаты клетки (например, `А1` или `б3`)\n"
        "• Нажмите на кнопки ниже для навигации\n"
    )
    
    if error:
        instructions = f"\n❌ *Ошибка:* {error}\n" + instructions

    await send_msg_call(
        message, 
        text=f"{field_display}{instructions}", 
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
  
