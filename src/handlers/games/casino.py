from decimal import Decimal
import random

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import MAX_CASINO_ROUNDS, WIN_ALGORITHM
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
    if not can_afford(user_id, bet):
        await message.answer(TEXTS["errors"]["insufficient_bc_game"])
        return
    old_balance = get_user_balance(user_id)
    new_balance = deduct_money(user_id, bet)
    base_p = 0.50
    adjusted_p = base_p if WIN_ALGORITHM == "legacy" else compute_adjusted_win_probability(user_id, base_p)
    dealer_number = random.randint(1, 20)
    is_win = random.random() < adjusted_p
    if is_win:
        player_number = random.randint(dealer_number, 20) if dealer_number < 20 else dealer_number
        text = TEXTS["games"]["casino"]["win"].format(
            bet=format_money(bet),
            old_balance=format_money(old_balance),
            new_balance=format_money(new_balance),
            player=player_number,
            dealer=dealer_number,
        )
        keyboard = InlineKeyboardBuilder()
        keyboard.button(
            text=TEXTS["buttons"]["next"],
            callback_data=CasinoCallback(user_id=user_id, action="continue", initial_bet=str(bet), round_num=2).pack(),
        )
        keyboard.button(
            text=TEXTS["buttons"]["take_win"].format(amount=format_money(bet * Decimal('2'))),
            callback_data=CasinoCallback(user_id=user_id, action="take", initial_bet=str(bet), round_num=1).pack(),
        )
        await message.answer(text, reply_markup=keyboard.as_markup())
    else:
        player_number = random.randint(1, dealer_number - 1) if dealer_number > 1 else dealer_number
        text = TEXTS["games"]["casino"]["lose"].format(
            old_balance=format_money(old_balance),
            new_balance=format_money(new_balance),
            player=player_number,
            dealer=dealer_number,
            lost=format_money(bet),
        )
        await message.answer(text)


@casino_router.callback_query(CasinoCallback.filter())
async def casino_handler(callback: CallbackQuery, callback_data: CasinoCallback):
    if callback.from_user.id != callback_data.user_id:
        await callback.answer(TEXTS["errors"]["not_your_game"], show_alert=True)
        return
    user_id = callback_data.user_id
    initial_bet = Decimal(callback_data.initial_bet)
    round_num = callback_data.round_num
    if round_num > MAX_CASINO_ROUNDS:
        await callback.answer(TEXTS["errors"]["casino_round_limit"], show_alert=True)
        return
    last_bet = initial_bet * (Decimal('2') ** (round_num - 1))
    current_bet = last_bet * Decimal('2')
    if not validate_casino_bet(initial_bet, round_num):
        await callback.answer(TEXTS["errors"]["casino_bet_too_large"], show_alert=True)
        return
    if callback_data.action == "continue":
        base_p = 0.50
        adjusted_p = base_p if WIN_ALGORITHM == "legacy" else compute_adjusted_win_probability(user_id, base_p)
        dealer_number = random.randint(1, 20)
        is_win = random.random() < adjusted_p
        player_number = random.randint(dealer_number, 20) if is_win and dealer_number < 20 else dealer_number if is_win else random.randint(1, dealer_number - 1) if dealer_number > 1 else dealer_number
        if is_win:
            next_round = round_num + 1
            text = TEXTS["games"]["casino"]["continue"].format(
                current=format_money(current_bet),
                balance=format_money(get_user_balance(user_id)),
                player=player_number,
                dealer=dealer_number,
            )
            keyboard = InlineKeyboardBuilder()
            keyboard.button(
                text=TEXTS["buttons"]["next"],
                callback_data=CasinoCallback(user_id=user_id, action="continue", initial_bet=str(initial_bet), round_num=next_round).pack(),
            )
            keyboard.button(
                text=TEXTS["buttons"]["take_win"].format(amount=format_money(current_bet)),
                callback_data=CasinoCallback(user_id=user_id, action="take", initial_bet=str(initial_bet), round_num=round_num).pack(),
            )
            await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
        else:
            text = TEXTS["games"]["casino"]["lose"].format(
                old_balance="",
                new_balance="",
                player=player_number,
                dealer=dealer_number,
                lost=format_money(initial_bet),
            ) + TEXTS["labels"]["could_take"].format(amount=format_money(last_bet))
            await callback.message.edit_text(text)
    elif callback_data.action == "take":
        new_balance = add_money(user_id, current_bet)
        text = TEXTS["games"]["casino"]["take"].format(amount=format_money(current_bet), balance=format_money(new_balance))
        await callback.message.edit_text(text)
    await callback.answer()


