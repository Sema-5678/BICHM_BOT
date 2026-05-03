from __future__ import annotations

import argparse
import asyncio

from database.engine import create_db, drop_db


async def _run(action: str) -> None:
    if action == "create":
        await create_db()
        return
    if action == "drop":
        await drop_db()
        return
    raise ValueError(f"Unknown action: {action}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Database helper (SQLite/SQLAlchemy async).")
    parser.add_argument("action", choices=("create", "drop"))
    args = parser.parse_args()
    asyncio.run(_run(args.action))


if __name__ == "__main__":
    main()

