# API testing

## 0) Start the API

From repo root:

```powershell
uvicorn api.main:app --app-dir src --host 127.0.0.1 --port 8000
```

## 1) Quick manual checks (PowerShell)

Set env vars (PowerShell):

```powershell
$env:API_BASE_URL="http://127.0.0.1:8000"
$env:API_KEY="<your-api-key>"
$env:TG_ID="5273608148"
```

Health (PowerShell `Invoke-RestMethod`):

```powershell
irm "$env:API_BASE_URL/health"
irm "$env:API_BASE_URL/ready"
irm "$env:API_BASE_URL/version"
```

Get user card:

```powershell
irm "$env:API_BASE_URL/v1/users/$env:TG_ID" -Headers @{ "X-API-Key" = $env:API_KEY }
```

Add BC +10.50:

```powershell
irm -Method Post "$env:API_BASE_URL/v1/users/$env:TG_ID/balance/bc" -Headers @{ "X-API-Key" = $env:API_KEY } -ContentType "application/json" -Body '{"amount":"10.50","mode":"delta"}'
```

Remove RUB -55.10:

```powershell
irm -Method Post "$env:API_BASE_URL/v1/users/$env:TG_ID/balance/rub" -Headers @{ "X-API-Key" = $env:API_KEY } -ContentType "application/json" -Body '{"amount":"-55.10","mode":"delta"}'
```

Farm endpoints (temporarily disabled):

```powershell
# disabled for now (will return 403)
irm -Method Post "$env:API_BASE_URL/v1/users/$env:TG_ID/farm/reset" -Headers @{ "X-API-Key" = $env:API_KEY } -ContentType "application/json" -Body '{"confirm":true}'
irm "$env:API_BASE_URL/v1/users/$env:TG_ID/farm" -Headers @{ "X-API-Key" = $env:API_KEY }
```

Inventory add/remove (clear is temporarily disabled):

```powershell
irm -Method Post "$env:API_BASE_URL/v1/users/$env:TG_ID/inventory/add" -Headers @{ "X-API-Key" = $env:API_KEY } -ContentType "application/json" -Body '{"category_id":"1","item_id":"10","quantity":3}'
irm "$env:API_BASE_URL/v1/users/$env:TG_ID/inventory" -Headers @{ "X-API-Key" = $env:API_KEY }
irm -Method Post "$env:API_BASE_URL/v1/users/$env:TG_ID/inventory/remove" -Headers @{ "X-API-Key" = $env:API_KEY } -ContentType "application/json" -Body '{"category_id":"1","item_id":"10","quantity":2}'
# disabled for now (will return 403)
irm -Method Post "$env:API_BASE_URL/v1/users/$env:TG_ID/inventory/clear" -Headers @{ "X-API-Key" = $env:API_KEY } -ContentType "application/json" -Body '{}'
```

## 2) Full smoke test script

From repo root:

```powershell
python scripts/api_smoke_test.py --base-url http://127.0.0.1:8000 --api-key "<your-api-key>" --telegram-id 5273608148
```

The script prints logs and fails fast on unexpected responses.
