from decimal import Decimal

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import MIN_POSITIVE_NUM
from handlers.components.callbacks import TTTCallback
from handlers.components.functions import (
    add_money,
    can_afford,
    check_is_valid_num,
    deduct_money,
    format_money,
    format_small_number,
    get_user_balance,
)
from common.data_for_bot import TEXTS
import random


ttt_router = Router()


MAX_TTT_BET = Decimal("50")


def _empty_board() -> str:
    return "---------"  # 9 символов, '-' = пусто


def _count_moves(state: str) -> int:
    return 9 - state.count('-')


def _current_mark(state: str) -> str:
    return 'X' if _count_moves(state) % 2 == 0 else 'O'


def _winner(state: str) -> str | None:
    lines = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
        (0, 4, 8), (2, 4, 6),             # diagonals
    ]
    for a, b, c in lines:
        if state[a] != '-' and state[a] == state[b] == state[c]:
            return state[a]
    return None


def _build_board_kbd(p1: int, p2: int, state: str, bet: Decimal) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for i in range(9):
        cell = state[i]
        text = cell if cell != '-' else ' '
        if cell == '-':
            # В state сразу кладём результат нажатия (X/O на эту клетку)
            mark = _current_mark(state)
            new_state = state[:i] + mark + state[i+1:]
            cb = TTTCallback(player1_id=p1, player2_id=p2, state=new_state, action="move", bet=format_small_number(bet)).pack()
        else:
            cb = TTTCallback(player1_id=p1, player2_id=p2, state=state, action="noop", bet=format_small_number(bet)).pack()
        kb.button(text=text, callback_data=cb)
    return kb.adjust(3, 3, 3)


async def _resolve_name(user_id: int, message: Message) -> str:
    try:
        chat = await message.bot.get_chat(user_id)
        if chat.username:
            return f"@{chat.username}"
        if chat.first_name or chat.last_name:
            return (chat.first_name or "") + (" " + chat.last_name if chat.last_name else "")
    except:
        pass
    return TEXTS["bank"]["user_fallback_name"].format(user_id=user_id)


async def _format_start_text(p1: int, p2: int, bet: Decimal, message: Message, turn_mark: str) -> str:
    p1_name = await _resolve_name(p1, message)
    p2_name = await _resolve_name(p2, message)
    return (
        f"{TEXTS['games']['tictactoe']['title']}\n\n"
        f"💰 Ставка: {format_money(bet)}\n"
        f"Игрок X: {p1_name}\n"
        f"Игрок O: {p2_name}\n"
        f"Ходит: {turn_mark}"
    )


@ttt_router.message(Command("tictactoe"))
async def ttt_invite(message: Message):
    # Ожидаем ответ на чужое сообщение и сумму ставки
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(TEXTS["games"]["tictactoe"]["invite_need_reply"])
        return
    try:
        bet = Decimal(parts[1])
    except:
        await message.answer(TEXTS["games"]["tictactoe"]["invalid_bet"])
        return
    # if bet <= MIN_POSITIVE_NUM or bet >= MAX_TTT_BET:
    #     await message.answer(TEXTS["games"]["tictactoe"]["invalid_bet"])
    #     return

    if not await check_is_valid_num(message, bet, max=MAX_TTT_BET):
        return
    
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.answer(TEXTS["games"]["tictactoe"]["invite_need_reply"])
        return
    
    # print(message.reply_to_message.text)
    p1 = message.from_user.id
    p2 = message.reply_to_message.from_user.id
    if p1 == p2:
        await message.answer(TEXTS["games"]["tictactoe"]["self_play_forbidden"])
        return
    # Формируем приглашение: согласие требуется, ставки не списываем
    state = _empty_board()
    invited_user = message.reply_to_message.from_user
    invited_name = (
        (f"@{invited_user.username}" if invited_user.username else None)
        or invited_user.full_name
        or TEXTS["bank"]["user_fallback_name"].format(user_id=p2)
    )
    invite_text = (
        f"{TEXTS['games']['tictactoe']['title']}\n\n"
        f"💰 Ставка: {format_money(bet)}\n"
        f"Приглашён: {invited_name}"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="Принять", callback_data=TTTCallback(player1_id=p1, player2_id=p2, state=state, action="accept", bet=format_small_number(bet)).pack())
    kb.button(text="Отклонить", callback_data=TTTCallback(player1_id=p1, player2_id=p2, state=state, action="reject", bet=format_small_number(bet)).pack())
    await message.answer(invite_text, reply_markup=kb.adjust(2).as_markup())


