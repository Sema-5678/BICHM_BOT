# import random
# import time
# from datetime import datetime, timedelta
# from typing import Dict, List, Optional, Tuple, TypedDict, Union
# from enum import Enum

# from config import FarmConfig

# # Import constants from FarmConfig for easier access
# # ECONOMY = {
# #     'exchange': FarmConfig.EXCHANGE_RATES,
# #     'farm': {
# #         'max_field_size': FarmConfig.MAX_FIELD_SIZE,
# #         'initial_field_size': FarmConfig.INITIAL_FIELD_SIZE,
# #         'care': FarmConfig.CARE_SETTINGS,
# #         'expansion_cost_multiplier': FarmConfig.EXPANSION_COST_MULTIPLIER,
# #         'shop_refresh_hours': FarmConfig.SHOP_REFRESH_HOURS,
# #         'plant_update_hours': FarmConfig.PLANT_UPDATE_HOURS,
# #         'daily_bonus_fc': FarmConfig.DAILY_BONUS_FC,
# #         'consecutive_bonus_days': FarmConfig.CONSECUTIVE_BONUS_DAYS,
# #         'consecutive_bonus_multiplier': FarmConfig.CONSECUTIVE_BONUS_MULTIPLIER
# #     },
# #     'shops': FarmConfig.SHOPS
# # }

# PLANT_TYPES = FarmConfig.PLANT_TYPES
# NORMAL_SHOP_ITEMS = FarmConfig.NORMAL_SHOP_ITEMS
# DONATE_SHOP_ITEMS = FarmConfig.DONATE_SHOP_ITEMS

# class PlantState(str, Enum):
#     EMPTY = "empty"
#     ALIVE = "alive"
#     WILTED = "wilted"

# class FarmGame:
#     def __init__(self, user_id: int, user_data: dict):
#         self.user_id = user_id
#         self.user_data = user_data
#         self.farm_data = user_data['farm_minigame']
        
#         # Initialize field if not exists
#         if not self.farm_data['field']:
#             self._initialize_field()
        
#         # Initialize shop if needed
#         self._initialize_shop()
    
 
    
#     def _initialize_field(self):
#         """Initialize the farm field with empty cells."""
#         size = self.farm_data['field_size']
#         self.farm_data['field'] = {}
        
#         for row in range(size):
#             for col in range(size):
#                 cell_id = f"{chr(65 + row)}{col + 1}"
#                 self.farm_data['field'][cell_id] = {
#                     'plant_id': None,
#                     # 'is_donate': False,
#                     'state': PlantState.EMPTY,
#                     'planted_at': None,
#                     'last_harvested': None
#                 }
    
#     def _initialize_shop(self):
#         """Initialize or refresh the shop if needed."""
#         now = datetime.now().date()
        
#         # Normal shop refresh
#         if (self.farm_data['shop']['normal_refresh_date'] is None or 
#             now >= datetime.strptime(self.farm_data['shop']['normal_refresh_date'], '%Y-%m-%d').date()):
#             self.farm_data['shop']['normal_stock'] = self._generate_shop_stock('normal')
#             self.farm_data['shop']['normal_refresh_date'] = (now + timedelta(
#                 days=ECONOMY['shops']['normal_refresh_days']
#             )).strftime('%Y-%m-%d')
        
#         # Donate shop refresh
#         if (self.farm_data['shop']['donate_refresh_date'] is None or 
#             now >= datetime.strptime(self.farm_data['shop']['donate_refresh_date'], '%Y-%m-%d').date()):
#             self.farm_data['shop']['donate_stock'] = self._generate_shop_stock('donate')
#             self.farm_data['shop']['donate_refresh_date'] = (now + timedelta(
#                 days=ECONOMY['shops']['donate_refresh_days']
#             )).strftime('%Y-%m-%d')
    
#     def _generate_shop_stock(self, shop_type: str) -> List[dict]:
#         """Generate random stock for the shop."""
#         if shop_type == 'normal':
#             items = NORMAL_SHOP_ITEMS
#             count = ECONOMY['shops']['normal_items_per_refresh']
#         else:  # donate
#             items = DONATE_SHOP_ITEMS
#             count = ECONOMY['shops']['donate_items_per_refresh']
        
#         # Weighted random selection
#         weighted_items = []
#         for item in items:
#             weight = item.get('weight', 1)
#             weighted_items.extend([item] * weight)
        
#         selected = random.sample(weighted_items, min(count, len(weighted_items)))
#         return [{'item_id': item['id'], 'stock': random.randint(1, 3)} for item in selected]
    
