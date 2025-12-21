from decimal import ROUND_HALF_UP, Decimal, getcontext
import math
import random
from datetime import datetime
import os
import time
from config import (
    BASE_ROBBERY_CHANCE,
    BASE_ROBBERY_PAYOUT,
    GET_BC_TIME_LIMIT,
    GET_BC_MIN_BC,
    GET_BC_MAX_BC,
    ROBBERY_ITEMS_PER_ROW,
    MAX_BALANCE,
    MAX_BET,
    MAX_LOAN,
    ROBBERY_CHANCES,
    TOP_RICH_COUNT,
    MIN_POSITIVE_NUM,
    chats_bonuses,
)
from utils.json_engine import get_user_data, update_user_data, database_path
from common.data_for_bot import TEXTS

MAX_BALANCE = Decimal(str(MAX_BALANCE))
MAX_BET = Decimal(str(MAX_BET))



def items_on_page(idx):
    # print((*(ITEMS_PER_ROW,)*((idx)//ITEMS_PER_ROW), idx%ITEMS_PER_ROW, 1))
    return  (*(ROBBERY_ITEMS_PER_ROW,)*((idx)//ROBBERY_ITEMS_PER_ROW), ROBBERY_ITEMS_PER_ROW)

def is_valid_num(amount, max=MAX_BET, min=MIN_POSITIVE_NUM):
    """Проверяет, что число валидно"""
    if isinstance(amount, (int, float)):
        amount = Decimal(str(amount))
    return min <= amount <= max


async def check_is_valid_num(msg, amount, max=MAX_BET, min=MIN_POSITIVE_NUM):
    if not is_valid_num(amount, max=max, min=min):
        await msg.answer(TEXTS["errors"]["invalid_number"].format(max=max, min=min))
        return False
    return True


def format_money(amount, currency=None):
    if currency is None:
        currency = "BC"
    elif currency == "rub":
        currency = "₽"
    elif currency == "bc":
        currency = "BC"
        
    """Форматирует денежную сумму с разделителями тысяч пробелами.
    Убирает лишние нули после запятой и точку, если они не нужны."""
    if isinstance(amount, (int, float)):
        amount = Decimal(str(amount))

    # Округляем до 2 знаков после запятой
    amount_rounded = amount.quantize(MIN_POSITIVE_NUM, rounding=ROUND_HALF_UP)
    
    # Преобразуем в строку и убираем лишние нули и точку, если они не нужны
    amount_str = f"{amount_rounded:.2f}"  # Используем достаточное количество знаков
    if '.' in amount_str:
        # Убираем лишние нули в конце
        amount_str = amount_str.rstrip('0')
        # Если после точки ничего не осталось, убираем и точку
        if amount_str.endswith('.'):
            amount_str = amount_str[:-1]
    
    # Разделяем целую и дробную части
    if '.' in amount_str:
        integer_part, decimal_part = amount_str.split('.')
        # Если дробная часть не пустая и не состоит из нулей, оставляем её
        if decimal_part and int(decimal_part) != 0:
            # Оставляем только значащие цифры
            decimal_part = decimal_part.rstrip('0')
            amount_str = f"{integer_part}.{decimal_part}"
        else:
            amount_str = integer_part
    else:
        integer_part = amount_str
    
    # Форматируем целую часть с разделителями тысяч
    try:
        integer_part = int(integer_part)
        formatted_integer = "{:,}".format(integer_part).replace(",", " ")
    except (ValueError, TypeError):
        formatted_integer = str(integer_part)
    
    # Собираем результат
    result = formatted_integer
    if '.' in amount_str and int(decimal_part) != 0:
        result = f"{formatted_integer}.{decimal_part}"
    
    return f"{result} {currency}"

    # # Добавляем пробелы каждые 3 цифры с конца
    # formatted_integer = ""
    # for i, char in enumerate(reversed(integer_part)):
    #     if i > 0 and i % 3 == 0:
    #         formatted_integer = " " + formatted_integer
    #     formatted_integer = char + formatted_integer

    # return f"{formatted_integer}.{decimal_part} {currency}"


def format_small_number(num):
    """Форматирует число для callback_data"""
    if isinstance(num, Decimal):
        # Убираем лишние нули для экономии места
        num_str = f"{num:.2f}"
        if num_str.endswith(".00"):
            return num_str[:-3]
        elif num_str.endswith("0"):
            return num_str[:-1]
        return num_str
    num_str = f"{float(num):.2f}"
    if num_str.endswith(".00"):
        return num_str[:-3]
    elif num_str.endswith("0"):
        return num_str[:-1]
    return num_str


def is_valid_bet(amount):
    if isinstance(amount, (int, float)):
        amount = Decimal(str(amount))
    return MIN_POSITIVE_NUM <= amount <= MAX_BET


def can_afford(user_id, amount):
    user_data = get_user_data(user_id)
    if isinstance(amount, (int, float)):
        amount = Decimal(str(amount))
    return user_data["balance"] >= amount


def deduct_money(user_id, amount):
    user_data = get_user_data(user_id)
    if isinstance(amount, (int, float)):
        amount = Decimal(str(amount))

    user_data["balance"] -= amount
    if user_data["balance"] < Decimal("0"):
        user_data["balance"] = Decimal("0")

    update_user_data(user_id, user_data)
    return user_data["balance"]


def add_money(user_id, amount):
    user_data = get_user_data(user_id)
    if isinstance(amount, (int, float)):
        amount = Decimal(str(amount))

    user_data["balance"] += amount
    if user_data["balance"] > MAX_BALANCE:
        user_data["balance"] = MAX_BALANCE

    update_user_data(user_id, user_data)
    return user_data["balance"]


def get_user_balance(user_id):
    return get_user_data(user_id)["balance"]


def validate_casino_bet(initial_bet, round_num):
    if isinstance(initial_bet, (int, float)):
        initial_bet = Decimal(str(initial_bet))
    current_bet = initial_bet * (Decimal("2") ** (round_num - 1))
    return current_bet <= MAX_BET * Decimal("100")


def create_card():
    suits = ["♠", "♥", "♦", "♣"]
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "J", "Q", "K", "A"]
    return random.choice(ranks) + random.choice(suits)


def encode_cards(cards_str):
    """Кодирует карты в компактный формат для callback_data"""
    if not cards_str:
        return ""

    # Маппинг только мастей (ранги остаются как есть)
    suit_map = {"♠": "1", "♥": "2", "♦": "3", "♣": "4"}

    encoded = ""
    for i in range(0, len(cards_str), 2):
        if i + 1 < len(cards_str):
            rank = cards_str[i]
            suit = cards_str[i + 1]
            encoded += rank + suit_map.get(suit, suit)

    return encoded


def decode_cards(encoded_cards):
    """Декодирует карты из компактного формата"""
    if not encoded_cards:
        return ""

    # Обратный маппинг только мастей (ранги остаются как есть)
    suit_map = {"1": "♠", "2": "♥", "3": "♦", "4": "♣"}

    decoded = ""
    for i in range(0, len(encoded_cards), 2):
        if i + 1 < len(encoded_cards):
            rank = encoded_cards[i]
            suit = encoded_cards[i + 1]
            decoded += rank + suit_map.get(suit, suit)

    return decoded


def calculate_score(cards_str):
    if not cards_str or len(cards_str) % 2 != 0:
        return 0
    score = 0
    aces = 0
    for i in range(0, len(cards_str), 2):
        card = cards_str[i : i + 2]
        rank = card[0]
        if rank in ["J", "Q", "K"]:
            score += 10
        elif rank == "A":
            score += 11
            aces += 1
        else:
            score += int(rank)
    while score > 21 and aces > 0:
        score -= 10
        aces -= 1
    return score


def get_dealer_visible_cards(dealer_cards_str):
    if not dealer_cards_str or len(dealer_cards_str) < 2:
        return "?"
    if len(dealer_cards_str) == 2:
        return dealer_cards_str + "?"
    else:
        return dealer_cards_str[:-2] + "?"


def format_cards_display(cards_str):
    if not cards_str:
        return ""
    cards = [cards_str[i : i + 2] for i in range(0, len(cards_str), 2)]
    return " ".join(cards)


def add_card_to_hand(hand_str):
    new_card = create_card()
    return hand_str + new_card


def add_card_to_hand_encoded(hand_str):
    """Добавляет карту в закодированном формате"""
    new_card = create_card()
    encoded_card = encode_cards(new_card)
    return hand_str + encoded_card


def get_card_count(cards_str):
    if not cards_str:
        return 0
    return len(cards_str) // 2


def create_amateur_card():
    suits = ["♠", "♥", "♦", "♣"]
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "A"]
    return random.choice(ranks) + random.choice(suits)


