# API roadmap (next update)

Ниже список эндпоинтов, которые логично добавить поверх текущей SQLite/SQLAlchemy базы и FastAPI‑сервиса, чтобы API был удобным для статистики и внешних интеграций.

В этом документе:
- Разделы **1–4** — то, что можно делать в ближайшем обновлении.
- Всё, что начинается с **5+**, перенесено в блок “не делаем сейчас” (это чувствительные админские штуки).

## 0) Общие принципы (важно)

- **Auth**: оставить `X-API-Key` (быстро), но лучше перейти на JWT (admin/service) + роли.
- **Audit**: логировать кто/когда/что менял (таблица `audit_log`).
- **Rate limit**: хотя бы базовый лимит на ключ.
- **Idempotency**: для платёжных/балансовых операций — `Idempotency-Key`.
- **Pagination**: на листингах `limit/offset` или cursor.
- **Safety**: эндпоинты “модификации” отделить от “просмотра”, возможность `dry_run`.

## 1) Health / Meta

### `GET /health`
Проверка “жив ли процесс”.

- **Auth**: нет
- **Response 200**:
  - `{"status":"ok"}`

### `GET /ready`
Готовность сервиса принимать запросы (БД доступна, миграции применены).

- **Auth**: нет (или можно включить)
- **Response 200** (пример):
  - `{"db":"ok","migrations":"ok"}`
- **Response 503**:
  - если БД не доступна / не применены миграции

### `GET /version`
Версия API и ревизия миграций.

- **Auth**: нет
- **Response 200** (пример):
  - `{"api_version":"0.1.0","alembic_head":"0001_create_core_tables"}`

## 2) Users (read)

Все эндпоинты этого раздела только читают данные.

**Auth**: по умолчанию `X-API-Key` (тот же, что и для write‑эндпоинтов), чтобы никто не мог “слить” базу с балансами.

### `GET /v1/users/{telegram_id}`
Краткая карточка пользователя.

- **Path**: `telegram_id` (int)
- **Response 200** (пример):
  - `{"id":5273608148,"username":"...","minecraft_username":null,"balance":"10.50","rub_balance":"0.00","deposit":"0.00","debt":"0.00","created_at":"...","updated_at":"...","date_create":171...,"date_update":171...}`
- **Response 404**:
  - если пользователя нет (или можно auto-create выключить именно для read)

### `GET /v1/users/{telegram_id}/balances`
Только балансы и финансовые поля.

- **Response 200** (пример):
  - `{"id":5273608148,"balance":"10.50","rub_balance":"0.00","deposit":"0.00","debt":"0.00","credit_rating":100}`

### `GET /v1/users`
Список пользователей с пагинацией и сортировкой.

- **Query**:
  - `limit` (default 50, max 200)
  - `offset` (default 0)
  - `sort` (`balance|rub_balance|date_create|date_update`, default `date_update`)
  - `order` (`asc|desc`, default `desc`)
- **Response 200** (пример):
  - `{"items":[{...user_card...},...],"limit":50,"offset":0,"total":1234}`

### `GET /v1/users/search`
Поиск пользователей.

- **Query**:
  - `username` (строка, partial match)
  - `minecraft_username` (строка, partial match)
  - `id` (точный telegram_id)
- **Response 200**: как `GET /v1/users`

### `GET /v1/users/{telegram_id}/inventory`
Просмотр инвентаря (JSON поле).

- **Response 200** (пример):
  - `{"id":5273608148,"inventory":{"1_10":3,"2_7":1}}`

### `GET /v1/users/{telegram_id}/farm`
Просмотр `farm_minigame` (JSON поле).

- **Response 200** (пример):
  - `{"id":5273608148,"farm_minigame":{...}}`

## 3) Users (write / admin)

Все эндпоинты этого раздела меняют данные пользователя.

**Auth**: обязательно `X-API-Key` + позже разделить роли (обычный ключ статистики vs админ‑ключ).

### `PATCH /v1/users/{telegram_id}`
Частичное обновление “профильных” полей, которые не являются балансами.

- **Body** (можно менять любое подмножество полей):
  - `{"username":"new_telegram_username"}`
  - `{"minecraft_username":"Steve"}`
  - `{"minecraft_username":null}` — удалить ник (сделать пустым)
