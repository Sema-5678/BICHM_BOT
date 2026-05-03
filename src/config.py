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

BACKUP_COUNT = 10
MAX_BYTES = 2 * 1024 * 1024

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
    {"chance": 0.20, "cost_percentage": 0.7, "name": "Водила"},
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



chats_bonuses = {'-1002988477375': Decimal("1.00"), "5273608148": Decimal("1.005")}



BC_PER_PUB = 50

ENABLE_TELEGRAM_LOGGING = False
MINI_CASINO_BET = 5



import random
import os

class FarmConfig:
    # Farm settings
    MAX_FIELD_SIZE = 9
    INITIAL_FIELD_SIZE = 3
    EXPANSION_COST_MULTIPLIER = 1000  # Cost per cell for expansion
    
    # Shop settings
    SHOP_REFRESH_HOURS = 24  # How often the shop refreshes (in hours)
    PLANT_UPDATE_HOURS = 1   # How often to update plant states (in hours)
    
    # Daily bonuses
    DAILY_BONUS_FC = 100  # Daily bonus FC for logging in
    CONSECUTIVE_BONUS_DAYS = 7  # Number of days for consecutive login bonus
    CONSECUTIVE_BONUS_MULTIPLIER = 2.0  # Multiplier for consecutive login bonus
    
    # Background task intervals (in seconds)
    FARM_UPDATE_INTERVAL = 3600  # 1 hour
    SHOP_REFRESH_INTERVAL = 86400  # 24 hours
    PLANT_UPDATE_INTERVAL = 3600  # 1 hour
    
    # Exchange rates
    EXCHANGE_RATES = {
        'bc_to_fc_rate': 0.1,  # 1 BC = 0.1 FC (unfavorable)
        'fc_to_bc_rate': 0.5,  # 1 FC = 0.5 BC (favorable)
    }
    
    # Plant care settings
    CARE_SETTINGS = {
        'price_fc': 0,
        'warning_after_days': 1,
        'wilt_after_days': 2,
        'max_wilted_per_day': 1
    }
    
    # Shop settings
    SHOPS = {
        'normal_refresh_days': 1,
        'donate_refresh_days': 2,
        'normal_items_per_refresh': 5,
        'donate_items_per_refresh': 3
    }
    
    # Soil types with emojis and multipliers
    SOIL_TYPES = {
        1: {'name': 'Обычная земля', 'emoji': '🟫', 'multiplier': 1.0},
        2: {'name': 'Теневой участок', 'emoji': '🌑', 'multiplier': 0.9},
        # 2: {'name': 'Плодородная почва', 'emoji': '🌱', 'multiplier': 1.3},
        3: {'name': 'Песчаная почва', 'emoji': '🏜️', 'multiplier': 0.8},
        4: {'name': 'Глинистая почва', 'emoji': '🟤', 'multiplier': 1.1},
        5: {'name': 'Чернозем', 'emoji': '🖤', 'multiplier': 1.5},
        6: {'name': 'Солнечная поляна', 'emoji': '☀️', 'multiplier': 1.4},
    }

    # Plant types configuration with emojis
    PLANT_TYPES = {
        # Regular plants (FC)
        1: {
            'name': 'Пшеница',
            'emoji': '🌾',
            'cost_fc': Decimal('10'),
            'base_income': Decimal('0.05'),  # FC per minute
            'synergies': {1: 0.5, 2: 1.2, 3: 0.4}  # 0-1: negative effect, 1-2: positive effect
        },
        2: {
            'name': 'Морковь',
            'emoji': '🥕',
            'cost_fc': Decimal('20'),
            'base_income': Decimal('0.1'),  # FC per minute
            'synergies': {1: 1.2, 2: 0.5, 4: 1.5}
        },
        3: {
            'name': 'Картофель',
            'emoji': '🥔',
            'cost_fc': Decimal('15'),
            'base_income': Decimal('0.08'),  # FC per minute
            'synergies': {1: 0.4, 3: 1.8, 5: 1.3}
        },
        4: {
            'name': 'Тыква',
            'emoji': '🎃',
            'cost_fc': Decimal('30'),
            'base_income': Decimal('0.15'),  # FC per minute
            'synergies': {2: 1.5, 4: 0.8, 6: 1.2}
        },
        5: {
            'name': 'Кукуруза',
            'emoji': '🌽',
            'cost_fc': Decimal('25'),
            'base_income': Decimal('0.12'),  # FC per minute
            'synergies': {3: 1.3, 5: 0.7, 1: 1.1}
        },
        
        # Donate plants (RUB only)
        # 101: {
        #     'name': 'Золотая пшеница',
        #     'emoji': '🌟',
        #     'cost_rub': 50,
        #     'base_income': 0.1,  # FC per minute
        #     'synergies': {1: 1.5, 101: 1.8},
        #     'is_donate': True
        # },
        # 102: {
        #     'name': 'Кристальная роза',
        #     'emoji': '🌹',
        #     'cost_rub': 100,
        #     'base_income': 0.25,  # FC per minute
        #     'synergies': {102: 2.0, 2: 1.5},
        #     'is_donate': True
        # },
        # 103: {
        #     'name': 'Ледяной цветок',
        #     'emoji': '❄️',
        #     'cost_rub': 150,
        #     'base_income': 0.2,  # FC per minute
        #     'synergies': {103: 1.8, 3: 1.7},
        #     'is_donate': True
        # }
    }
    
    # Shop items
    NORMAL_SHOP_ITEMS = [
        {
            'id': 'revival_potion',
            'name': 'Эликсир оживления',
            'cost_fc': Decimal('30'),
            'description': 'Возвращает увядшее растение к жизни',
            'type': 'consumable',
            'weight': 30  # Higher weight = more likely to appear
        },
        {
            'id': 'growth_booster_1',
            'name': 'Ускоритель роста I',
            'cost_fc': Decimal('50'),
            'description': 'Ускоряет рост растений на 25% на 24 часа',
            'type': 'booster',
            'duration_hours': 24,
            'effect': {'growth_speed': 1.2},
            'rarity': 0.4
        },
        {
            'id': 'fertilizer',
            'name': 'Удобрение',
            'cost_fc': Decimal('25'),
            'description': 'Увеличивает доход с растений на 10% на 12 часов',
            'type': 'booster',
            'duration_hours': 12,
            'effect': {'income_multiplier': 1.1},
            'rarity': 0.5
        },
        {
            'id': 'field_expansion',
            'name': 'Расширение поля',
            'cost_fc': Decimal('100'),
            'description': 'Увеличивает размер фермы на 1 клетку',
            'type': 'upgrade',
            'rarity': 0.2
        }
    ]

    DONATE_SHOP_ITEMS = [
        # Donate plants
        {
            'id': 'eternal_rose',
            'name': 'Вечная роза',
            'cost_rub': Decimal('50'),
            'description': 'Особый сорт розы, который никогда не вянет',
            'type': 'permanent_plant',
            'plant_id': 101,
            'rarity': 0.4
        },
        {
            'id': 'golden_watercan',
            'name': 'Золотая лейка',
            'cost_rub': Decimal('100'),
            'description': 'Увеличивает доход с растений на 15% навсегда',
            'type': 'permanent_boost',
            'effect': {'income_multiplier': 1.15},
            'rarity': 0.3
        },
        {
            'id': 'magic_seeds',
            'name': 'Волшебные семена',
            'cost_rub': Decimal('75'),
            'description': 'Дает случайное редкое растение',
            'type': 'consumable',
            'rarity': 0.5
        },
        {
            'id': 'rainbow_fertilizer',
            'name': 'Радужное удобрение',
            'cost_rub': Decimal('60'),
            'description': 'Увеличивает все синергии на 50% на 3 дня',
            'type': 'booster',
            'duration_hours': 72,
            'effect': {'synergy_multiplier': 1.5},
            'rarity': 0.4
        }
    ]
    
    @classmethod
    def get_shop_items(cls, shop_type: str, count: int) -> list:
        """Get random shop items based on type and count."""
        pool = cls.NORMAL_SHOP_ITEMS if shop_type == 'normal' else cls.DONATE_SHOP_ITEMS
        
        # Weighted random selection based on rarity
        weights = [item.get('weight', item.get('rarity', 1)) for item in pool]
        return random.choices(pool, weights=weights, k=min(count, len(pool)))
    
    @classmethod
    def get_plant_info(cls, plant_id: int) -> dict:
        """Get plant information by ID."""
        return cls.PLANT_TYPES.get(plant_id, {})


class Config:
    RCON_HOST = os.getenv("RCON_HOST")
    RCON_PORT = os.getenv("RCON_PORT")
    RCON_PASSWORD = os.getenv("RCON_PASSWORD")