def calculate_amateur_score(cards_str):
    if not cards_str or len(cards_str) % 2 != 0:
        return 0
    score = 0
    for i in range(0, len(cards_str), 2):
        card = cards_str[i : i + 2]
        rank = card[0]
        if rank == "A":
            score += 10
        else:
            score += int(rank)
    return score


def add_amateur_card_to_hand(hand_str):
    new_card = create_amateur_card()
    return hand_str + new_card


def calculate_robbery_chance(crew_str):
    chance = BASE_ROBBERY_CHANCE
    cost_percentage = 0
    if crew_str:
        crew_ids = crew_str.split(",")
        for member_id in crew_ids:

            curr_chances = ROBBERY_CHANCES[int(member_id)]
            chance += curr_chances["chance"]
            cost_percentage += curr_chances["cost_percentage"]

    final_chance = chance
    final_multiplier = BASE_ROBBERY_PAYOUT - cost_percentage
    # print(final_chance, final_multiplier)
    return final_chance, final_multiplier


def get_crew_display(crew_str):
    if not crew_str:
        return TEXTS["games"]["robbery"]["crew_empty"]
    crew_ids = crew_str.split(",")
    text = TEXTS["games"]["robbery"]["crew_ready"] + "\n"
    for member_id in crew_ids:
        member = ROBBERY_CHANCES[int(member_id)]
        text += f"+ {member['name']}: {member['chance']*100:.2f}% к удаче (стоимость: {member['cost_percentage']*100:.2f}% от выигрыша)\n"
    return text


