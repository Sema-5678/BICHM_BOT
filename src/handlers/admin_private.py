from aiogram import F, Router, types, html
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os
import json
from pathlib import Path
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

from filters.chat_types import ChatTypeFilter, IsAdmin
from utils.json_engine import get_all_users, get_categories_data, get_user_data, update_categories_data, update_user_data
from utils.rcon import apply_rcon_settings, rcon_manager
from kbds.inline import get_callback_btns

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())

# States for admin panel
class CategoryStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_item = State()
    editing_item = State()
    adding_category = State()
    adding_item = State()
    deleting_category = State()
    deleting_item = State()
    changing_minecraft_nickname = State()
    entering_new_nickname = State()


class BotSettingsStates(StatesGroup):
    entering_rcon_host = State()
    entering_rcon_port = State()
    entering_rcon_password = State()

# Helper functions
def get_categories_kb():
    categories = get_categories_data()
    buttons = {}
    
    for cat_id, cat_data in categories.items():
        buttons[cat_data['name']] = f"cat_{cat_id}"
    
    buttons["➕ Добавить категорию"] = "add_category"
    buttons["❌ Удалить категорию"] = "delete_category"
    buttons["⬅ Назад"] = "back_to_admin_menu"
    
    return get_callback_btns(btns=buttons, sizes=(1,))

def get_items_kb(category_id):
    categories = get_categories_data()
    category = categories.get(str(category_id))
    if not category:
        return None
    
    buttons = {}

    iter_obj = dict(
            list(category['elems'].items())[-50 :]
        )
    
    for item_id, item_data in iter_obj.items():
        buttons[f"{item_data['emoji']} {item_data['name']}"] = f"item_{category_id}_{item_id}"
    
    buttons["➕ Добавить предмет"] = f"add_item_{category_id}"
    buttons["⬅ Назад к категориям"] = "manage_items"
    buttons["⬅ Назад в меню"] = "back_to_admin_menu"
    
    return get_callback_btns(btns=buttons, sizes=(1,))

def get_item_actions_kb(category_id, item_id):
    buttons = {
        "✏️ Редактировать": f"edit_item_{category_id}_{item_id}",
        "❌ Удалить": f"delete_item_{category_id}_{item_id}",
        "⬅ Назад к предметам": f"cat_{category_id}"
    }
    return get_callback_btns(btns=buttons, sizes=(1,))

def get_edit_item_kb(category_id, item_id):
    item = get_categories_data()[str(category_id)]['elems'][str(item_id)]
    buttons = {}
    
    for field in ['name', 'emoji', 'description', 'base_price', 'price_growth', 'max_stack', 'currency', 'minecraft_id']:
        buttons[f"✏️ {field}"] = f"edit_field_{category_id}_{item_id}_{field}"
    
    buttons["⬅ Назад к предмету"] = f"item_{category_id}_{item_id}"
    
    return get_callback_btns(btns=buttons, sizes=(1,))

# Command handlers
def get_admin_main_menu():
    buttons = {
        "🛠️ Управление предметами": "manage_items",
        "⚙️ Настройки бота": "bot_settings",
        "📊 Статистика": "bot_stats",
        "🎮 Изменить никнейм Minecraft": "change_minecraft_nickname"
    }
    return get_callback_btns(btns=buttons, sizes=(1,))


def get_bot_settings_kb():
    buttons = {
        "✏️ Изменить RCON_HOST": "edit_rcon_host",
        "✏️ Изменить RCON_PORT": "edit_rcon_port",
        "✏️ Изменить RCON_PASSWORD": "edit_rcon_password",
        "⬅ Назад в меню": "back_to_admin_menu",
    }
    return get_callback_btns(btns=buttons, sizes=(1,))


