from aiogram.filters.callback_data import CallbackData

class BlackjackCallback(CallbackData, prefix="b"):  # было "bj" → стало "b"
    user_id: int
    action: str
    player_cards: str
    dealer_cards: str
    bet: str

class AmateurBlackjackCallback(CallbackData, prefix="a"):  # было "abj" → стало "a"
    user_id: int
    action: str
    player_cards: str
    dealer_cards: str
    bet: str

class CasinoCallback(CallbackData, prefix="c"):  # было "casino" → стало "c"
    user_id: int
    action: str
    initial_bet: str
    round_num: int

class RobberyCallback(CallbackData, prefix="r"):  # было "rob" → стало "r"
    user_id: int
    action: str
    member_id: str | None = None
    bet: str
    crew: str = ""

# Крестики-нолики: максимально короткий колбэк
class TTTCallback(CallbackData, prefix="t"):
    # player1_id, player2_id — id игроков; state — новое/текущее поле (9 символов)
    # action — действие; bet — ставка.
    player1_id: int
    player2_id: int
    state: str
    action: str
    bet: str