def add_crew_member(crew_str, new_member_id):
    if not crew_str:
        return new_member_id
    crew_ids = crew_str.split(",")
    if new_member_id in crew_ids or len(crew_ids) >= len(ROBBERY_CHANCES):
        return crew_str
    crew_ids.append(new_member_id)
    return ",".join(crew_ids)


def get_all_users_data():
    users_data = []
    users_dir_path = os.path.join(database_path, "users")
    if not os.path.exists(users_dir_path):
        return []
    for filename in os.listdir(users_dir_path):
        if filename.endswith(".json"):
            user_id = int(filename.split(".")[0])
            try:
                user_data = get_user_data(user_id)
                users_data.append((user_id, user_data))
            except:
                continue
    return users_data


def get_top_rich(limit=TOP_RICH_COUNT):
    users_data = get_all_users_data()
    users_data.sort(key=lambda x: x[1]["balance"] + x[1]["deposit"], reverse=True)
    return users_data[:limit]


def transfer_money(from_user_id, to_user_id, amount):
    from_user_data = get_user_data(from_user_id)
    to_user_data = get_user_data(to_user_id)
    if isinstance(amount, (int, float)):
        amount = Decimal(str(amount))
    if from_user_data["balance"] < amount:
        return False, "Недостаточно средств"
    from_user_data["balance"] -= amount
    to_user_data["balance"] += amount
    update_user_data(from_user_id, from_user_data)
    update_user_data(to_user_id, to_user_data)
    return True, "Перевод успешно выполнен"


def take_loan(user_id, amount):
    user_data = get_user_data(user_id)
    if isinstance(amount, (int, float)):
        amount = Decimal(str(amount))
    loan = {
        "amount": float(amount),
        "taken_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "interest_rate": 0.5,
    }
    user_data["loans"].append(loan)
    user_data["debt"] += amount
    user_data["balance"] += amount
    user_data["credit_rating"] -= 5
    update_user_data(user_id, user_data)
    return user_data


def pay_debt(user_id, amount):
    user_data = get_user_data(user_id)
    if isinstance(amount, (int, float)):
        amount = Decimal(str(amount))
    if amount > user_data["debt"]:
        amount = user_data["debt"]
    user_data["balance"] -= amount
    user_data["debt"] -= amount
    user_data["credit_rating"] += 2
    update_user_data(user_id, user_data)
    return user_data


