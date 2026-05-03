from decimal import Decimal

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import AMATEUR_BLACKJACK_BET
from filters.chat_types import ChatTypeFilter
from handlers.components.functions import (
    add_money,
    add_amateur_card_to_hand,
    calculate_amateur_score,
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
from handlers.components.callbacks import AmateurBlackjackCallback
from common.data_for_bot import TEXTS


amateur_blackjack_router = Router()


async def _validate_and_process_bet(message: Message, bet: Decimal):
    if isinstance(bet, (int, float)):
        bet = Decimal(str(bet))
    if not is_valid_bet(bet):
        await message.answer(TEXTS["errors"]["bet_range"].format(min_val=Decimal('0.01'), max_val=format_money(Decimal('0'))))
        return None, None
    user_id = message.from_user.id
    if not await can_afford(user_id, bet):
        await message.answer(TEXTS["errors"]["insufficient_bc_game"])
        return None, None
    old_balance = await get_user_balance(user_id)
    new_balance = await deduct_money(user_id, bet)
    return old_balance, new_balance


@amateur_blackjack_router.message(Command("amateur_blackjack"))
async def amateur_blackjack_start(message: Message):
    bet = Decimal(str(AMATEUR_BLACKJACK_BET))
    result = await _validate_and_process_bet(message, bet)
    if result[0] is None:
        return
    old_balance, new_balance = result
    user_id = message.from_user.id
    player_cards = add_amateur_card_to_hand("")
    player_cards = add_amateur_card_to_hand(player_cards)
    dealer_cards = add_amateur_card_to_hand("")
    dealer_cards = add_amateur_card_to_hand(dealer_cards)
    player_score = calculate_amateur_score(player_cards)
    text = TEXTS["games"]["amateur_blackjack"]["start"].format(
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
        callback_data=AmateurBlackjackCallback(
            user_id=user_id,
            action="hit",
            player_cards=encode_cards(player_cards),
            dealer_cards=encode_cards(dealer_cards),
            bet=format_small_number(bet),
        ).pack(),
    )
    keyboard.button(
        text=TEXTS["buttons"]["stand"],
        callback_data=AmateurBlackjackCallback(
            user_id=user_id,
            action="stand",
            player_cards=encode_cards(player_cards),
            dealer_cards=encode_cards(dealer_cards),
            bet=format_small_number(bet),
        ).pack(),
    )
    await message.answer(text, reply_markup=keyboard.as_markup())


@amateur_blackjack_router.callback_query(AmateurBlackjackCallback.filter())
async def amateur_blackjack_handler(callback: CallbackQuery, callback_data: AmateurBlackjackCallback):
    if callback.from_user.id != callback_data.user_id:
        await callback.answer(TEXTS["errors"]["not_your_game"], show_alert=True)
        return
    user_id = callback_data.user_id
    action = callback_data.action
    player_cards = decode_cards(callback_data.player_cards)
    dealer_cards = decode_cards(callback_data.dealer_cards)
    bet = Decimal(callback_data.bet)
    if action == "hit":
        player_cards = add_amateur_card_to_hand(player_cards)
        dealer_cards = add_amateur_card_to_hand(dealer_cards)
        player_score = calculate_amateur_score(player_cards)
        dealer_score = calculate_amateur_score(dealer_cards)
        if player_score > 21:
            text = TEXTS["games"]["amateur_blackjack"]["bust"].format(
                player_cards=player_cards,
                player_score=player_score,
                dealer_cards=dealer_cards,
                dealer_score=dealer_score,
                lost=format_money(bet),
                balance=format_money(await get_user_balance(user_id)),
            )
            await callback.message.edit_text(text)
        else:
            text = TEXTS["games"]["amateur_blackjack"]["regular"].format(
                bet=format_money(bet),
                balance=format_money(await get_user_balance(user_id)),
                player_cards=player_cards,
                player_score=player_score,
                dealer_visible=get_dealer_visible_cards(dealer_cards),
            )
            keyboard = InlineKeyboardBuilder()
            if get_card_count(player_cards) < 5:
                keyboard.button(
                    text=TEXTS["buttons"]["more"],
                    callback_data=AmateurBlackjackCallback(
                        user_id=user_id,
                        action="hit",
                        player_cards=player_cards,
                        dealer_cards=dealer_cards,
                        bet=format_small_number(bet),
                    ).pack(),
                )
            keyboard.button(
                text=TEXTS["buttons"]["stand"],
                callback_data=AmateurBlackjackCallback(
                    user_id=user_id,
                    action="stand",
                    player_cards=player_cards,
                    dealer_cards=dealer_cards,
                    bet=format_small_number(bet),
                ).pack(),
            )
            await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
    elif action == "stand":
        player_score = calculate_amateur_score(player_cards)
        dealer_score = calculate_amateur_score(dealer_cards)
        if player_score > 21:
            result = TEXTS["games"]["common"]["lose_bust"]
            new_balance = await get_user_balance(user_id)
        elif dealer_score > 21:
            win_amount = bet * 2
            new_balance = await add_money(user_id, win_amount)
            result = f"{TEXTS['games']['common']['dealer_busted_prefix']} {TEXTS['labels']['win_amount'].format(amount=format_money(win_amount))}"
        elif player_score > dealer_score:
            win_amount = bet * 2
            new_balance = await add_money(user_id, win_amount)
            result = TEXTS["labels"]["win_amount"].format(amount=format_money(win_amount))
        elif player_score < dealer_score:
            result = TEXTS["games"]["common"]["dealer_won"]
            new_balance = await get_user_balance(user_id)
        else:
            new_balance = await add_money(user_id, bet)
            result = TEXTS["labels"]["draw"]
        text = TEXTS["games"]["amateur_blackjack"]["result"].format(
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


