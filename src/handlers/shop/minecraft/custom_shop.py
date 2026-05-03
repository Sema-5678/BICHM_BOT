
import json
import uuid
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
import logging

from common.data_for_bot import TEXTS
from handlers.components.functions import get_user_data, update_user_data, format_money
from handlers.common_funcs import send_msg_call
from kbds.inline import get_callback_btns
from handlers.components.callbacks import MinecraftShopCallback, CustomizationCallback
from handlers.components.decorators import protected_callback
from utils.sqlite_storage import get_categories_data
from utils.rcon import rcon_manager

# Service prices (in BC)
PRICE_COLORED_NICKNAME = 10_000  # Price for colored nickname
PRICE_COLORED_PREFIX = 15_000    # Price for colored prefix

minecraft_custom_shop_router = Router()
minecraft_custom_shop_router.callback_query.filter(
    CustomizationCallback.filter()
)


# States for customization
class CustomizationStates(StatesGroup):
    waiting_for_customization_type = State()
    waiting_for_color = State()
    waiting_for_text = State()

# Available colors with their Minecraft color codes
COLORS = {
    'Черный': 'black',
    'Темно-синий': 'dark_blue',
    'Темно-зеленый': 'dark_green',
    'Бирюзовый': 'dark_aqua',
    'Темно-красный': 'dark_red',
    'Фиолетовый': 'dark_purple',
    'Золотой': 'gold',
    'Серый': 'gray',
    'Темно-серый': 'dark_gray',
    'Синий': 'blue',
    'Зеленый': 'green',
    'Аквамарин': 'aqua',
    'Красный': 'red',
    'Розовый': 'light_purple',
    'Желтый': 'yellow',
    'Белый': 'white'
}

@minecraft_custom_shop_router.callback_query(CustomizationCallback.filter(F.action == "show_customization"))
@protected_callback
async def show_customization_menu(callback: CallbackQuery, state: FSMContext, callback_data: CustomizationCallback):
    """Show customization options menu"""
    user_id = callback.from_user.id
    
    # Create keyboard with customization options
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"🎨 Цветной префикс - {format_money(PRICE_COLORED_PREFIX, 'bc')}",
        callback_data=CustomizationCallback(
            user_id=user_id,
            action="choose_color",
            custom_type="prefix"
        ).pack()
    )
    
    builder.button(
        text=f"👤 Цветной ник - {format_money(PRICE_COLORED_NICKNAME, 'bc')}",
        callback_data=CustomizationCallback(
            user_id=user_id,
            action="choose_color",
            custom_type="nickname"
        ).pack()
    )
    
    builder.button(
        text="⬅ Назад",
        callback_data=MinecraftShopCallback(
            user_id=user_id,
            action="show_shop",
            # shop_type="items"
        ).pack()
    )
    
    builder.adjust(1)
    
    await state.set_state(CustomizationStates.waiting_for_customization_type)
    await callback.message.edit_text(
        "🎨 <b>Настройка внешнего вида</b>\n\n"
        "Выберите, что вы хотите изменить:",
        reply_markup=builder.as_markup(),
        parse_mode='HTML'
    )

@minecraft_custom_shop_router.callback_query(CustomizationCallback.filter(F.action == "choose_color"))
@protected_callback
async def choose_color(callback: CallbackQuery, state: FSMContext, callback_data: CustomizationCallback):
    """Show color selection menu"""
    user_id = callback.from_user.id
    custom_type = callback_data.custom_type
    
    # Store the customization type in state
    await state.update_data(custom_type=custom_type)
    
    # Create keyboard with color options
    builder = InlineKeyboardBuilder()
    
    # Add color buttons (2 columns)
    for i in range(0, len(COLORS), 2):
        colors = list(COLORS.items())
        color1_name, color1_code = colors[i]
        builder.button(
            text=f"{color1_name}",
            callback_data=CustomizationCallback(
                user_id=user_id,
                action="set_color",
                custom_type=custom_type,
                color=color1_code
            ).pack()
        )
        
        if i + 1 < len(colors):
            color2_name, color2_code = colors[i + 1]
            builder.button(
                text=f"{color2_name}",
                callback_data=CustomizationCallback(
                    user_id=user_id,
                    action="set_color",
                    custom_type=custom_type,
                    color=color2_code
                ).pack()
            )
    
    # Add back button
    builder.button(
        text="⬅ Назад",
        callback_data=MinecraftShopCallback(
            user_id=user_id,
            action="show_customization",
            shop_type="custom"
        ).pack()
    )
    
    builder.adjust(2, repeat=True)
    
    await state.set_state(CustomizationStates.waiting_for_color)
    if custom_type == 'prefix':
        text = f"""
🎨 ЦВЕТНОЙ ПРЕФИКС

Цена {PRICE_COLORED_NICKNAME} ВС
Префикс отображается в игре везде перед ником

❗️Префикс не должен в себя включать свастику, политику, маты, буллинг в сторону игрока,непристойные слова, 18+
❗️Префикс может быть краси́вее в [квадратных скобках], а также учитывайте постановку пробела междуником и префиксом

Напишите в ответе на это сообщение сам префикс

❗️Обратите внимание, что с вашего счета сразу спишется цена, как вы ответите на сообщение
Префикс МОМЕНТАЛЬНО применится
        
"""
    else:
        text = f"""
🫟 Ц В Е Т Н О Й   Н И К

Цена {PRICE_COLORED_NICKNAME} ВС

❗️Обратите внимание, что с вашего счета сразу спишется цена, когда вы выберите цвет
Цвет МОМЕНТАЛЬНО применится"""

    await callback.message.edit_text(
        f"{text}\n\n🎨 <b>Выберите цвет</b>",
        reply_markup=builder.as_markup(),
        parse_mode='HTML'
    )

