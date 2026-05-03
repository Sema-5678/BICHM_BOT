from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from utils.sqlite_storage import get_user_data
from .farm_game import FarmGame

# Initialize router
farm_router = Router()

@farm_router.message(Command("farm"))
async def farm_command(message: Message, state: FSMContext):
    """Handle the /farm command to show the farm."""
    user_data = await get_user_data(message.from_user.id)
    
    # Initialize farm data if not exists
    if 'farm_data' not in user_data:
        user_data['farm_data'] = {
            'visible_field': {f"{row}{col}": {'state': 'empty', 'plant_id': None} 
                            for row in ['A', 'B', 'C'] 
                            for col in range(1, 4)}
        }
    
    farm = FarmGame(message.from_user.id, user_data)
    await show_farm_status(message, farm)

async def show_farm_status(message: Message, farm: FarmGame, edit_message: bool = False):
    """Display the current farm status with emoji representation."""
    farm_data = farm.farm_data
    field = farm_data.get('visible_field', {})
    
    # Plant emoji mapping
    PLANT_EMOJIS = {
        1: '🌾',  # Пшеница
        2: '🥕',  # Морковь
        3: '🥔',  # Картофель
        4: '🎃',  # Тыква
        5: '🌽',  # Кукуруза
        101: '🌟', # Золотая пшеница
        102: '🌹', # Кристальная роза
        103: '❄️'  # Ледяной цветок
    }
    
    # Build the farm grid
    rows = []
    
    # Add column numbers header
    header = '  ' + ' '.join([f' {i} ' for i in range(1, 4)])
    rows.append(header)
    
    # Add rows with row letters and cells
    for row in ['A', 'B', 'C']:
        row_cells = [f'{row} ']
        for col in range(1, 4):
            cell_id = f"{row}{col}"
            cell = field.get(cell_id, {'state': 'empty'})
            
            if cell.get('state') == 'empty' or not cell.get('plant_id'):
                row_cells.append('🌱')  # Empty soil emoji
            else:
                plant_emoji = PLANT_EMOJIS.get(cell['plant_id'], '🌱')
                row_cells.append(plant_emoji)
        
        rows.append(' '.join(row_cells))
    
    # Add instructions
    instructions = """
    
ℹ️ Чтобы посмотреть информацию о клетке, напишите её номер (например, A1, B2, C3)
    """
    
    farm_display = '\n'.join(rows) + instructions
    
    if edit_message and hasattr(message, 'edit_text'):
        await message.edit_text(farm_display)
    else:
        await message.answer(farm_display)

def register_handlers(dp: Dispatcher):
    """Register all farm game handlers."""
    # Command handler
    dp.register_message_handler(farm_command, commands=["farm"])
