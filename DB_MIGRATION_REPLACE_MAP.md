# JSON → SQLite migration replace map

Ниже — места в коде, где сейчас используется старая JSON-логика (`src/utils/json_engine.py`) и где нужно заменить её на SQLite/SQLAlchemy (`src/database/*`).

## Core imports / bootstrap

- `src/app.py:12,143` — `get_admins_data()` (JSON) → заменить на async ORM: `orm_get_admins_ids()` (через `session_maker`) или отдельный helper, который возвращает список админов из таблицы `singletons`.

## Users (get_user_data / update_user_data)

В этих местах используется `get_user_data()`/`update_user_data()`:

- `src/handlers/common_cmds.py:73`
- `src/handlers/bank_handlers.py:36,64,91,124,147,165,189,203,359`
- `src/handlers/user_group.py:28`
- `src/handlers/games/casino.py:25,131`
- `src/handlers/games/farm.py:13,178,204,227,242,248,373,414`
- `src/handlers/games/farm_functions.py:14,219,307,317`
- `src/handlers/games/test/farm_handler.py:6,15`
- `src/handlers/components/functions.py:22,135,142,150,155,163,168,347,361,362,369,370,375,387,392,400,417,426,462,479`
- `src/handlers/shop/minecraft/inventory.py:97,122,124,177,179`
- `src/handlers/shop/minecraft/defs.py:77,82,84,88,91,97,107`
- `src/handlers/shop/minecraft/items_shop.py:143,243,267`
- `src/handlers/shop/minecraft/custom_shop.py:200,233,270,295,311,355`
- `src/utils/background_tasks.py:5,57,139` — массовые обновления пользователей через `get_all_users()` + `update_user_data()`
- `src/update_json.py:1,3,44` — миграционный/одноразовый скрипт, сейчас целиком завязан на JSON

Что менять (общая идея):
- `get_user_data(user_id)` → `async with session_maker() as s: user = await orm_get_or_create_user(s, user_id, username=...)`
- прямые изменения полей в dict + `update_user_data(...)` → `await orm_update_user_fields(s, user_id, balance=..., debt=..., ...)`
- участки, где берутся вложенные dict-данные (`inventory`, `farm_minigame`), нужно перевести на JSON-поля модели `User` (в SQLite это `JSON`-колонки) либо нормализовать в отдельные таблицы (позже).

## Categories / shop goods (minecraft_goods.json)

Использование `get_categories_data()`/`update_categories_data()`:

- `src/handlers/admin_private.py:11,38,51,80,259,275,310,318,382,397,418,447,466,487,516,540,548,561,582,606,614`
- `src/handlers/shop/replenishment.py:23`
- `src/handlers/shop/minecraft/shop.py:27`
- `src/handlers/shop/minecraft/inventory.py:24,41`
- `src/handlers/shop/minecraft/defs.py:24,286,339,385,428,474`
- `src/handlers/shop/minecraft/items_shop.py:23,98,128,231`
- `src/handlers/shop/minecraft/custom_shop.py:24`

Что менять:
- `get_categories_data()` → `orm_get_singleton(session, "minecraft_goods")`
- `update_categories_data(data)` → `orm_set_singleton(session, "minecraft_goods", data)`

## Farm global state (mini_game_farm.json)

Использование `get_farm_data()`/`update_farm_data()`:

- `src/handlers/games/farm_functions.py:14,224`
- `src/utils/background_tasks.py:5` (и закомментированные места `115,120`)

Что менять:
- `get_farm_data()` → `orm_get_singleton(session, "mini_game_farm")`
- `update_farm_data(data)` → `orm_set_singleton(session, "mini_game_farm", data)`

## Admin list (admins_data.json)

Использование `get_admins_data()`/`update_admins_data()`:

- `src/app.py:12,143`

Что менять:
- `get_admins_data()` → `orm_get_admins_ids()` (или `orm_get_singleton(session, "admins_data")`)
- `update_admins_data(data)` → `orm_set_singleton(session, "admins_data", data)` / `orm_set_admins_ids(...)`

## Bulk users list

Использование `get_all_users()`:

- `src/handlers/admin_private.py:11,692`
- `src/utils/background_tasks.py:5`
- `src/update_json.py:1,3`

Что менять:
- вместо обхода файлов `data/json_database/users/*.json` нужно сделать SQL-запрос по таблице `users` (добавить ORM helper вида `orm_list_users()` / `orm_iter_users()`), и уже по результатам обновлять записи.

## Config pointer to JSON database

- `src/config.py:12` — `database_path = .../data/json_database`

Это не обязательно ломает работу прямо сейчас, но при полном переходе на SQLite этот путь станет не нужен (или останется только для миграции/бэкапов).