@minecraft_custom_shop_router.callback_query(CustomizationCallback.filter(F.action == "set_color"))
@protected_callback
async def set_color(callback: CallbackQuery, state: FSMContext, callback_data: CustomizationCallback):
    """Handle color selection"""
    user_id = callback.from_user.id
    color = callback_data.color
    custom_type = callback_data.custom_type
    
    # Get user data and check balance
    user_data = await get_user_data(user_id)
    
    # Determine the price based on service type
    price = PRICE_COLORED_PREFIX if custom_type == "prefix" else PRICE_COLORED_NICKNAME
    
    # Check if user has enough balance
    if user_data.get('balance', 0) < price:
        await callback.answer(f"❌ Недостаточно BC. Нужно: {price}")
        return
    
    # Store the selected color and price in state
    await state.update_data(selected_color=color, service_price=price)
    
    if custom_type == "prefix":
        # For prefix, ask for the text
        await state.set_state(CustomizationStates.waiting_for_text)
        await callback.message.edit_text(
            f"✏️ <b>Введите текст префикса:</b>\n\n"
            f"Если вы не хотите менять текст префикса то просто напишите его сюда\n\n"
            f"Максимальная длина: 10 символов\n"
            f"Стоимость: {price} BC",
            parse_mode='HTML'
        )
    else:
        # For nickname, we already have the nickname, so we can apply the color directly
        minecraft_username = user_data.get('minecraft_username')
        
        if not minecraft_username:
            await callback.answer("❌ Ошибка: не указан ник в майнкрафте")
            return
        
        # Deduct balance
        user_data['balance'] -= price
        await update_user_data(user_id, user_data)
        
        # Format the nickname with color
        # formatted_nickname = f"&{color}{minecraft_username}"


        team_uuid = uuid.uuid4()
        team_uuid = minecraft_username
        # data = {
        # # "text": f"{text} ",
        # "color": color
        # }
        # payload = json.dumps(data, ensure_ascii=False)

        # minecraft_username = user_data.get('team')


        cmd_1 = f"team add {team_uuid}"
        cmd_2 = f"team modify {team_uuid} color {color}"
        print(cmd_2)
        cmd_3 = f"team join {team_uuid} {minecraft_username}"
        
        # Execute the RCON command
        # command = f"nickname {minecraft_username} {formatted_nickname}"
        
        result = await rcon_manager.do_command(cmd_1)
        result = await rcon_manager.do_command(cmd_2)

        result = await rcon_manager.do_command(cmd_3)
        
        
        if "No player was found" not in result:
            await callback.message.answer(f"✅ Цвет ника успешно изменен! Списано {price} BC")
            await show_customization_menu(callback, state, callback_data)
        else:
            # Return money if command failed
            user_data['balance'] += price
            await update_user_data(user_id, user_data)
            await callback.message.answer(f"❌ Ошибка: {result}")

@minecraft_custom_shop_router.message(CustomizationStates.waiting_for_text)
@protected_callback
async def handle_prefix_text(message: Message, state: FSMContext):
    """Handle prefix text input"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if len(text) > 10:
        await message.answer("❌ Превышена максимальная длина префикса (10 символов). Пожалуйста, введите короче:")
        return
    
    # Get the selected color and price from state
    state_data = await state.get_data()
    color = state_data.get('selected_color')
    price = state_data.get('service_price', PRICE_COLORED_PREFIX)
    custom_type = state_data.get('custom_type')
    
    if not color or custom_type != "prefix":
        await message.answer("❌ Произошла ошибка. Пожалуйста, начните заново.")
        await state.clear()
        return
    
    user_data = await get_user_data(user_id)
    minecraft_username = user_data.get('minecraft_username')
    
    if not minecraft_username:
        await message.answer("❌ Ошибка: не указан ник в майнкрафте")
        await state.clear()
        return
    
    # Check balance one more time before applying
    if user_data.get('balance', 0) < price:
        await message.answer(f"❌ Недостаточно BC. Нужно: {price}")
        await state.clear()
        return
    
    # Deduct balance
    user_data['balance'] -= price
    await update_user_data(user_id, user_data)
    
    # Format the prefix with color
    # formatted_prefix = f"&{color}[{text}]&r"

    team_uuid = uuid.uuid4()
    team_uuid = minecraft_username


    # print(color, text)

    cmd_1 = f"team add {team_uuid}"
    # cmd_2 = f"team modify {team_uuid} color ({color}) "
    data = {
        "text": f"{text} ",
        "color": color
    }
    payload = json.dumps(data, ensure_ascii=False)
    cmd_3 = f'team modify {team_uuid} prefix {payload}'

    # print(cmd_3)

    cmd_4 = f"team join {team_uuid} {minecraft_username}"
    
    
    # Execute the RCON command to set the prefix
    # command = f"team add 1"

    # success, result = await execute_rcon_command(command, minecraft_username)
    result = await rcon_manager.do_command(cmd_1)
    # result = await rcon_manager.do_command(cmd_2)

    result = await rcon_manager.do_command(cmd_3)
    result = await rcon_manager.do_command(cmd_4)
    
    if "No player was found" not in result:
        await message.answer(
            f"✅ Префикс успешно установлен: {text}\n"
            f"Списано: {price} BC"
            # f"Остаток: {user_data['balance']} BC"
        )
    else:
        # Return money if command failed
        user_data['balance'] += price
        await update_user_data(user_id, user_data)
        await message.answer(f"❌ Ошибка: {result}")
    
    await state.clear()