def get_bot_settings_text() -> str:
    return (
        "⚙️ <b>Настройки бота</b>\n\n"
        f"<b>RCON_HOST</b>: <code>{rcon_manager.host}</code>\n"
        f"<b>RCON_PORT</b>: <code>{rcon_manager.port}</code>\n"
        f"<b>RCON_PASSWORD</b>: <code>{rcon_manager.password}</code>\n\n"
        "Выберите, что изменить:"
    )

@admin_router.message(Command("admin"))
async def admin_panel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🔧 <b>Панель администратора</b>\n\nВыберите раздел:",
        reply_markup=get_admin_main_menu(),
        parse_mode='HTML'
    )


@admin_router.callback_query(F.data == "bot_settings")
async def bot_settings(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        get_bot_settings_text(),
        reply_markup=get_bot_settings_kb(),
        parse_mode="HTML",
    )


@admin_router.callback_query(F.data == "edit_rcon_host")
async def edit_rcon_host_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotSettingsStates.entering_rcon_host)
    await callback.message.edit_text(
        "Введите новый <b>RCON_HOST</b>.\n"
        "Пример: <code>185.9.145.7</code> или <code>example.com</code>",
        reply_markup=get_callback_btns(btns={"❌ Отмена": "bot_settings"}, sizes=(1,)),
        parse_mode="HTML",
    )


@admin_router.message(BotSettingsStates.entering_rcon_host)
async def edit_rcon_host_finish(message: types.Message, state: FSMContext):
    host = (message.text or "").strip()
    if not host:
        await message.answer(
            "❌ RCON_HOST не может быть пустым. Введите значение ещё раз.\n"
            "Пример: <code>185.9.145.7</code>",
            parse_mode="HTML",
        )
        return

    apply_rcon_settings(host=host)
    await state.clear()
    await message.answer("✅ RCON_HOST обновлён.", reply_markup=ReplyKeyboardRemove())
    await message.answer(get_bot_settings_text(), reply_markup=get_bot_settings_kb(), parse_mode="HTML")


@admin_router.callback_query(F.data == "edit_rcon_port")
async def edit_rcon_port_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotSettingsStates.entering_rcon_port)
    await callback.message.edit_text(
        "Введите новый <b>RCON_PORT</b> (число 1–65535).\n"
        "Пример: <code>42385</code>",
        reply_markup=get_callback_btns(btns={"❌ Отмена": "bot_settings"}, sizes=(1,)),
        parse_mode="HTML",
    )


@admin_router.message(BotSettingsStates.entering_rcon_port)
async def edit_rcon_port_finish(message: types.Message, state: FSMContext):
    raw = (message.text or "").strip()
    try:
        port = int(raw)
    except ValueError:
        await message.answer(
            "❌ Нужен порт-число. Введите <b>RCON_PORT</b> ещё раз.\n"
            "Пример: <code>42385</code>",
            parse_mode="HTML",
        )
        return

    if not (1 <= port <= 65535):
        await message.answer(
            "❌ Порт должен быть в диапазоне 1–65535. Введите ещё раз.\n"
            "Пример: <code>42385</code>",
            parse_mode="HTML",
        )
        return

    apply_rcon_settings(port=port)
    await state.clear()
    await message.answer("✅ RCON_PORT обновлён.", reply_markup=ReplyKeyboardRemove())
    await message.answer(get_bot_settings_text(), reply_markup=get_bot_settings_kb(), parse_mode="HTML")


@admin_router.callback_query(F.data == "edit_rcon_password")
async def edit_rcon_password_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotSettingsStates.entering_rcon_password)
    await callback.message.edit_text(
        "Введите новый <b>RCON_PASSWORD</b>.\n"
        "Вводится как есть (без маскировки).",
        reply_markup=get_callback_btns(btns={"❌ Отмена": "bot_settings"}, sizes=(1,)),
        parse_mode="HTML",
    )


