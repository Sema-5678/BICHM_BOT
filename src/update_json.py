import asyncio

from utils.sqlite_storage import get_all_users, update_user_data


async def main() -> None:
    users = await get_all_users()
    for user_id, user_data in users:
        await update_user_data(user_id, user_data)

    print("Done")


if __name__ == "__main__":
    asyncio.run(main())