- **Response 200**:
  - возвращает обновлённую карточку как `GET /v1/users/{telegram_id}`

### `POST /v1/users/{telegram_id}/balances/bc`
Уже реализовано.

- **Body**:
  - `{"amount":"10.50","mode":"delta"}`
  - `{"amount":"0.00","mode":"set"}`
- **Response 200**:
  - `{"user_id":...,"currency":"BC","mode":"delta","amount":"10.50","new_balance":"123.45"}`

### `POST /v1/users/{telegram_id}/balances/rub`
Уже реализовано, аналогично BC.

### `POST /v1/users/{telegram_id}/inventory/add`
Добавить предмет в инвентарь пользователя.

- **Body**:
  - `{"category_id":"1","item_id":"10","quantity":3}`
- **Effect**:
  - увеличивает `inventory["1_10"]` на `quantity`
- **Response 200**:
  - `{"id":...,"inventory":{...}}`

### `POST /v1/users/{telegram_id}/inventory/remove`
Убрать предмет из инвентаря.

- **Body**:
  - `{"category_id":"1","item_id":"10","quantity":2}`
- **Effect**:
  - уменьшает `inventory["1_10"]`, не даёт уйти ниже 0 (0 → удаляем ключ)
- **Response 200**:
  - `{"id":...,"inventory":{...}}`

### `POST /v1/users/{telegram_id}/inventory/clear`
Полностью очистить инвентарь.

- **Body**: пусто
- **Response 200**:
  - `{"id":...,"inventory":{}}`

### `POST /v1/users/{telegram_id}/farm/reset`
Сброс мини‑фермы для пользователя (аккуратно, т.к. это прогресс игрока).

- **Body**:
  - `{"confirm":true}`
- **Response 200**:
  - `{"id":...,"farm_minigame":{...default...}}`

## 4) Stats / Analytics

Этот раздел нужен для внешней статистики/дашбордов.

**Auth**: `X-API-Key` (иначе утечка статистики/базы).

### `GET /v1/stats/users/count`
- **Response 200**:
  - `{"users":1234}`

### `GET /v1/stats/balances/top`
Топ по “богатству” как в боте: `balance + deposit`.

- **Query**:
  - `limit` (default 10, max 100)
- **Response 200**:
  - `{"items":[{"id":...,"total":"123.45","balance":"100.00","deposit":"23.45"},...]}`

### `GET /v1/stats/balances/summary`
Агрегаты по балансу/рублям/депозиту/долгу.

- **Response 200** (пример):
  - `{"bc":{"sum":"...","avg":"..."},"rub":{"sum":"...","avg":"..."},"deposit":{"sum":"...","avg":"..."},"debt":{"sum":"...","avg":"..."}}`

### `GET /v1/stats/active`
Активность по `date_update`.

- **Query**:
  - `days` (default 7, max 365)
- **Response 200**:
  - `{"days":7,"active_users":123}`

### `GET /v1/stats/inventory/top-items`
Топ предметов по всем инвентарям (может быть тяжёлым, нужен limit).

- **Query**:
  - `limit` (default 50, max 200)
- **Response 200**:
  - `{"items":[{"item_key":"1_10","total_qty":999},...]}`

## Не делаем сейчас (зарезервировано на будущее)

Следующие блоки **не добавляем сейчас**: это высокорисковые админские возможности, которые не должны быть доступны обычному API‑ключу.


## 5) Singletons / Config (minecraft_goods, admins_data, mini_game_farm)


- `GET /v1/config/minecraft_goods` — текущие товары/категории.
- `PUT /v1/config/minecraft_goods` — залить новый конфиг целиком (валидировать).
- `PATCH /v1/config/minecraft_goods` — точечные изменения (категория/элемент).

- `GET /v1/config/mini_game_farm` — текущее “глобальное” поле.
- `PUT /v1/config/mini_game_farm` — обновить (например, сменить `curr_field`).



### 6) Minecraft / RCON
Пока **не делаем** никакого RCON API (слишком опасно).

### 7) Admin tools
Пока **не делаем** эндпоинты управления миграциями/аудитом через API.

### 8) Webhooks / Events
Пока **не делаем**. Вернёмся, если потребуется стриминг/интеграции.
