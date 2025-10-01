from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BLACKJACK_BET
from filters.chat_types import ChatTypeFilter
from handlers.components.functions import (
    add_money,
    add_card_to_hand,
    calculate_score,
    decode_cards,
    encode_cards,
    format_money,
    format_small_number,
    get_card_count,
    get_dealer_visible_cards,
    get_user_balance,
    is_valid_bet,
    can_afford,
    deduct_money,
)
from handlers.components.callbacks import BlackjackCallback
from common.data_for_bot import TEXTS


blackjack_router = Router()


async def _validate_and_process_bet(message: Message, bet: Decimal):
    if isinstance(bet, (int, float)):
        bet = Decimal(str(bet))
    if not is_valid_bet(bet):
        await message.answer(TEXTS["errors"]["bet_range"].format(min_val=Decimal('0.01'), max_val=format_money(Decimal('0'))))
        return None, None
    user_id = message.from_user.id
    if not can_afford(user_id, bet):
        await message.answer(TEXTS["errors"]["insufficient_bc_game"])
        return None, None
    old_balance = get_user_balance(user_id)
    new_balance = deduct_money(user_id, bet)
    return old_balance, new_balance


@blackjack_router.message(Command("blackjack"))
async def blackjack_start(message: Message):
    bet = Decimal(str(BLACKJACK_BET))
    result = await _validate_and_process_bet(message, bet)
    if result[0] is None:
        return
    old_balance, new_balance = result
    user_id = message.from_user.id
    player_cards = add_card_to_hand("")
    player_cards = add_card_to_hand(player_cards)
    dealer_cards = add_card_to_hand("")
    dealer_cards = add_card_to_hand(dealer_cards)
    player_score = calculate_score(player_cards)
    text = TEXTS["games"]["blackjack"]["start_spaced"].format(
        bet=format_money(bet),
        old_balance=format_money(old_balance),
        new_balance=format_money(new_balance),
        player_cards=player_cards,
        player_score=player_score,
        dealer_visible=get_dealer_visible_cards(dealer_cards),
    )
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=TEXTS["buttons"]["more"],
        callback_data=BlackjackCallback(
            user_id=user_id,
            action="hit",
            player_cards=encode_cards(player_cards),
            dealer_cards=encode_cards(dealer_cards),
            bet=format_small_number(bet),
        ).pack(),
    )
    keyboard.button(
        text=TEXTS["buttons"]["stand"],
        callback_data=BlackjackCallback(
            user_id=user_id,
            action="stand",
            player_cards=encode_cards(player_cards),
            dealer_cards=encode_cards(dealer_cards),
            bet=format_small_number(bet),
        ).pack(),
    )
    await message.answer(text, reply_markup=keyboard.as_markup())


@blackjack_router.callback_query(BlackjackCallback.filter())
async def blackjack_handler(callback: CallbackQuery, callback_data: BlackjackCallback):
    if callback.from_user.id != callback_data.user_id:
        await callback.answer(TEXTS["errors"]["not_your_game"], show_alert=True)
        return
    user_id = callback_data.user_id
    action = callback_data.action
    player_cards = decode_cards(callback_data.player_cards)
    dealer_cards = decode_cards(callback_data.dealer_cards)
    bet = Decimal(callback_data.bet)
    if action == "hit":
        player_cards = add_card_to_hand(player_cards)
        player_score = calculate_score(player_cards)
        if player_score > 21:
            text = TEXTS["games"]["blackjack"]["bust"].format(
                player_cards=player_cards,
                player_score=player_score,
                lost=format_money(bet),
                balance=format_money(get_user_balance(user_id)),
            )
            await callback.message.edit_text(text)
        else:
            text = TEXTS["games"]["blackjack"]["regular"].format(
                bet=format_money(bet),
                balance=format_money(get_user_balance(user_id)),
                player_cards=player_cards,
                player_score=player_score,
                dealer_visible=get_dealer_visible_cards(dealer_cards),
            )
            keyboard = InlineKeyboardBuilder()
            if get_card_count(player_cards) < 5:
                keyboard.button(
                    text=TEXTS["buttons"]["more"],
                    callback_data=BlackjackCallback(
                        user_id=user_id,
                        action="hit",
                        player_cards=player_cards,
                        dealer_cards=dealer_cards,
                        bet=format_small_number(bet),
                    ).pack(),
                )
            keyboard.button(
                text=TEXTS["buttons"]["stand"],
                callback_data=BlackjackCallback(
                    user_id=user_id,
                    action="stand",
                    player_cards=player_cards,
                    dealer_cards=dealer_cards,
                    bet=format_small_number(bet),
                ).pack(),
            )
            await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
    elif action == "stand":
        from handlers.components.functions import create_card  # local import to avoid cycles
        dealer_cards_list = [dealer_cards[i:i+2] for i in range(0, len(dealer_cards), 2)]
        dealer_score = calculate_score(dealer_cards)
        while dealer_score < 17 and len(dealer_cards_list) < 5:
            new_card = create_card()
            dealer_cards_list.append(new_card)
            dealer_cards = ''.join(dealer_cards_list)
            dealer_score = calculate_score(dealer_cards)
        player_score = calculate_score(player_cards)
        if player_score > 21:
            result = TEXTS["games"]["common"]["lose_bust"]
            new_balance = get_user_balance(user_id)
        elif dealer_score > 21:
            win_amount = bet * 2
            new_balance = add_money(user_id, win_amount)
            result = f"{TEXTS['games']['common']['dealer_busted_prefix']} {TEXTS['labels']['win_amount'].format(amount=format_money(win_amount))}"
        elif player_score > dealer_score:
            win_amount = bet * 2
            new_balance = add_money(user_id, win_amount)
            result = TEXTS["labels"]["win_amount"].format(amount=format_money(win_amount))
        elif player_score < dealer_score:
            result = TEXTS["games"]["common"]["dealer_won"]
            new_balance = get_user_balance(user_id)
        else:
            new_balance = add_money(user_id, bet)
            result = TEXTS["labels"]["draw"]
        text = TEXTS["games"]["blackjack"]["result"].format(
            bet=format_money(bet),
            player_cards=player_cards,
            player_score=player_score,
            dealer_cards=dealer_cards,
            dealer_score=dealer_score,
            result=result,
            balance=format_money(new_balance),
        )
        await callback.message.edit_text(text)
    await callback.answer()