#     def care_for_garden(self) -> Tuple[bool, str]:
#         """Care for the garden and reset missed days counter."""
#         today = datetime.now().date()
#         last_care = datetime.strptime(self.farm_data['last_care_day'], '%Y-%m-%d').date() if self.farm_data['last_care_day'] else None
        
#         if last_care and last_care == today:
#             return False, "Вы уже ухаживали за садом сегодня."
        
#         self.farm_data['last_care_day'] = today.strftime('%Y-%m-%d')
#         self.farm_data['missed_days'] = 0
#         return True, "Вы ухаживали за садом. Все растения в порядке!"
    
#     def update_wilted_plants(self):
#         """Update plant states based on care status."""
#         if not self.farm_data['last_care_day']:
#             return
        
#         today = datetime.now().date()
#         last_care = datetime.strptime(self.farm_data['last_care_day'], '%Y-%m-%d').date()
#         days_since_care = (today - last_care).days
        
#         if days_since_care <= 1:
#             return
        
#         # Calculate how many days of wilting to process
#         wilt_days = days_since_care - 1
#         max_wilted = ECONOMY['farm']['care']['max_wilted_per_day'] * wilt_days
        
#         # Get all non-donate, non-wilted plants
#         plants_to_wilt = [
#             cell_id for cell_id, cell in self.farm_data['field'].items()
#             if cell['plant_id'] and not cell['is_donate'] and cell['state'] == PlantState.ALIVE
#         ]
        
#         # Randomly select plants to wilt
#         num_to_wilt = min(max_wilted, len(plants_to_wilt))
#         if num_to_wilt > 0:
#             wilted = random.sample(plants_to_wilt, num_to_wilt)
#             for cell_id in wilted:
#                 self.farm_data['field'][cell_id]['state'] = PlantState.WILTED
    
#     def plant(self, cell_id: str, plant_id: int, is_donate: bool = False) -> Tuple[bool, str]:
#         """Plant a new plant in the specified cell."""
#         if cell_id not in self.farm_data['field']:
#             return False, "Неверная клетка."
        
#         cell = self.farm_data['field'][cell_id]
#         if cell['state'] != PlantState.EMPTY:
#             return False, "Клетка уже занята."
        
#         plant_info = PLANT_TYPES.get(plant_id)
#         if not plant_info:
#             return False, "Неизвестный тип растения."
        
#         # Check if it's a donate plant and user has enough RUB
#         if is_donate:
#             if self.user_data.get('rub_balance', 0) < plant_info.get('cost_rub', 0):
#                 return False, "Недостаточно RUB для покупки этого растения."
#             self.user_data['rub_balance'] -= plant_info['cost_rub']
#         else:
#             if self.farm_data['fc_balance'] < plant_info.get('cost_fc', 0):
#                 return False, "Недостаточно FC для покупки этого растения."
#             self.farm_data['fc_balance'] -= plant_info['cost_fc']
        
#         # Check neighbor synergies
#         neighbor_bonus = self._calculate_neighbor_bonus(cell_id, plant_id)
#         if neighbor_bonus <= 0:
#             return False, "Эти растения нельзя сажать рядом!"
        
#         # Plant the new plant
#         cell.update({
#             'plant_id': plant_id,
#             'is_donate': is_donate,
#             'state': PlantState.ALIVE,
#             'planted_at': time.time(),
#             'last_harvested': None
#         })
        
#         return True, f"Посажено: {plant_info['name']}"
    
#     def _calculate_neighbor_bonus(self, cell_id: str, plant_id: int) -> float:
#         """Calculate bonus from neighboring plants (0 means cannot plant)."""
#         if plant_id not in PLANT_TYPES:
#             return 0
        
#         synergies = PLANT_TYPES[plant_id].get('synergies', {})
#         if not synergies:
#             return 1.0  # No synergies defined, neutral
        
#         # Get coordinates
#         row = ord(cell_id[0]) - 65  # A=0, B=1, etc.
#         col = int(cell_id[1:]) - 1
        
#         # Check all 8 neighboring cells
#         total_bonus = 1.0
#         for dr in [-1, 0, 1]:
#             for dc in [-1, 0, 1]:
#                 if dr == 0 and dc == 0:
#                     continue  # Skip self
                
#                 nr, nc = row + dr, col + dc
#                 if 0 <= nr < self.farm_data['field_size'] and 0 <= nc < self.farm_data['field_size']:
#                     neighbor_id = f"{chr(65 + nr)}{nc + 1}"
#                     neighbor = self.farm_data['field'].get(neighbor_id, {})
                    
