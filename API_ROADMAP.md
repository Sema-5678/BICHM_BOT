# API roadmap (next update)

Ниже список эндпоинтов, которые логично добавить поверх текущей SQLite/SQLAlchemy базы и FastAPI‑сервиса, чтобы API был “полным” для админки/статистики/интеграций.

## 0) Общие принципы (важно)

- **Auth**: оставить `X-API-Key` (быстро), но лучше перейти на JWT (admin/service) + роли.
- **Audit**: логировать кто/когда/что менял (таблица `audit_log`).
- **Rate limit**: хотя бы базовый лимит на ключ.
- **Idempotency**: для платёжных/балансовых операций — `Idempotency-Key`.
- **Pagination**: на листингах `limit/offset` или cursor.
- **Safety**: эндпоинты “модификации” отделить от “просмотра”, возможность `dry_run`.

## 1) Health / Meta

- `GET /health` — проверка живости сервиса.
- `GET /ready` — готовность (БД доступна, миграции применены).
- `GET /version` — версия API/билда + текущая ревизия Alembic.

## 2) Users (read)

- `GET /v1/users/{telegram_id}` — краткая карточка: балансы, username, minecraft_username, created/updated.
- `GET /v1/users/{telegram_id}/balances` — только балансы.
- `GET /v1/users` — список пользователей (пагинация, сортировки: balance/rub_balance/date_create).
- `GET /v1/users/search?username=...&minecraft_username=...` — поиск.
- `GET /v1/users/{telegram_id}/inventory` — инвентарь (JSON поле).
- `GET /v1/users/{telegram_id}/farm` — farm_minigame (JSON поле).

## 3) Users (write / admin)

- `PATCH /v1/users/{telegram_id}` — изменить `minecraft_username`, `username` (частично).
- `POST /v1/users/{telegram_id}/balances/bc` — уже есть.
- `POST /v1/users/{telegram_id}/balances/rub` — уже есть.
- `POST /v1/users/{telegram_id}/inventory/add` — добавить предмет (category_id/item_id/qty).
- `POST /v1/users/{telegram_id}/inventory/remove` — убрать предмет.
- `POST /v1/users/{telegram_id}/inventory/clear` — очистить.
- `POST /v1/users/{telegram_id}/farm/reset` — сброс фермы (аккуратно).

## 4) Stats / Analytics

- `GET /v1/stats/users/count` — всего пользователей.
- `GET /v1/stats/balances/top?limit=...` — топ богатых (BC + депозит, как в боте).
- `GET /v1/stats/balances/summary` — суммы/средние/медианы (BC/rub/deposit/debt).
- `GET /v1/stats/active` — активность по `date_update` за N дней.
- `GET /v1/stats/inventory/top-items` — топ предметов по инвентарям.

## 5) Singletons / Config (minecraft_goods, admins_data, mini_game_farm)

- `GET /v1/config/admins` — текущий список админов.
- `PUT /v1/config/admins` — заменить список админов.

- `GET /v1/config/minecraft_goods` — текущие товары/категории.
- `PUT /v1/config/minecraft_goods` — залить новый конфиг целиком (валидировать).
- `PATCH /v1/config/minecraft_goods` — точечные изменения (категория/элемент).

- `GET /v1/config/mini_game_farm` — текущее “глобальное” поле.
- `PUT /v1/config/mini_game_farm` — обновить (например, сменить `curr_field`).

## 6) Minecraft / RCON (опасный блок)

Добавлять можно, но **строго ограниченно** (API‑ключи, allowlist команд, audit, rate‑limit), иначе это удалённый RCE на сервер.

Минимальный безопасный вариант:
- `POST /v1/minecraft/give` — выдать предметы игроку (username, items) — фактически обёртка над вашей `give_player_items_in_minecraft`.
- `POST /v1/minecraft/nickname/color` — применить цвет к нику (обёртка над вашей логикой team).
- `POST /v1/minecraft/execute` — **не делать “любой RCON”**, только allowlist из 5–10 команд с параметрами.

## 7) Admin tools

- `POST /v1/admin/migrations/upgrade` — лучше не надо в проде, но можно для локалки.
- `POST /v1/admin/reload-cache` — если появится кэш/локи.
- `GET /v1/admin/audit` — просмотр журнала изменений.

## 8) Webhooks / Events (если потребуется)

- `POST /v1/events/user-balance-changed` — входящие события.
- `GET /v1/stream/...` — SSE/WebSocket для live‑статистики (опционально).

