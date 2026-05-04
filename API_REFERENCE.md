# FastAPI API Reference

База URL (prod):

```powershell
$BASE_URL = "https://bichmbot.mooo.com"
```

Авторизация:
- Все защищённые эндпоинты требуют заголовок `X-API-Key`.
- Ключ берётся из `.env` на сервере (`API_KEY`).

Важно: **не храни и не коммить реальный API‑ключ в документации/репозитории**. Ниже в примерах используется переменная `$API_KEY`.

```powershell
$API_KEY = "<PUT_YOUR_API_KEY_HERE>"
```

Демо пользователь:

```powershell
$TG_ID = 5273608148
```

PowerShell команды используют `irm` (`Invoke-RestMethod`).

## Форматы данных

### Money / Decimal

Баланс/суммы передаются строкой с десятичной точкой, например `"10.50"` или `"-7.25"`.

### Общие ошибки

- `401 Invalid API key` — неверный/отсутствующий `X-API-Key`.
- `422` — ошибка валидации входных данных.
- `404 User not found` — пользователя нет (на read эндпоинтах).
- `500` — ошибка сервера.

## 1) Health / Meta

### `GET /health`
Назначение: проверка “жив ли сервис”.

Запрос:
```powershell
irm "$BASE_URL/health"
```

Ответ (пример):
```json
{"status":"ok"}
```

### `GET /ready`
Назначение: проверка готовности (доступна ли БД).

Запрос:
```powershell
irm "$BASE_URL/ready"
```

Ответ (пример):
```json
{"db":"ok","migrations":"unknown"}
```

### `GET /version`
Назначение: версия API.

Запрос:
```powershell
irm "$BASE_URL/version"
```

Ответ (пример):
```json
{"api_version":"0.1.0","alembic_head":"0001_create_core_tables"}
```

## 2) Балансы (BC / RUB)

Эти эндпоинты:
- требуют `X-API-Key`,
- **создают пользователя**, если его ещё нет (через `orm_get_or_create_user`),
- поддерживают режимы:
  - `mode="delta"` — прибавить/убавить
  - `mode="set"` — установить абсолютное значение
- ограничивают баланс снизу `0.00` и сверху лимитом (`MAX_BALANCE` / `MAX_RUB_BALANCE`).

### `POST /v1/users/{telegram_id}/balance/bc`
Назначение: изменить BC.

Запрос (пример, +10.50):
```powershell
irm -Method Post "$BASE_URL/v1/users/$TG_ID/balance/bc" `
  -Headers @{ "X-API-Key" = $API_KEY } `
  -ContentType "application/json" `
  -Body '{"amount":"10.50","mode":"delta"}'
```

Ответ (пример):
```json
{"user_id":5273608148,"currency":"BC","mode":"delta","amount":"10.50","new_balance":"123.45"}
```

### `POST /v1/users/{telegram_id}/balance/rub`
Назначение: изменить RUB.

Запрос (пример, -55.10):
```powershell
irm -Method Post "$BASE_URL/v1/users/$TG_ID/balance/rub" `
  -Headers @{ "X-API-Key" = $API_KEY } `
  -ContentType "application/json" `
  -Body '{"amount":"-55.10","mode":"delta"}'
```

Ответ (пример):
```json
{"user_id":5273608148,"currency":"RUB","mode":"delta","amount":"-55.10","new_balance":"0.00"}
```

## 3) Users (read)

Все эндпоинты этого раздела требуют `X-API-Key` и **не создают** пользователей автоматически.

### `GET /v1/users/{telegram_id}`
Назначение: карточка пользователя.

Запрос:
```powershell
irm "$BASE_URL/v1/users/$TG_ID" -Headers @{ "X-API-Key" = $API_KEY }
```

Ответ (пример):
```json
{
  "id": 5273608148,
  "username": "",
  "minecraft_username": null,
  "balance": "10.50",
  "rub_balance": "0.00",
  "deposit": "0.00",
  "debt": "0.00",
  "credit_rating": 100,
  "date_create": 1710000000,
  "date_update": 1710000001,
  "created_at": "2026-05-04T07:00:00",
  "updated_at": "2026-05-04T07:00:00"
}
```