@ttt_router.callback_query(TTTCallback.filter())
async def ttt_handler(callback: CallbackQuery, callback_data: TTTCallback):
    action = callback_data.action
    p1 = callback_data.player1_id
    p2 = callback_data.player2_id
    state = callback_data.state
    bet = Decimal(callback_data.bet)

    if action == "reject":
        if callback.from_user.id != p2:
            await callback.answer(TEXTS["errors"]["not_your_game"], show_alert=True)
            return
        await callback.message.edit_text("🚫 Приглашение отклонено")
        await callback.answer()
        return

    if action == "accept":
        if callback.from_user.id != p2:
            await callback.answer(TEXTS["errors"]["not_your_game"], show_alert=True)
            return
        # Проверим балансы обоих только сейчас
        if not can_afford(p1, bet) or not can_afford(p2, bet):
            await callback.message.edit_text(TEXTS["games"]["tictactoe"]["opponent_insufficient"])
            await callback.answer()
            return
        # Списываем ставки
        deduct_money(p1, bet)
        deduct_money(p2, bet)
        # Случайно выбираем первого игрока; для логики первый всегда тот, кто в поле player1_id
        first = random.choice([p1, p2])
        if first == p2:
            p1, p2 = p2, p1
        state = _empty_board()
        # Первый ход делает X (player1_id)
        text = await _format_start_text(p1, p2, bet, callback.message, 'X')
        kb = _build_board_kbd(p1, p2, state, bet)
        await callback.message.edit_text(text, reply_markup=kb.as_markup())
        await callback.answer()
        return

    if action == "noop":
        await callback.answer("Эта клетка уже занята")
        return

    if action == "move":
        user_id = callback.from_user.id
        if user_id not in (p1, p2):
            await callback.answer(TEXTS["errors"]["not_your_game"], show_alert=True)
            return
        # Ход всегда у player1_id; проверяем, что он и нажал
        if user_id != p1:
            await callback.answer(TEXTS["games"]["tictactoe"]["not_your_turn"], show_alert=True)
            return
        new_state = state
        w = _winner(new_state)
        is_draw = (w is None and '-' not in new_state)
        if w is not None or is_draw:
            if w is not None:
                # Побеждает всегда текущий p1 (тот, кто ходил последним)
                winner_id = p1
                win_amount = bet * Decimal('2.01')
                add_money(winner_id, win_amount)
                mark_label = w
                print(mark_label)
                winner_name = await _resolve_name(winner_id, callback.message)
                # Балансы и дельты после выплаты
                p1_balance = get_user_balance(p1)
                p2_balance = get_user_balance(p2)
                winner_delta = win_amount - bet
                loser_delta = -bet
                def fmt_delta(x: Decimal) -> str:
                    return ("+" + format_money(x)) if x > 0 else ("-" + format_money(-x) if x < 0 else format_money(0))
                p1_name = await _resolve_name(p1, callback.message)
                p2_name = await _resolve_name(p2, callback.message)

                next_turn = 'O' if w == 'X' else 'X'

                result_text = (
                    TEXTS["games"]["tictactoe"]["win"].format(mark=mark_label, name=winner_name)
                    + "\n\n"
                    # + f"X {p1_name}: {format_money(p1_balance)} ({fmt_delta(winner_delta if winner_id==p1 else loser_delta)})\n"
                    # + f"O {p2_name}: {format_money(p2_balance)} ({fmt_delta(winner_delta if winner_id==p2 else loser_delta)})"
                    + f"{w} {p1_name}: {format_money(p1_balance)} ({fmt_delta(winner_delta)})\n"
                    + f"{next_turn} {p2_name}: {format_money(p2_balance)} ({fmt_delta(loser_delta)})\n"

                )
            else:
                # Ничья → вернуть ставки
                add_money(p1, bet)
                add_money(p2, bet)
                # Балансы и нулевая дельта
                p1_balance = get_user_balance(p1)
                p2_balance = get_user_balance(p2)
                p1_name = await _resolve_name(p1, callback.message)
                p2_name = await _resolve_name(p2, callback.message)
                zero = Decimal('0')
                def fmt_delta(x: Decimal) -> str:
                    return ("+" + format_money(x)) if x > 0 else ("-" + format_money(-x) if x < 0 else format_money(0))
                result_text = (
                    TEXTS["games"]["tictactoe"]["draw"]
                    + "\n\n"
                    + f"X {p1_name}: {format_money(p1_balance)} ({fmt_delta(zero)})\n"
                    + f"O {p2_name}: {format_money(p2_balance)} ({fmt_delta(zero)})"
                )
            final_text = result_text
            await callback.message.edit_text(final_text)
            await callback.answer()
            return
        # Смена сторон: меняем местами player1_id/player2_id, чтобы ход всегда был у нового player1_id
        p1, p2 = p2, p1
        # Инвертируем последний символ текущего текста (X <-> O), сохраняяостальной текст
        current_text = callback.message.text or 'X'
        current_text = current_text.rstrip()
        last = current_text[-1] if current_text else 'X'
        next_turn = 'O' if last == 'X' else 'X'
        text = current_text[:-1] + next_turn if current_text else next_turn
        kb = _build_board_kbd(p1, p2, new_state, bet)
        await callback.message.edit_text(text, reply_markup=kb.as_markup())
        await callback.answer()
        return

    await callback.answer()


