from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from config import (
    EASTER_EGGS,
    MIN_CREDIT_RATING,
    TOP_RICH_COUNT,
    BLACKJACK_BET,
    AMATEUR_BLACKJACK_BET,
    BASE_ROBBERY_CHANCE,
    INTEREST_DEPOSIT_RATE,
    INTEREST_CREDIT_RATE,
)
from filters.chat_types import ChatTypeFilter
from handlers.components.functions import *
from common.data_for_bot import TEXTS

bank_router = Router()



@bank_router.message(Command("take_loan"))
async def take_loan_handler(message: Message):
    try:
        amount = Decimal(message.text.split()[1])
    except:
        await message.answer(TEXTS["errors"]["use_syntax_take_loan"])
        return
    
    if not await check_is_valid_num(message, amount):
        return

    user_id = message.from_user.id
    user_data = get_user_data(user_id)

    # Проверяем кредитный рейтинг
    if user_data["credit_rating"] < MIN_CREDIT_RATING:
        await message.answer(TEXTS["bank"]["credit_rating_too_low"])
        return

    max_loan = calculate_max_loan(user_data["credit_rating"])
    total_debt_after = user_data["debt"] + amount

    if total_debt_after > max_loan:
        await message.answer(
            TEXTS["bank"]["loan_limit_exceeded"].format(max=format_money(max_loan))
        )
        return

    # Выдаем кредит
    user_data["debt"] = total_debt_after
    user_data["balance"] += amount
    user_data["credit_rating"] = max(
        0, user_data["credit_rating"] - 2
    )  # Уменьшаем рейтинг
    
    # Обновляем min_credit - записываем текущую сумму долга
    # Это защищает от манипуляций: пользователь не может погасить кредит
    # и сразу взять новый перед начислением процентов
    user_data["max_loan"] = max(user_data["debt"], user_data["max_loan"])
    
    update_user_data(user_id, user_data)

    await message.answer(
        TEXTS["bank"]["take_loan_approved"].format(
            amount=format_money(amount),
            debt=format_money(user_data['debt']),
            credit_rating=user_data['credit_rating'],
            available=format_money(max_loan - user_data['debt']),
        )
    )


@bank_router.message(Command("pay_off_loan"))
async def pay_off_loan_handler(message: Message):
    try:
        amount = Decimal(message.text.split()[1])
    except:
        await message.answer(TEXTS["errors"]["use_syntax_pay_off"])
        return
    
    if not await check_is_valid_num(message, amount):
        return

    

    user_id = message.from_user.id
    user_data = get_user_data(user_id)

    

    if user_data["balance"] < amount:
        await message.answer(TEXTS["errors"]["not_enough_balance"])
        return

    debt_before = user_data["debt"]

    if debt_before <= Decimal("0"):
        await message.answer(TEXTS["errors"]["no_debt"])
        return

    if user_data["debt"] < amount:
        amount = user_data["debt"]  # Нельзя погасить больше долга

    # Погашаем кредит
    user_data["balance"] -= amount
    user_data["debt"] -= amount

    # Повышаем кредитный рейтинг при погашении
    if user_data["debt"] == Decimal("0"):
        user_data["credit_rating"] = user_data["credit_rating"] + 5
    else:
        # Начисляем +1 только при "значимом платеже"
        from config import MIN_PAYMENT_FOR_RATING, MIN_PERCENT_FOR_RATING
        threshold_abs = MIN_PAYMENT_FOR_RATING
        threshold_pct = (debt_before * MIN_PERCENT_FOR_RATING)
        threshold = max(threshold_abs, threshold_pct)
        if amount >= threshold:
            user_data["credit_rating"] = user_data["credit_rating"] + 1

    update_user_data(user_id, user_data)

    await message.answer(
        TEXTS["bank"]["pay_off_success"].format(
            amount=format_money(amount),
            debt=format_money(user_data['debt']),
            credit_rating=user_data['credit_rating'],
        )
    )


@bank_router.message(Command("deposit_replenish"))
async def deposit_replenish_handler(message: Message):
    try:
        amount = Decimal(message.text.split()[1])
    except:
        await message.answer(TEXTS["errors"]["use_syntax_dep_repl"])
        return
    
    if not await check_is_valid_num(message, amount):
        return

    user_id = message.from_user.id
    user_data = get_user_data(user_id)


    if user_data["balance"] < amount:
        await message.answer(TEXTS["errors"]["not_enough_balance"])
        return

    # Пополняем вклад
    user_data["balance"] -= amount
    user_data["deposit"] += amount

    update_user_data(user_id, user_data)

    await message.answer(
        TEXTS["bank"]["deposit_replenished"].format(
            amount=format_money(amount),
            deposit=format_money(user_data['deposit']),
            balance=format_money(user_data['balance']),
        )
    )


