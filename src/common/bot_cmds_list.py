from aiogram.types import BotCommand
from common.data_for_bot import TEXTS


group = [
    BotCommand(command=item["command"], description=item["description"]) for item in TEXTS["commands"]["group"]
]


private = [
    *group,
    *(BotCommand(command=item["command"], description=item["description"]) for item in TEXTS["commands"]["private_extra"]),
]