### `GET /v1/users/{telegram_id}/balances`
Назначение: только финансовые поля.

Запрос:
```powershell
irm "$BASE_URL/v1/users/$TG_ID/balances" -Headers @{ "X-API-Key" = $API_KEY }
```

Ответ (пример):
```json
{"id":5273608148,"balance":"10.50","rub_balance":"0.00","deposit":"0.00","debt":"0.00","credit_rating":100}
```

### `GET /v1/users`
Назначение: список пользователей с пагинацией/сортировкой.

Запрос (пример):
```powershell
irm "$BASE_URL/v1/users?limit=50&offset=0&sort=date_update&order=desc" -Headers @{ "X-API-Key" = $API_KEY }
```

Ответ (пример):
```json
{"items":[{...user_card...}],"limit":50,"offset":0,"total":1234}
```

### `GET /v1/users/search`
Назначение: поиск (по `id`, `username`, `minecraft_username`).

Запрос (пример, по id):
```powershell
irm "$BASE_URL/v1/users/search?id=$TG_ID&limit=5&offset=0" -Headers @{ "X-API-Key" = $API_KEY }
```

Ответ (пример):
```json
{"items":[{...user_card...}],"limit":5,"offset":0,"total":1}
```

### `GET /v1/users/{telegram_id}/inventory`
Назначение: получить инвентарь пользователя.

Запрос:
```powershell
irm "$BASE_URL/v1/users/$TG_ID/inventory" -Headers @{ "X-API-Key" = $API_KEY }
```

Ответ (пример):
```json
{"id":5273608148,"inventory":{"1_10":1}}
```

### `GET /v1/users/{telegram_id}/farm` (временно отключено)
Сейчас эндпоинт отключён и возвращает `403`.

Запрос:
```powershell
irm "$BASE_URL/v1/users/$TG_ID/farm" -Headers @{ "X-API-Key" = $API_KEY }
```

Ответ:
```json
{"detail":"Farm API is temporarily disabled"}
```

## 4) Users (write)

### `PATCH /v1/users/{telegram_id}`
Назначение: обновить `username` / `minecraft_username`.

Запрос (пример, установить ник Minecraft):
```powershell
irm -Method Patch "$BASE_URL/v1/users/$TG_ID" `
  -Headers @{ "X-API-Key" = $API_KEY } `
  -ContentType "application/json" `
  -Body '{"minecraft_username":"Steve"}'
```

Запрос (пример, очистить ник Minecraft):
```powershell
irm -Method Patch "$BASE_URL/v1/users/$TG_ID" `
  -Headers @{ "X-API-Key" = $API_KEY } `
  -ContentType "application/json" `
  -Body '{"minecraft_username":null}'
```

Ответ: `UserCardOut` как в `GET /v1/users/{telegram_id}`.

### `POST /v1/users/{telegram_id}/inventory/add`
Назначение: добавить предмет в инвентарь.

Запрос:
```powershell
irm -Method Post "$BASE_URL/v1/users/$TG_ID/inventory/add" `
  -Headers @{ "X-API-Key" = $API_KEY } `
  -ContentType "application/json" `
  -Body '{"category_id":"1","item_id":"10","quantity":3}'
```

Ответ:
```json
{"id":5273608148,"inventory":{"1_10":3}}
```

### `POST /v1/users/{telegram_id}/inventory/remove`
Назначение: убрать предмет из инвентаря.

Правила:
- уменьшает количество,
- если стало `<= 0` — ключ удаляется.

Запрос:
```powershell
irm -Method Post "$BASE_URL/v1/users/$TG_ID/inventory/remove" `
  -Headers @{ "X-API-Key" = $API_KEY } `
  -ContentType "application/json" `
  -Body '{"category_id":"1","item_id":"10","quantity":2}'
```

Ответ:
```json
{"id":5273608148,"inventory":{"1_10":1}}
```