@bank_router.message(Command("deposit_withdraw"))
async def deposit_withdraw_handler(message: Message):
    try:
        amount = Decimal(message.text.split()[1])
    except:
        await message.answer(TEXTS["errors"]["use_syntax_dep_wd"])
        return
    
    if not await check_is_valid_num(message, amount):
        return

    user_id = message.from_user.id
    user_data = get_user_data(user_id)

    if user_data["deposit"] < amount:
        amount = user_data["deposit"]  # Нельзя снять больше вклада

    # Снимаем с вклада
    user_data["balance"] += amount
    user_data["deposit"] -= amount
    
    # Обновляем min_deposit - записываем текущую сумму депозита
    # Это защищает от манипуляций: пользователь не может снять деньги
    # и сразу положить обратно перед начислением процентов
    user_data["min_deposit"] = min(user_data["deposit"], user_data["min_deposit"])

    update_user_data(user_id, user_data)

    await message.answer(
        TEXTS["bank"]["deposit_withdrawn"].format(
            amount=format_money(amount),
            deposit=format_money(user_data['deposit']),
            balance=format_money(user_data['balance']),
        )
    )


@bank_router.message(Command("games"))
async def show_games(message: Message):
    text = TEXTS["bank"]["games_list"].format(
        blackjack_bet=format_money(BLACKJACK_BET),
        amateur_bet=format_money(AMATEUR_BLACKJACK_BET),
        base_robbery=BASE_ROBBERY_CHANCE,
    )

    await message.answer(text)


# Остальные команды (bctop, transfer) без изменений...


@bank_router.message(Command("bctop"))
async def show_top_rich(message: Message):
    top_users = get_top_rich(TOP_RICH_COUNT)
    if not top_users:
        await message.answer(TEXTS["bank"]["top_rich_no_data"])
        return
    text = TEXTS["bank"]["top_rich_header"].format(count=TOP_RICH_COUNT)
    for i, (user_id, user_data) in enumerate(top_users, 1):
        try:
            user = await message.bot.get_chat(user_id)
            name = user.first_name or TEXTS["bank"]["user_fallback_name"].format(user_id=user_id)
        except:
            name = TEXTS["bank"]["user_fallback_name"].format(user_id=user_id)
        dep =   f"  +  {format_money(user_data['deposit'])}" if user_data['deposit'] > 0 else ''
        text += f"{i}. {name}: {format_money(user_data['balance'])}{dep}\n\n"
    await message.answer(text)


@bank_router.message(Command("transfer"))
async def transfer_money_handler(message: Message):
    # Проверяем, что команда отправлена в ответ на сообщение
    if not message.reply_to_message:
        await message.answer(TEXTS["bank"]["transfer_reply_hint"])
        return

    try:
        parts = message.text.split()
        if len(parts) < 2:
            raise ValueError
        amount = Decimal(parts[1])
    except:
        await message.answer(TEXTS["errors"]["use_syntax_transfer"])
        return

    if not await check_is_valid_num(message, amount):
        return

    from_user_id = message.from_user.id
    to_user_id = message.reply_to_message.from_user.id

    if from_user_id == to_user_id:
        await message.answer(TEXTS["errors"]["self_transfer_forbidden"])
        return

    success, result_text = transfer_money(from_user_id, to_user_id, amount)
    if success:
        from_balance = get_user_balance(from_user_id)
        to_balance = get_user_balance(to_user_id)
        text = (
            f"✅ {result_text}\n\n"
            f"💰 Сумма: {format_money(amount)}\n"
            f"💳 Ваш баланс: {format_money(from_balance)}\n"
            f"👤 Баланс получателя: {format_money(to_balance)}"
        )
    else:
        # normalize known backend messages to our centralized ones
        normalized = TEXTS["bank"]["transfer_insufficient"] if "Недостаточно" in result_text else result_text
        text = f"❌ {normalized}"
    await message.answer(text)


@bank_router.message(Command("contrib"))
async def add_contribution(message: Message):

    text = random.choice(EASTER_EGGS)
    await message.answer(text)


@bank_router.message(Command("getbc"))
async def getbc_handler(message: Message):
    """Обработчик команды /getbc - выдает случайную награду раз в 4 часа"""
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    # Проверяем, может ли пользователь использовать команду
    if not can_use_getbc(user_id):
        remaining_time = get_getbc_cooldown_remaining(user_id)
        time_str = format_time_remaining(remaining_time)
        
        await message.answer(
            TEXTS["errors"]["getbc_on_cooldown"].format(time=time_str)
        )
        return
    
    # Используем команду и получаем награду
    reward = use_getbc(user_id, username)
    user_data = get_user_data(user_id)
    
    # Формируем сообщение с username если есть
    username_text = f"@{username}" if username else TEXTS["static"]["user_fallback"]
    
    await message.answer(
        TEXTS["templates"]["getbc_reward"].format(
            username=username_text,
            reward=format_money(reward),
            balance=format_money(user_data['balance']),
        )
    )