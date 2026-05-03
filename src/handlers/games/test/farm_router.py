# from aiogram import Router, F
# from aiogram.filters import Command
# from aiogram.types import Message, CallbackQuery

# from .farm_handler import farm_command, FarmStates, shop_callback, buy_item_callback, plant_callback, harvest_callback, water_plants_callback
# from .farm_game import FarmGame, PlantState

# # Create router instance
# farm_router = Router()

# # Register message handlers
# @farm_router.message(Command("farm"))
# async def handle_farm_command(message: Message, state: FSMContext):
#     """Handle /farm command"""
#     await farm_command(message, state)

# # Register callback query handlers
# @farm_router.callback_query(F.data.startswith("shop_"))
# async def handle_shop_callback(callback: CallbackQuery, state: FSMContext):
#     """Handle shop-related callbacks"""
#     await shop_callback(callback, state)

# @farm_router.callback_query(F.data.startswith("buy_"))
# async def handle_buy_item_callback(callback: CallbackQuery, state: FSMContext):
#     """Handle buy item callbacks"""
#     await buy_item_callback(callback, state)

# @farm_router.callback_query(F.data.startswith("plant_"))
# async def handle_plant_callback(callback: CallbackQuery, state: FSMContext):
#     """Handle plant action callbacks"""
#     await plant_callback(callback, state)

# @farm_router.callback_query(F.data.startswith("harvest_"))
# async def handle_harvest_callback(callback: CallbackQuery, state: FSMContext):
#     """Handle harvest action callbacks"""
#     await harvest_callback(callback, state)

# @farm_router.callback_query(F.data.startswith("water_"))
# async def handle_water_plants_callback(callback: CallbackQuery, state: FSMContext):
#     """Handle water plants callbacks"""
#     await water_plants_callback(callback, state)

# # Export router for use in main.py
# def get_farm_router() -> Router:
#     """Return the farm router with all handlers registered"""
#     return farm_router
