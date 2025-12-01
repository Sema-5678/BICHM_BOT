import os

from decimal import ROUND_HALF_UP, Decimal, getcontext

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())
# ===== Paths =====
# Получаем путь на уровень выше директории, где находится этот файл
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Пути к директориям
database_path = os.path.join(BASE_DIR, "data", "json_database")
log_dir = os.path.join(BASE_DIR, "data", "logs")


# ===== Interest and rates =====
# Настройки процентов(используем строки для точности)

# ============не используется==============
# INTEREST_UPDATE_INTERVAL = 10 * 60 * 60  # Интервал обновления в секундах (10 часов)  не используется
# CREDIT_INTEREST_RATE = 1.00027194  # не используется
# DEPOSIT_INTEREST_RATE = 1.00013624  # не используется
# CREDIT_RATING_DECREASE_PER_HOUR = 1  # На сколько уменьшается рейтинг в час 


week = Decimal(str(7))
INTEREST_DEPOSIT_RATE = Decimal(str(0.005))
INTEREST_CREDIT_RATE = Decimal(str(0.01))

INTEREST_DEPOSIT_RATE_day = INTEREST_DEPOSIT_RATE / week
INTEREST_CREDIT_RATE_day = INTEREST_CREDIT_RATE / week


CREDIT_INTEREST_RATE_TIME = (16, 2)  # Время для начисления процентов по кредиту  часы, минуты

# Пороги значимого платежа по кредиту для начисления рейтинга
MIN_PAYMENT_FOR_RATING = Decimal("5")  # абсолютный минимум суммы
MIN_PERCENT_FOR_RATING = Decimal("0.10")  # минимум 10% от текущего долга
# Кредитный рейтинг
CREDIT_RATING_DECREASE_PER_DAY = 1


TRANSFER_COMMISSION = 1.1


# ===== Precision & serialization =====
getcontext().prec = 15  # МАКС КОЛ-ВО ЧИСЕЛ В БОТЕ И JSON
MIN_POSITIVE_NUM = Decimal("0.01")  # 2 знака после запятой

# ===== Feature toggles =====
# Управление автодобавлением отсутствующих ключей в JSON пользователей
FILL_MISSING_DEFAULTS = True

# ===== Economy & limits =====
# Максимальный баланс пользователя
MAX_BALANCE = 1_000_000  # 1 миллион BC
MAX_BET = 100_000


MAX_LOAN = 1_000
MAX_DEPOSIT = 10_000
START_BALANCE = 60
MIN_CREDIT_RATING = 10
TOP_RICH_COUNT = 10

# ===== Games settings =====
MAX_CASINO_ROUNDS = 10
BLACKJACK_BET = Decimal("5")
AMATEUR_BLACKJACK_BET = Decimal("3")

# Win algorithm toggle
# legacy: use fixed base chances only
# balance: scale win chances by user balance using get_winning_chance
WIN_ALGORITHM = "balance"  # options: "legacy" | "balance"

# ===== Robbery settings =====
BASE_ROBBERY_CHANCE = 0.46
BASE_ROBBERY_PAYOUT = 2.2
ROBBERY_CHANCES = [
    {"chance": 0.02, "cost_percentage": 0.09, "name": "Взломщик"},
    {"chance": 0.20, "cost_percentage": 0.6, "name": "Водила"},
    {"chance": 0.01, "cost_percentage": 0.05, "name": "Смотрящий"},
    {"chance": -0.20, "cost_percentage": -0.5, "name": "Подрывник"},
    {"chance": 0.40, "cost_percentage": 1.1, "name": "Работник банка"},


]
ROBBERY_ITEMS_PER_ROW = 3

BLACKJACK_PAYOUT_X = Decimal("2.5")

# ===== /getbc settings =====
GET_BC_TIME_LIMIT = 4 * 60 * 60  # 4 часа в секундах
GET_BC_MIN_BC = 10  # Минимальное количество BC
GET_BC_MAX_BC = 20  # Максимальное количество BC


# ===== Easter eggs =====
EASTER_EGGS = [
    "🥚 Ты нашёл секретное пасхальное яйцо!",
    "🎉 Сюрприз! Вот тебе редкая пасхалка.",
    "🦄 Поздравляю! Пасхалка активирована.",
    "🐉 Ты вызвал древнего дракона... шучу, просто пасхалка.",
    "💎 Бонус! Но он ничего не даёт, кроме улыбки.",
    "🌌 Ты открыл портал в другую вселенную... но он сразу закрылся.",
    "🐧 Пингвин машет тебе крылышками!",
    "🍀 Нашёл клевер! Может, повезёт?",
    "🚀 Пасхалка доставлена с космоса.",
    "🧙 Ты случайно стал учеником великого мага... на 5 секунд.",
    "🐢 Медленная, но верная пасхалка.",
    "🍕 О, кусочек пиццы. Но виртуальный.",
    "🕹️ Старый аркадный автомат мигнул: 'Insert coin'.",
    "🐇 Белый кролик промчался мимо. Ты за ним?",
    "📦 Ты нашёл коробку. В ней... ещё одна пасхалка.",
    "⚡ Молния ударила рядом. Это был Зевс, просто мимо проходил.",
    "🦖 Динозавр сказал тебе 'Привет!'",
    "🔮 Шар предсказаний говорит: 'Сегодня твой день'.",
    "🎩 Фокусник достал из шляпы именно ТЕБЯ!",
    "📀 Пасхалка из 2000-х: 'Please insert disk 2'.",
    "🐙 Осьминог помахал щупальцами.",
    "🧩 Пазл сложился. Ты получил пасхалку!",
    "🦕 Ты активировал режим динозавра Chrome без интернета.",
    "🥕 Кролик утащил твою морковку. Пасхалка компенсирует.",
    "👑 Ты король пасхалок! Ну, на пару секунд.",
    "🐝 Жужжащая пасхалка пролетела мимо.",
    "🎲 Ты бросил кубик и выпало... Пасхалка!",
]



chats_bonuses = {'-1002988477375': Decimal("1.01"), "5273608148": Decimal("1.005")}



BC_PER_PUB = 50

ENABLE_TELEGRAM_LOGGING = False
MINI_CASINO_BET = 5



class Config():
    RCON_HOST = os.getenv("RCON_HOST")
    RCON_PORT = os.getenv("RCON_PORT")
    RCON_PASSWORD = os.getenv("RCON_PASSWORD")