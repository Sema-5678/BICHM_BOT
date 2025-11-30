from utils.json_engine import get_all_users, update_user_data

f = get_all_users()
for user_id, user_data in f:
    new_data = {
        "inventory" : {},
        "minecraft_goods_count_season" : {},
        # "minecraft_username" : {},
        "rub_balance" : {},

    }
    user_data.update(new_data)

    update_user_data(user_id, user_data)

print("Done")