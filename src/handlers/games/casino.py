import asyncio
from decimal import Decimal
import random

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import MAX_CASINO_ROUNDS, MINI_CASINO_BET, WIN_ALGORITHM
from filters.chat_types import ChatTypeFilter
from handlers.components.functions import (
    add_money,
    can_afford,
    check_is_valid_num,
    compute_adjusted_win_probability,
    deduct_money,
    format_money,
    get_user_balance,
    is_valid_bet,
    validate_casino_bet,
)
from handlers.components.callbacks import CasinoCallback
from common.data_for_bot import TEXTS
from utils.sqlite_storage import get_user_data


casino_router = Router()


@casino_router.message(Command("casino"))
async def casino_start(message: Message):
    try:
        bet = Decimal(message.text.split()[1])
    except:
        await message.answer(TEXTS["errors"]["use_syntax_casino"])
        return
    # if not is_valid_bet(bet):
    #     await message.answer(TEXTS["errors"]["bet_range"].format(min_val=Decimal('0.01'), max_val=format_money(bet)))
    #     return
    if not await check_is_valid_num(message, bet):
        return
    user_id = message.from_user.id
    if not await can_afford(user_id, bet):
        await message.answer(TEXTS["errors"]["insufficient_bc_game"])
        return
    old_balance = await get_user_balance(user_id)
    new_balance = await deduct_money(user_id, bet)
    
    base_p = Decimal("0.50")
    adjusted_p = compute_adjusted_win_probability(user_id, message.chat.id, base_p)
    # print(adjusted_p)
    dealer_number = random.randint(1, 20)
    is_win = random.random() < adjusted_p
    if is_win:
        player_number = (
            random.randint(dealer_number, 20) if dealer_number < 20 else dealer_number
        )
        new_balance = await add_money(user_id, bet*2)

        text = TEXTS["games"]["casino"]["win"].format(
            bet=format_money(bet),
            old_balance=format_money(old_balance),
            new_balance=format_money(new_balance),
            player=player_number,
            dealer=dealer_number,
        )

        # text = TEXTS["games"]["casino"]["take"].format(
        #     amount=format_money(bet), balance=format_money(new_balance)
        # )
        await message.answer(text)
        # keyboard = InlineKeyboardBuilder()
        # keyboard.button(
        #     text=TEXTS["buttons"]["next"],
        #     callback_data=CasinoCallback(
        #         user_id=user_id, action="continue", initial_bet=str(bet), round_num=2
        #     ).pack(),
        # )
        # keyboard.button(
        #     text=TEXTS["buttons"]["take_win"].format(
        #         amount=format_money(bet * Decimal("2"))
        #     ),
        #     callback_data=CasinoCallback(
        #         user_id=user_id, action="take", initial_bet=str(bet), round_num=1
        #     ).pack(),
        # )
        # await message.answer(text)
    else:
        player_number = (
            random.randint(1, dealer_number - 1) if dealer_number > 1 else dealer_number
        )
        text = TEXTS["games"]["casino"]["lose"].format(
            old_balance=format_money(old_balance),
            bet=format_money(bet),
            new_balance=format_money(new_balance),
            player=player_number,
            dealer=dealer_number,
            lost=format_money(bet),
        )
        await message.answer(text)



casino_dice_dict = {
    64: {
        "text": "🎉 Джекпот 777 ⭐⭐⭐",
        "prize": 25,
        "combination": "777",
    },
    1: {
        "text": "🎉 Джекпот BAR",
        "prize": 8,
        "combination": "BAR",
    },
    43: {
        "text": "🎉 Джекпот 'Лимончик' 🍋🍋🍋",
        "prize": 18,
        "combination": "🍋🍋🍋",
    },
    22: {
        "text": "🎉 Джекпот 🍒🍒🍒",
        "prize": 15,
        "combination": "🍒🍒🍒",
    },
}


@casino_router.message(F.dice)
async def handle_dice(message: Message):
    user_data = await get_user_data(message.from_user.id)
    if user_data['balance'] < MINI_CASINO_BET:
        await message.answer('У вас недостаточно баланса')
        return
    if message.forward_from_chat is not None or message.forward_from is not None:
        await message.answer('Нельзя пересылать сообщения с 🎰, они не учитываются')
        return
        
    await asyncio.sleep(2.1)
    dice = message.dice  # объект aiogram.types.Dice
    emoji = dice.emoji  # например, "🎰"
    value = dice.value  # случайное значение (int)

    # await message.answer(f"🎰 Выпало значение: {value}")
    win = casino_dice_dict.get(
        value,
        {
            "text": "Повезёт в следующий раз",
            "prize": -1,
            "combination": "None",
        }
    )
    win_bet = win["prize"] * MINI_CASINO_BET
    new_balance = await add_money(message.from_user.id, win_bet)
    prize_text = f"   + {format_money(win_bet)}" if win["prize"] > 0 else f"   - {format_money(-win_bet)}"

    text = f'{win["text"]}{prize_text}\n🎰 Баланс: {format_money(new_balance)}'
    await message.reply(text=text)
