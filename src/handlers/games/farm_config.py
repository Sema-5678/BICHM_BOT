from typing import Dict, List, TypedDict
from enum import Enum
from datetime import timedelta

class PlantState(str, Enum):
    EMPTY = "empty"
    ALIVE = "alive"
    WILTED = "wilted"

# Economy configuration
ECONOMY = {
    # Exchange rates
    'exchange': {
        'bc_to_fc_rate': 0.08,  # 1 BC = 0.08 FC
        'fc_to_bc_rate': 0.3,    # 1 FC = 0.3 BC
        'daily_exchange_limit_fc': 50  # Max FC that can be exchanged to BC per day
    },
    
    # Farm settings
    'farm': {
        'max_field_size': 9,
        'initial_field_size': 4,
        'care': {
            'price_fc': 0,  # Cost to care for the garden
            'warning_after_days': 1,  # Warning after 1 day of no care
            'wilt_after_days': 2,     # Plants start wilting after 2 days
            'max_wilted_per_day': 1   # Max plants that can wilt per day of inactivity
        }
    },
    
    # Shop settings
    'shops': {
        'donate_refresh_days': 2,    # Donate shop refresh interval
        'normal_shop_refresh_days': 1  # Normal shop refresh interval
    }
}

# Plant types configuration
PLANT_TYPES = {
    # Regular plants (FC)
    1: {
        'name': 'Пшеница',
        'cost_fc': 10,
        'grow_time': 24,  # hours
        'base_income': 1,
        'synergies': {2: 10, 3: 15}  # {plant_id: bonus_percentage}
    },
    2: {
        'name': 'Морковь',
        'cost_fc': 20,
        'grow_time': 36,
        'base_income': 2,
        'synergies': {1: 10, 3: 20}
    },
    
    # Donate plants (BC only)
    101: {
        'name': 'Золотая пшеница',
        'cost_bc': 10,
        'grow_time': 20,
        'base_income': 2,
        'synergies': {1: 20, 101: 15},
        'is_donate': True
    },
    102: {
        'name': 'Кристальная роза',
        'cost_bc': 25,
        'grow_time': 48,
        'base_income': 5,
        'synergies': {102: 25},
        'is_donate': True
    }
}

# Shop items
SHOP_ITEMS = {
    # Normal shop (FC)
    'revival_potion': {
        'name': 'Эликсир оживления',
        'cost_fc': 15,
        'description': 'Возвращает увядшее растение к жизни',
        'type': 'consumable'
    },
    'growth_booster': {
        'name': 'Ускоритель роста',
        'cost_fc': 30,
        'description': 'Ускоряет рост всех растений на 20% на 24 часа',
        'type': 'booster',
        'duration_hours': 24,
        'effect': {'growth_speed': 1.2}
    },
    
    # Donate shop (BC)
    'eternal_rose': {
        'name': 'Вечная роза',
        'cost_bc': 50,
        'description': 'Особый сорт розы, который никогда не вянет',
        'type': 'permanent_plant',
        'plant_id': 103,
        'is_donate': True
    },
    'golden_watercan': {
        'name': 'Золотая лейка',
        'cost_bc': 100,
        'description': 'Увеличивает доход с растений на 15% навсегда',
        'type': 'permanent_boost',
        'effect': {'income_multiplier': 1.15}
    }
}
