# Migration scripts

## JSON → SQLite (singletons)

Migrates these files from `data/json_database/` into SQLite table `singletons`:

- `admins_data.json` → key `admins_data`
- `minecraft_goods.json` → key `minecraft_goods`
- `mini_game_farm.json` → key `mini_game_farm`

Run (from repo root):

```powershell
python scripts/migrate_singletons_from_json.py
```

Optional:

```powershell
python scripts/migrate_singletons_from_json.py --json-dir .\\data\\json_database --verbose
```