# Добавляем в существующий файл
def calculate_max_loan(credit_rating):
    """Рассчитывает максимальный доступный кредит"""
    base_amount = MAX_LOAN

    return base_amount
    # base_amount = Decimal('1000')
    # rating_bonus = Decimal(str(credit_rating)) * Decimal('10')
    # return base_amount + rating_bonus


def can_use_getbc(user_id):
    """Проверяет, может ли пользователь использовать команду /getbc"""
    user_data = get_user_data(user_id)
    current_time = int(time.time())
    last_use_time = user_data.get("getbc_time", 0)

    return current_time - last_use_time >= GET_BC_TIME_LIMIT


def get_getbc_cooldown_remaining(user_id):
    """Возвращает оставшееся время до возможности использования /getbc в секундах"""
    user_data = get_user_data(user_id)
    current_time = int(time.time())
    last_use_time = user_data.get("getbc_time", 0)

    elapsed = current_time - last_use_time
    remaining = GET_BC_TIME_LIMIT - elapsed

    return max(0, remaining)


def format_time_remaining(seconds):
    """Форматирует оставшееся время в читаемый вид"""
    if seconds <= 0:
        return "0 секунд"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}ч {minutes}м {secs}с"
    elif minutes > 0:
        return f"{minutes}м {secs}с"
    else:
        return f"{secs}с"


def generate_getbc_reward():
    """Генерирует случайную награду для команды /getbc"""
    # Генерируем случайное число от GET_BC_MIN_BC до GET_BC_MAX_BC с точностью до 0.01
    reward = random.uniform(GET_BC_MIN_BC, GET_BC_MAX_BC)
    return Decimal(str(round(reward, 2)))


def use_getbc(user_id, username=None):
    """Использует команду /getbc и возвращает награду"""
    user_data = get_user_data(user_id)
    current_time = int(time.time())

    # Генерируем награду
    reward = generate_getbc_reward()

    # Обновляем время последнего использования
    user_data["getbc_time"] = current_time

    # Обновляем username если передан
    if username:
        user_data["username"] = username

    # Добавляем награду к балансу
    user_data["balance"] += reward

    # Сохраняем данные
    update_user_data(user_id, user_data)

    return reward


def get_winning_chance(balance: Decimal) -> float:
    """
    Одна аппроксимирующая функция по всем заданным точкам.
    f(x) = 70 - 3 * (ln(x+1))**0.95

    Возвращает значения в пределах [0, 100].


    x=0.01 → ~68 ✅
    x=1 → ~65 ✅
    x=10 → ~60 ✅
    x=100 → ~54 ✅
    x=500 → ~50 ✅
    x=1000 → ~48 ✅
    x=10000→ ~40 ✅
    
    """
    if balance < 0:
        raise ValueError("x должно быть >= 0")
    if balance >= 500:
        return 51

    value = 70 - 3 * (math.log(balance + 1)) ** 0.95
    return max(0, min(100, value))


def win_chance(x: Decimal) -> Decimal:
    # x = float(x)
    if x>Decimal("1000"):
        return Decimal("50.5")
    if x < Decimal("0.01"):
        return Decimal('68')
    return Decimal("-0.016") * x + Decimal("68")


def compute_adjusted_win_probability(user_id: int, chat_id,  base_probability: float) -> float:
    """
    Converts the balance-based chance into a multiplier around a neutral point (50%),
    then scales a game's base probability.
    - base_probability: base win probability of the game profile (e.g., 0.50 for x2, 0.25 for x4)
    Returns probability in [0, 1]
    """
    chat_id = str(chat_id)

    base_probability = Decimal(str(base_probability))
    # main_chat_id = -1002988477375
    chat_bonus = chats_bonuses.get(chat_id, 1)
    # print(chat_bonus, chat_id, '-1002988477375'==str(chat_id))


    user_data = get_user_data(user_id)
    all_balance = user_data["balance"] + user_data["deposit"]
    user_chance_percent = win_chance(all_balance)  # 0..100
    # Neutral point is 50%. Above 50 increases odds, below decreases
    factor = user_chance_percent * Decimal("0.02")
    adjusted = base_probability * factor * chat_bonus
    if adjusted < 0:
        return 0
    if adjusted > 1:
        return 1
    return adjusted