#                     if neighbor.get('state') == PlantState.ALIVE:
#                         neighbor_plant = neighbor.get('plant_id')
#                         bonus = synergies.get(neighbor_plant, 1.0)
#                         if bonus <= 0:
#                             return 0  # Cannot plant next to incompatible plants
#                         total_bonus *= bonus
        
#         return total_bonus
    
#     def harvest(self, cell_id: str) -> Tuple[bool, str, int]:
#         """Harvest a plant and return the earnings."""
#         if cell_id not in self.farm_data['field']:
#             return False, "Неверная клетка.", 0
        
#         cell = self.farm_data['field'][cell_id]
#         if cell['state'] != PlantState.ALIVE:
#             return False, "Нечего собирать.", 0
        
#         plant_info = PLANT_TYPES.get(cell['plant_id'])
#         if not plant_info:
#             return False, "Ошибка: неизвестное растение.", 0
        
#         # Check if plant is ready to harvest
#         now = time.time()
#         if cell['last_harvested']:
#             time_since_harvest = now - cell['last_harvested']
#         else:
#             time_since_harvest = now - cell['planted_at']
        
#         grow_time = plant_info['grow_time'] * 3600  # Convert hours to seconds
#         if time_since_harvest < grow_time:
#             time_left = int((grow_time - time_since_harvest) / 60)  # in minutes
#             return False, f"Еще не выросло. Осталось: {time_left} минут.", 0
        
#         # Calculate earnings with bonuses
#         base_income = plant_info['base_income']
#         neighbor_bonus = self._calculate_neighbor_bonus(cell_id, cell['plant_id'])
#         boost_multiplier = self._get_income_multiplier()
        
#         earnings = int(base_income * neighbor_bonus * boost_multiplier)
        
#         # Update cell and balance
#         cell['last_harvested'] = now
#         self.farm_data['fc_balance'] += earnings
        
#         return True, f"Собрано {earnings} FC!", earnings
    
#     def _get_income_multiplier(self) -> float:
#         """Calculate total income multiplier from all active boosts."""
#         multiplier = 1.0
#         now = time.time()
        
#         # Check permanent boosts
#         for boost_id, boost in self.farm_data.get('boosts', {}).items():
#             if boost.get('expires_at', float('inf')) > now:
#                 multiplier *= boost.get('effect', {}).get('income_multiplier', 1.0)
        
#         return multiplier
    
#     def buy_shop_item(self, item_id: str, shop_type: str) -> Tuple[bool, str]:
#         """Buy an item from the shop."""
#         shop = self.farm_data['shop']
#         stock = shop[f"{shop_type}_stock"]
        
#         # Find the item in stock
#         item_info = None
#         item_idx = -1
#         for i, item in enumerate(stock):
#             if item['item_id'] == item_id:
#                 item_info = next((i for i in (NORMAL_SHOP_ITEMS if shop_type == 'normal' else DONATE_SHOP_ITEMS) 
#                                if i['id'] == item_id), None)
#                 item_idx = i
#                 break
        
#         if not item_info or item_idx == -1:
#             return False, "Товар не найден в магазине."
        
#         # Check stock
#         if stock[item_idx]['stock'] <= 0:
#             return False, "Товар закончился."
        
#         # Check balance
#         if shop_type == 'normal':
#             if self.farm_data['fc_balance'] < item_info['cost_fc']:
#                 return False, f"Недостаточно FC. Нужно {item_info['cost_fc']} FC."
#             self.farm_data['fc_balance'] -= item_info['cost_fc']
#         else:  # donate
#             if self.user_data.get('rub_balance', 0) < item_info['cost_rub']:
#                 return False, f"Недостаточно RUB. Нужно {item_info['cost_rub']} RUB."
#             self.user_data['rub_balance'] -= item_info['cost_rub']
        
#         # Apply item effect
#         if item_info['type'] in ['consumable', 'permanent_plant']:
#             self.farm_data['inventory'][item_id] = self.farm_data['inventory'].get(item_id, 0) + 1
#         elif item_info['type'] in ['booster', 'permanent_boost']:
#             self._apply_boost(item_id, item_info)
#         elif item_info['type'] == 'random_plant':
#             # Give random plant from the list
#             plant_id = random.choice(item_info['plant_ids'])
#             self.farm_data['inventory'][f"plant_{plant_id}"] = self.farm_data['inventory'].get(f"plant_{plant_id}", 0) + 1
        