### `POST /v1/users/{telegram_id}/inventory/clear` (временно отключено)
Сейчас эндпоинт отключён и возвращает `403`.

Запрос:
```powershell
irm -Method Post "$BASE_URL/v1/users/$TG_ID/inventory/clear" `
  -Headers @{ "X-API-Key" = $API_KEY } `
  -ContentType "application/json" `
  -Body '{}'
```

Ответ:
```json
{"detail":"Inventory clear endpoint is temporarily disabled"}
```

### `POST /v1/users/{telegram_id}/farm/reset` (временно отключено)
Сейчас эндпоинт отключён и возвращает `403`.

## 5) Stats / Analytics

### `GET /v1/stats/users/count`
Запрос:
```powershell
irm "$BASE_URL/v1/stats/users/count" -Headers @{ "X-API-Key" = $API_KEY }
```
Ответ:
```json
{"users":1234}
```

### `GET /v1/stats/balances/top`
Запрос:
```powershell
irm "$BASE_URL/v1/stats/balances/top?limit=10" -Headers @{ "X-API-Key" = $API_KEY }
```
Ответ:
```json
{"items":[{"id":1,"total":"123.45","balance":"100.00","deposit":"23.45"}]}
```

### `GET /v1/stats/balances/summary`
Запрос:
```powershell
irm "$BASE_URL/v1/stats/balances/summary" -Headers @{ "X-API-Key" = $API_KEY }
```
Ответ:
```json
{"bc":{"sum":"...","avg":"..."},"rub":{"sum":"...","avg":"..."},"deposit":{"sum":"...","avg":"..."},"debt":{"sum":"...","avg":"..."}}
```

### `GET /v1/stats/active`
Запрос:
```powershell
irm "$BASE_URL/v1/stats/active?days=7" -Headers @{ "X-API-Key" = $API_KEY }
```
Ответ:
```json
{"days":7,"active_users":123}
```

### `GET /v1/stats/inventory/top-items`
Запрос:
```powershell
irm "$BASE_URL/v1/stats/inventory/top-items?limit=50" -Headers @{ "X-API-Key" = $API_KEY }
```
Ответ:
```json
{"items":[{"item_key":"1_10","total_qty":999}]}
```

## 6) Config (Singletons)

Сюда входят только `minecraft_goods` и `mini_game_farm` (админы не доступны через API).

### `GET /v1/config/minecraft_goods`
Запрос:
```powershell
irm "$BASE_URL/v1/config/minecraft_goods" -Headers @{ "X-API-Key" = $API_KEY }
```
Ответ:
```json
{"key":"minecraft_goods","value":{...}}
```

### `PUT /v1/config/minecraft_goods`
Полная замена конфига.

Запрос (пример — загрузить JSON из файла):
```powershell
$body = Get-Content -Raw ".\\data\\json_database\\minecraft_goods.json"
irm -Method Put "$BASE_URL/v1/config/minecraft_goods" -Headers @{ "X-API-Key" = $API_KEY } -ContentType "application/json" -Body $body
```

### `PATCH /v1/config/minecraft_goods`
Точечная модификация (операции):

`set_item_field` (пример):
```powershell
irm -Method Patch "$BASE_URL/v1/config/minecraft_goods" `
  -Headers @{ "X-API-Key" = $API_KEY } `
  -ContentType "application/json" `
  -Body '{"op":"set_item_field","category_id":"1","item_id":"10","field":"base_price","value":"100.00"}'
```

### `GET /v1/config/mini_game_farm`
Запрос:
```powershell
irm "$BASE_URL/v1/config/mini_game_farm" -Headers @{ "X-API-Key" = $API_KEY }
```

### `PUT /v1/config/mini_game_farm`
Запрос (пример — загрузить JSON из файла):
```powershell
$body = Get-Content -Raw ".\\data\\json_database\\mini_game_farm.json"
irm -Method Put "$BASE_URL/v1/config/mini_game_farm" -Headers @{ "X-API-Key" = $API_KEY } -ContentType "application/json" -Body $body
```