@admin_router.message(BotSettingsStates.entering_rcon_password)
async def edit_rcon_password_finish(message: types.Message, state: FSMContext):
    password = message.text if message.text is not None else ""
    apply_rcon_settings(password=password)
    await state.clear()
    await message.answer("✅ RCON_PASSWORD обновлён.", reply_markup=ReplyKeyboardRemove())
    await message.answer(get_bot_settings_text(), reply_markup=get_bot_settings_kb(), parse_mode="HTML")


@admin_router.callback_query(F.data == "back_to_admin_menu")
async def back_to_admin_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🔧 <b>Панель администратора</b>\n\nВыберите раздел:",
        reply_markup=get_admin_main_menu(),
        parse_mode='HTML'
    )


@admin_router.callback_query(F.data == "manage_items")
async def manage_items(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(None)

    await callback.message.edit_text(
        "📦 <b>Управление предметами</b>\n\nВыберите категорию:",
        reply_markup=get_categories_kb(),
        parse_mode='HTML'
    )

# Category callbacks
# @admin_router.callback_query(F.data == "back_to_categories")
# async def back_to_categories(callback: types.CallbackQuery, state: FSMContext):
#     await callback.message.edit_text(
#         "📦 <b>Управление предметами</b>\n\nВыберите категорию:",
#         reply_markup=get_categories_kb(),
#         parse_mode='HTML'
#     )

@admin_router.callback_query(F.data.startswith("cat_"))
async def show_category(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(None)
    category_id = callback.data.split("_")[1]
    categories = get_categories_data()
    
    if category_id not in categories:
        await callback.answer("Категория не найдена")
        return
    
    category = categories[category_id]
    await callback.message.edit_text(
        f"Категория: {category['name']}\n\nВыберите предмет:",
        reply_markup=get_items_kb(category_id)
    )

# Item callbacks
@admin_router.callback_query(F.data.startswith("item_"))
async def show_item(callback: types.CallbackQuery, state: FSMContext):
    _, category_id, item_id = callback.data.split("_")
    categories = get_categories_data()
    
    if category_id not in categories or item_id not in categories[category_id]['elems']:
        await callback.answer("Предмет не найден")
        return
    
    item = categories[category_id]['elems'][item_id]
    text = (
        f"🔹 {item['name']} {item['emoji']}\n"
        f"📝 {item['description']}\n\n"
        f"💵 Базовая цена: {item['base_price']} {item['currency']}\n"
        f"📈 Рост цены: {item['price_growth']}\n"
        f"📦 Макс. в стаке: {item['max_stack']}\n"
        f"🆔 Minecraft ID: {item.get('minecraft_id', 'Не указан')}"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_item_actions_kb(category_id, item_id)
    )

# Add category
@admin_router.callback_query(F.data == "add_category")
async def add_category_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CategoryStates.adding_category)
    await callback.message.edit_text(
        "Введите название новой категории:",
        reply_markup=get_callback_btns(
            btns={"❌ Отмена": "manage_items"},
            sizes=(1,)
        )
    )

@admin_router.message(CategoryStates.adding_category)
async def add_category_finish(message: types.Message, state: FSMContext):
    categories = get_categories_data()
    new_id = str(max([int(k) for k in categories.keys()] + [0]) + 1)
    
    categories[new_id] = {
        "name": message.text,
        "elems": {}
    }
    
    update_categories_data(categories)
    await message.answer(
        f"✅ Категория '{message.text}' добавлена!",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()
    await admin_panel(message, state)

# Add item
@admin_router.callback_query(F.data.startswith("add_item_"))
async def add_item_start(callback: types.CallbackQuery, state: FSMContext):
    category_id = callback.data.split("_")[2]
    await state.update_data(category_id=category_id)
    await state.set_state(CategoryStates.adding_item)
    
    await callback.message.edit_text(
        "Введите данные предмета в формате (каждая строка - отдельное поле):\n"
        "Название\n"
        "Эмодзи\n"
        "Описание\n"
        "Базовая цена\n"
        "Рост цены\n"
        "Макс. в стаке\n"
        'За какую валюту кипить? bc или rub (маленькими буквами)\n'
        "Minecraft ID\n\n"
        "Пример:\n"
        "Алмазный меч\n"
        "⚔️\n"
        "Мощное оружие...\n"
        "50\n"
        "10\n"
        "1\n"
        'bc\n'
        "diamond_sword",
        reply_markup=get_callback_btns(
            # btns={"❌ Отмена": "cancel_action"},
            btns={"❌ Отмена": f"cat_{category_id}"},

            sizes=(1,)
        )
    )

@admin_router.message(CategoryStates.adding_item)
async def add_item_finish(message: types.Message, state: FSMContext):
    try:
        data = message.text.split('\n')
        if len(data) < 7:
            raise ValueError("Недостаточно данных")
            
        item_data = {
            "id": "",  # Will be set after
            "name": data[0].strip(),
            "emoji": data[1].strip(),
            "description": data[2].strip(),
            "base_price": float(data[3].strip()),
            "price_growth": float(data[4].strip()),
            "max_stack": int(data[5].strip()),
            "currency": data[6].strip().lower(),
            "minecraft_id": data[7].strip(),
            "cat_name": ""  # Will be set after
        }
        
        state_data = await state.get_data()
        category_id = state_data['category_id']
        categories = get_categories_data()
        
        if category_id not in categories:
            await message.answer("Ошибка: категория не найдена")
            return
            
        # Generate new item ID
        item_id = str(max([int(k) for k in categories[category_id]['elems'].keys()] + [0]) + 1)
        
        # Set category name and item ID
        item_data['id'] = item_id
        item_data['cat_name'] = categories[category_id]['name']
        
        # Add item to category
        categories[category_id]['elems'][item_id] = item_data
        update_categories_data(categories)
        
        await message.answer(
            f"✅ Предмет '{item_data['name']}' добавлен в категорию!",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        # await admin_panel(message, state)
        # await manage_items(message, state)
        await admin_panel(message, state)
        
    except (ValueError, IndexError) as e:
        await message.answer(
            "Ошибка при обработке данных. Убедитесь, что все поля заполнены правильно.\n"
            "Попробуйте ещё раз или нажмите 'Отмена'."
        )

# Edit item
@admin_router.callback_query(F.data.startswith("edit_item_"))
async def edit_item_start(callback: types.CallbackQuery, state: FSMContext):
    _, _, category_id, item_id = callback.data.split("_")
    categories = get_categories_data()
    
    if category_id not in categories or item_id not in categories[category_id]['elems']:
        await callback.answer("Предмет не найден")
        return
    
    item = categories[category_id]['elems'][item_id]
    await state.update_data(category_id=category_id, item_id=item_id)
    
    text = (
        f"Редактирование предмета: {item['name']}\n\n"
        f"Выберите поле для редактирования:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_edit_item_kb(category_id, item_id)
    )

@admin_router.callback_query(F.data.startswith("edit_field_"))
async def edit_field_start(callback: types.CallbackQuery, state: FSMContext):
    _, _, category_id, item_id, field = callback.data.split("_", 4)
    await state.update_data(
        category_id=category_id,
        item_id=item_id,
        field=field
    )
    await state.set_state(CategoryStates.editing_item)
    
    categories = get_categories_data()
    item = categories[category_id]['elems'][item_id]
    
    await callback.message.edit_text(
        f"Текущее значение поля '{field}': {item.get(field, 'Не указано')}\n\n"
        f"Введите новое значение: {'bc или rub (маленькими буквами)' if field == 'currency' else ''}",
        reply_markup=get_callback_btns(
            btns={"❌ Отмена": f"edit_item_{category_id}_{item_id}"},
            sizes=(1,)
        )
    )

@admin_router.message(CategoryStates.editing_item)
async def edit_field_finish(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    category_id = state_data['category_id']
    item_id = state_data['item_id']
    field = state_data['field']
    
    categories = get_categories_data()
    
    if category_id not in categories or item_id not in categories[category_id]['elems']:
        await message.answer("Ошибка: предмет не найден")
        await state.clear()
        return
    
    # Convert value to appropriate type
    try:
        if field in ['base_price', 'price_growth']:
            value = float(message.text)
        elif field == 'max_stack':
            value = int(message.text)
        else:
            value = message.text
    except ValueError:
        await message.answer("Неверный формат данных. Пожалуйста, введите корректное значение.")
        return
    
    # Update the field
    categories[category_id]['elems'][item_id][field] = value
    update_categories_data(categories)
    
    await message.answer(
        f"✅ Поле '{field}' успешно обновлено!",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Show the item again
    item = categories[category_id]['elems'][item_id]
    text = (
        f"🔹 {item['name']} {item['emoji']}\n"
        f"📝 {item['description']}\n\n"
        f"💵 Базовая цена: {item['base_price']} {item['currency']}\n"
        f"📈 Рост цены: {item['price_growth']}\n"
        f"📦 Макс. в стаке: {item['max_stack']}\n"
        f"🆔 Minecraft ID: {item.get('minecraft_id', 'Не указан')}"
    )
    
    await message.answer(
        text,
        reply_markup=get_item_actions_kb(category_id, item_id)
    )
    
    await state.clear()

# Delete item
@admin_router.callback_query(F.data.startswith("delete_item_"))
async def delete_item(callback: types.CallbackQuery, state: FSMContext):
    _, _, category_id, item_id = callback.data.split("_")
    categories = get_categories_data()
    
    if category_id not in categories or item_id not in categories[category_id]['elems']:
        await callback.answer("Предмет не найден")
        return
    
    item_name = categories[category_id]['elems'][item_id]['name']
    
    # Ask for confirmation
    await callback.message.edit_text(
        f"Вы уверены, что хотите удалить предмет '{item_name}'?\n"
        "Это действие нельзя отменить!",
        reply_markup=get_callback_btns(
            btns={
                "❌ Да, удалить": f"confirm_delete_item_{category_id}_{item_id}",
                "⬅ Нет, отмена": f"item_{category_id}_{item_id}"
            },
            sizes=(2,)
        )
    )

@admin_router.callback_query(F.data.startswith("confirm_delete_item_"))
async def confirm_delete_item(callback: types.CallbackQuery, state: FSMContext):
    _, _, _, category_id, item_id = callback.data.split("_")
    categories = get_categories_data()
    
    if category_id not in categories or item_id not in categories[category_id]['elems']:
        await callback.answer("Предмет не найден")
        return
    
    item_name = categories[category_id]['elems'][item_id]['name']
    del categories[category_id]['elems'][item_id]
    update_categories_data(categories)
    
    await callback.message.edit_text(
        f"✅ Предмет '{item_name}' был удален.",
        reply_markup=get_callback_btns(
            btns={"⬅ К предметам": f"cat_{category_id}"},
            sizes=(1,)
        )
    )

# Delete category
@admin_router.callback_query(F.data == "delete_category")
async def delete_category_start(callback: types.CallbackQuery, state: FSMContext):
    categories = get_categories_data()
    
    if not categories:
        await callback.answer("Нет категорий для удаления")
        return
    
    buttons = {}
    
    for cat_id, cat_data in categories.items():
        buttons[f"❌ {cat_data['name']}"] = f"delete_cat_{cat_id}"
    
    buttons["⬅ Назад"] = "manage_items"
    
    await callback.message.edit_text(
        "Выберите категорию для удаления (все предметы в ней также будут удалены):",
        reply_markup=get_callback_btns(btns=buttons, sizes=(1,))
    )

@admin_router.callback_query(F.data.startswith("delete_cat_"))
async def delete_category_confirm(callback: types.CallbackQuery, state: FSMContext):
    category_id = callback.data.split("_")[2]
    categories = get_categories_data()
    
    if category_id not in categories:
        await callback.answer("Категория не найдена")
        return
    
    category_name = categories[category_id]['name']
    
    await callback.message.edit_text(
        f"Вы уверены, что хотите удалить категорию '{category_name}'?\n"
        f"В ней находится {len(categories[category_id]['elems'])} предметов.\n"
        "Это действие нельзя отменить!",
        reply_markup=get_callback_btns(
            btns={
                "❌ Да, удалить": f"confirm_delete_cat_{category_id}",
                "⬅ Нет, отмена": "manage_items"
            },
            sizes=(2,)
        )
    )

@admin_router.callback_query(F.data.startswith("confirm_delete_cat_"))
async def delete_category_finish(callback: types.CallbackQuery, state: FSMContext):
    category_id = callback.data.split("_")[3]
    categories = get_categories_data()
    
    if category_id not in categories:
        await callback.answer("Категория не найдена")
        return
    
    category_name = categories[category_id]['name']
    del categories[category_id]
    update_categories_data(categories)
    
    await callback.message.edit_text(
        f"✅ Категория '{category_name}' и все её предметы были удалены.",
        reply_markup=get_callback_btns(
            btns={"⬅ К категориям": "manage_items"},
            sizes=(1,)
        )
    )

# Cancel action
@admin_router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Действие отменено.")
    await admin_panel(callback.message, state)




























































@admin_router.callback_query(F.data == "change_minecraft_nickname")
async def change_minecraft_nickname_start(callback: types.CallbackQuery, state: FSMContext):
    users =  get_all_users()
    if len(users) == 0:
        await callback.answer("❌ Нет зарегистрированных пользователей", show_alert=True)
        return
    
    buttons = {}
    for user_id, data in users:
        display_name = f"@{data['username']}" if data.get('username') else f"Пользователь {user_id}"
        buttons[display_name] = f"change_nick_user_{user_id}"
    
    buttons["⬅ Назад"] = "back_to_admin_menu"
    
    await callback.message.edit_text(
        "👥 Выберите пользователя, чей никнейм нужно изменить:",
        reply_markup=get_callback_btns(btns=buttons, sizes=(1,))
    )
    await state.set_state(CategoryStates.changing_minecraft_nickname)

@admin_router.callback_query(F.data.startswith("change_nick_user_"), CategoryStates.changing_minecraft_nickname)
async def select_user_for_nickname_change(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.data.split('_')[-1]
    await state.update_data(selected_user_id=user_id)
    
    await callback.message.edit_text(
        f"✏️ Введите новый никнейм Minecraft для пользователя ID: {user_id}",
        reply_markup=get_callback_btns(btns={"❌ Отмена": "back_to_admin_menu"})
    )
    await state.set_state(CategoryStates.entering_new_nickname)

@admin_router.message(CategoryStates.entering_new_nickname)
async def save_minecraft_nickname(message: types.Message, state: FSMContext):
    new_nickname = message.text.strip()
    if not new_nickname:
        await message.answer("❌ Никнейм не может быть пустым. Попробуйте еще раз.")
        return
    
    if len(new_nickname) > 16:
        await message.answer("❌ Никнейм не может быть длиннее 16 символов. Попробуйте еще раз.")
        return
    
    user_data = await state.get_data()
    user_id = user_data.get('selected_user_id')
    
    if not user_id:
        await message.answer("❌ Ошибка: пользователь не выбран. Попробуйте снова.")
        await state.clear()
        await admin_panel(message, state)
        return
    
    user_data = get_user_data(user_id)
    user_data['minecraft_username'] = new_nickname
    update_user_data(user_id, user_data)
    
    # if success:
    await message.answer(
            f"✅ Никнейм Minecraft успешно изменен на: {new_nickname}",
            reply_markup=get_admin_main_menu()
        )
    # else:
    #     await message.answer(
    #         "❌ Не удалось изменить никнейм. Пользователь не найден или произошла ошибка.",
    #         reply_markup=get_admin_main_menu()
    #     )
    
    await state.clear()