#         # Update stock
#         stock[item_idx]['stock'] -= 1
#         if stock[item_idx]['stock'] <= 0:
#             stock.pop(item_idx)
        
#         return True, f"Вы купили {item_info['name']}!"
    
#     def _apply_boost(self, boost_id: str, boost_info: dict):
#         """Apply a boost effect."""
#         if 'boosts' not in self.farm_data:
#             self.farm_data['boosts'] = {}
        
#         now = time.time()
#         expires_at = None
        
#         if boost_info['type'] == 'booster':
#             expires_at = now + (boost_info['duration_hours'] * 3600)
        
#         self.farm_data['boosts'][boost_id] = {
#             'applied_at': now,
#             'expires_at': expires_at,
#             'effect': boost_info['effect']
#         }
    
#     def exchange_currency(self, from_currency: str, amount: float) -> Tuple[bool, str]:
#         """Exchange between BC and FC."""
#         today = datetime.now().date()
        
#         # Reset daily exchange counter if it's a new day
#         if self.farm_data['last_exchange_date'] != today.strftime('%Y-%m-%d'):
#             self.farm_data['fc_exchanged_today'] = 0
#             self.farm_data['last_exchange_date'] = today.strftime('%Y-%m-%d')
        
#         if from_currency == 'bc':
#             # BC to FC exchange (unfavorable)
#             if self.user_data.get('balance', 0) < amount:
#                 return False, "Недостаточно BC для обмена."
            
#             fc_amount = amount * ECONOMY['exchange']['bc_to_fc_rate']
#             self.user_data['balance'] = str(float(self.user_data['balance']) - amount)
#             self.farm_data['fc_balance'] += fc_amount
#             return True, f"Обменяно {amount} BC на {fc_amount:.2f} FC"
            
#         elif from_currency == 'fc':
#             # FC to BC exchange (favorable)
#             if self.farm_data['fc_balance'] < amount:
#                 return False, "Недостаточно FC для обмена."
            
#             bc_amount = amount * ECONOMY['exchange']['fc_to_bc_rate']
#             self.farm_data['fc_balance'] -= amount
#             self.user_data['balance'] = str(float(self.user_data.get('balance', 0)) + bc_amount)
#             self.farm_data['fc_exchanged_today'] += amount
#             return True, f"Обменяно {amount} FC на {bc_amount:.2f} BC"
        
#         return False, "Неверная валюта для обмена."
    
#     def revive_plant(self, cell_id: str) -> Tuple[bool, str]:
#         """Revive a wilted plant using a revival potion."""
#         if cell_id not in self.farm_data['field']:
#             return False, "Неверная клетка."
        
#         cell = self.farm_data['field'][cell_id]
#         if cell['state'] != PlantState.WILTED:
#             return False, "Растение не увядшее."
        
#         # Check if user has revival potion
#         if self.farm_data['inventory'].get('revival_potion', 0) <= 0:
#             return False, "У вас нет эликсира оживления."
        
#         # Revive the plant
#         cell['state'] = PlantState.ALIVE
#         self.farm_data['inventory']['revival_potion'] -= 1
        
#         return True, "Растение оживлено!"
    
#     def expand_farm(self) -> Tuple[bool, str]:
#         """Expand the farm to the next size if possible."""
#         current_size = self.farm_data['field_size']
#         if current_size >= ECONOMY['farm']['max_field_size']:
#             return False, "Достигнут максимальный размер фермы."
        
#         # Calculate expansion cost (1000 FC per new cell)
#         new_size = current_size + 1
#         cost = (new_size * 2 - 1) * ECONOMY['farm']['expansion_cost_multiplier']
        
#         if self.farm_data['fc_balance'] < cost:
#             return False, f"Недостаточно FC для расширения. Нужно {cost} FC."
        
#         # Expand the field
#         self.farm_data['fc_balance'] -= cost
#         self.farm_data['field_size'] = new_size
        
#         # Add new cells (bottom row and right column)
#         for row in range(new_size):
#             for col in range(new_size):
#                 cell_id = f"{chr(65 + row)}{col + 1}"
#                 if cell_id not in self.farm_data['field']:
#                     self.farm_data['field'][cell_id] = {
#                         'plant_id': None,
#                         'is_donate': False,
#                         'state': PlantState.EMPTY,
#                         'planted_at': None,
#                         'last_harvested': None
#                     }
        
#         return True, f"Ферма расширена до {new_size}×{new_size}!"