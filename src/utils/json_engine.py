from decimal import Decimal, ROUND_HALF_UP
import json
import os
import time
from config import MAX_BALANCE, START_BALANCE, MIN_POSITIVE_NUM, database_path, FILL_MISSING_DEFAULTS



balance_list = ['balance', 'debt', 'deposit', 'min_deposit', 'max_loan', 'rub_balance']
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            rounded = obj.quantize(MIN_POSITIVE_NUM, rounding=ROUND_HALF_UP)
            return str(rounded)
        return super().default(obj)

users_dir = 'users'

def _ensure_defaults(data, defaults):
    """Добавляет отсутствующие ключи из defaults в data (рекурсивно).
    Возвращает True, если были внесены изменения.
    """
    changed = False
    for key, default_value in defaults.items():
        if key not in data:
            data[key] = default_value
            changed = True
        elif isinstance(default_value, dict) and isinstance(data.get(key), dict):
            if _ensure_defaults(data[key], default_value):
                changed = True
    return changed

def get_user_data(user_id, data_key=None):
    filename = os.path.join(users_dir, f'{user_id}.json')
    
    default_data = {
        "balance": f"{START_BALANCE}",
        "debt": "0.0",
        "deposit": "0.0",
        "credit_rating": 100,
        "min_deposit": "0.0",  # Минимальная сумма депозита для начисления процентов
        "max_loan": "0.0",     # Максимальная сумма кредита, которую пользователь когда-либо брал
        "getbc_time": 0,       # Время последнего использования команды /getbc (Unix timestamp)
        "username": "",        # Telegram username пользователя
        "date_create": int(time.time()),      # Дата создания пользователя (Unix timestamp)
        "date_update": int(time.time()),   
        "last_interest_date": "None",
        'inventory': {},
        "minecraft_goods_count_season": {},
        "rub_balance": "0.0",
        # Убрали last_interest_update - он не используется
    }
    
    data = get_data(filename, default_data)
    
    # Если это новый пользователь (date_create = 0), устанавливаем текущее время
    # if data.get("date_create", 0) == 0:
    #     data["date_create"] = int(time.time())
    #     data["date_update"] = int(time.time())
    
    # Конвертируем строки в Decimal
    for key in balance_list:
        if isinstance(data.get(key), str):
            data[key] = Decimal(data[key])
    
    # print(data)
    
    if data_key is not None:
        data = data.get(data_key)
    return data

def update_user_data(user_id, data):
    filename = os.path.join(users_dir, f'{user_id}.json')
    
    data_to_save = data.copy()
    
    # Добавляем текущее время как date_update
    data_to_save["date_update"] = int(time.time())
    
    # Округляем и конвертируем Decimal в строки
    for key in balance_list:
        data_num = data_to_save.get(key)
        if isinstance(data_num, Decimal):
            if data_num < 0:
                print('баланс в минусе')
                data_num = Decimal('0')
            # print('    # Округляем и конвертируем Decimal в строки', data_num)
            if data_num > MAX_BALANCE:
                data_num = Decimal(MAX_BALANCE)

       
            rounded = data_num.quantize(MIN_POSITIVE_NUM, rounding=ROUND_HALF_UP)
            data_to_save[key] = str(rounded)
    
    update_file(filename, data_to_save)



def get_admins_data():
    filename = 'admins_data.json'
    return get_data(filename, {"admins_ids": []})


def update_admins_data(data):
    filename = 'admins_data.json'
    update_file(filename, data)


def get_categories_data():
    filename = 'minecraft_goods.json'
    return get_data(filename, {})


def update_categories_data(data):
    filename = 'minecraft_goods.json'
    update_file(filename, data)




def get_donat_goods_data():
    filename = 'minecraft_donat_goods.json'
    return get_data(filename, {})


def update_donat_goods_data(data):
    filename = 'minecraft_donat_goods.json'
    update_file(filename, data)


def get_all_users():
    """Возвращает данные всех пользователей"""
    users_data = []
    users_dir_path = os.path.join(database_path, users_dir)
    
    if not os.path.exists(users_dir_path):
        return users_data
    
    for filename in os.listdir(users_dir_path):
        if filename.endswith('.json'):
            user_id = int(filename.split('.')[0])
            try:
                user_data = get_user_data(user_id)
                users_data.append((user_id, user_data))
            except:
                continue
    
    return users_data






def get_data(filename, start_data):
    file_path = os.path.join(database_path, filename)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = start_data
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, cls=DecimalEncoder)
    else:
        # Если файл существует, убедимся, что в нём есть все ключи по умолчанию (если включено)
        if FILL_MISSING_DEFAULTS and isinstance(start_data, dict) and isinstance(data, dict):
            if _ensure_defaults(data, start_data):
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, cls=DecimalEncoder)
    finally:
        return data


def update_file(filename, data):
    file_path = os.path.join(database_path, filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, cls=DecimalEncoder)


        