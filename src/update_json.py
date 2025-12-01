from utils.json_engine import get_all_users, update_user_data

f = get_all_users()
for user_id, user_data in f:
    # new_data = {
    #     "inventory" : {},
    #     "minecraft_goods_count_season" : {},
    #     # "minecraft_username" : {},
    #     "rub_balance" : {},
    #     "balance" : 10_000,
    #     "deposit":0

    # }

    # user_data['deposit'] = "0"
    # user_data['rub_balance'] = "0"
    # user_data['balance'] = "0"
    # user_data['min_deposit'] = "0"



    # if user_data['balance'] >=10_000:
    #     user_data['balance'] = 5_000
    #     user_data['rub_balance'] = 3

    


    # if user_data['balance'] >=100_000:
    #     user_data['balance'] = 10_000
    #     user_data['rub_balance'] = 10

    








    # user_data.update(new_data)

    update_user_data(user_id, user_data)

print("Done")