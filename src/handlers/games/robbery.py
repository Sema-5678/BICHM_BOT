from decimal import Decimal
import random

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BASE_ROBBERY_CHANCE
from filters.chat_types import ChatTypeFilter
from handlers.components.functions import (
    add_crew_member,
    add_money,
    calculate_robbery_chance,
    format_money,
    format_small_number,
    get_crew_display,
    get_user_balance,
    can_afford,
    deduct_money,
)
from handlers.components.callbacks import RobberyCallback
from common.data_for_bot import TEXTS
from config import WIN_ALGORITHM, ROBBERY_CHANCES
from handlers.components.functions import compute_adjusted_win_probability


robbery_router = Router()


@robbery_router.message(Command("robbed"))
async def robbery_start(message: Message):
    try:
        bet = Decimal(message.text.split()[1])
    except:
        await message.answer(TEXTS["errors"]["use_syntax_robbed"])
        return
    if not can_afford(message.from_user.id, bet):
        await message.answer(TEXTS["errors"]["insufficient_bc_heist"])
        return
    old_balance = get_user_balance(message.from_user.id)
    new_balance = deduct_money(message.from_user.id, bet)
    payout_multiplier = 2.2
    text = TEXTS["games"]["robbery"]["start"].format(
        bet=format_money(bet),
        old_balance=format_money(old_balance),
        new_balance=format_money(new_balance),
        base=BASE_ROBBERY_CHANCE,
        multiplier=payout_multiplier,
    )
    keyboard = InlineKeyboardBuilder()
    for idx, member in enumerate(ROBBERY_CHANCES):
        keyboard.button(
            text=member["name"],
            callback_data=RobberyCallback(
                user_id=message.from_user.id,
                action="member_type",
                member_id=str(idx),
                bet=format_small_number(bet),
                crew="",
            ).pack(),
        )
    keyboard.button(
        text=TEXTS["buttons"]["fight"],
        callback_data=RobberyCallback(
            user_id=message.from_user.id,
            action="start",
            bet=format_small_number(bet),
            crew="",
        ).pack(),
    )
    await message.answer(text, reply_markup=keyboard.adjust(3, 1).as_markup())


@robbery_router.callback_query(RobberyCallback.filter())
async def robbery_handler(callback: CallbackQuery, callback_data: RobberyCallback):
    if callback.from_user.id != callback_data.user_id:
        await callback.answer(TEXTS["errors"]["not_your_game"], show_alert=True)
        return
    if callback_data.action == "member_type":
        new_crew = add_crew_member(callback_data.crew, callback_data.member_id)
        success_chance, multiplier = calculate_robbery_chance(new_crew)
        bet_amount = Decimal(callback_data.bet)
        text = TEXTS["games"]["robbery"]["with_team"].format(
            bet=format_money(bet_amount),
            crew=get_crew_display(new_crew),
            chance=success_chance,
            multiplier=f"{multiplier:.2f}",
            count=len(new_crew.split(',')) if new_crew else 0,
        )
        keyboard = InlineKeyboardBuilder()
        available_members = []
        crew_list = new_crew.split(',') if new_crew else []
        for member_id, member_name in enumerate(ROBBERY_CHANCES):
            member_id = str(member_id)
            if member_id not in crew_list:
                available_members.append((member_id, member_name['name']))
        for member_id, member_name in available_members:
            keyboard.button(
                text=member_name,
                callback_data=RobberyCallback(
                    user_id=callback_data.user_id,
                    action="member_type",
                    member_id=str(member_id),
                    bet=callback_data.bet,
                    crew=new_crew,
                ).pack(),
            )
        keyboard.button(
            text=TEXTS["buttons"]["fight"],
            callback_data=RobberyCallback(
                user_id=callback_data.user_id,
                action="start",
                bet=callback_data.bet,
                crew=new_crew,
            ).pack(),
        )
        await callback.message.edit_text(text, reply_markup=keyboard.adjust(max(len(available_members), 1), 1).as_markup())
    elif callback_data.action == "start":
        success_chance, multiplier = calculate_robbery_chance(callback_data.crew)
        print(success_chance, multiplier)
        if WIN_ALGORITHM == "balance":
            final_percent = compute_adjusted_win_probability(callback_data.user_id, success_chance)
            print(final_percent)
        else:
            final_percent = success_chance
        bet_amount = Decimal(callback_data.bet)
        if random.random() <= final_percent:
            win_amount = bet_amount * Decimal(str(multiplier))
            new_balance = add_money(callback_data.user_id, win_amount)
            text = TEXTS["games"]["robbery"]["success"].format(
                bet=format_money(bet_amount),
                multiplier=f"{multiplier:.2f}",
                win=format_money(win_amount),
                balance=format_money(new_balance),
            )
        else:
            new_balance = get_user_balance(callback_data.user_id)
            text = TEXTS["games"]["robbery"]["fail"].format(balance=format_money(new_balance))
        await callback.message.edit_text(text)
    await callback.answer()


