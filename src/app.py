import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand
from dotenv import find_dotenv, load_dotenv

from utils.background_tasks import interest_scheduler
load_dotenv(find_dotenv())
import config


from common.bot_cmds_list import private, group

# Импортируем настройку логирования
from utils.logging_setup import setup_logging


# ALLOWED_UPDATES = ['message', 'edited_message', 'callback_query']

# Определяем, нужно ли включать логирование в Telegram
ENABLE_TELEGRAM_LOGGING = os.getenv('ENABLE_TELEGRAM_LOGGING', 'False').lower()

bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
bot.my_admins_list = []

# Настраиваем логирование
logger, error_handler = setup_logging(bot, enable_telegram_logging=ENABLE_TELEGRAM_LOGGING)


dp = Dispatcher()




async def on_startup(bot):
    """Функция, выполняемая при запуске бота"""
    logger.info("Бот запускается...")
    
    # Запускаем фоновые задачи
    await interest_scheduler.start()
    logger.info("Фоновые задачи запущены")
    
    # await bot.set_my_commands(private)
    # logger.info("Команды бота установлены")



async def on_shutdown(bot):
    """Функция, выполняемая при остановке бота"""
    logger.info("Бот останавливается...")
    
    # Останавливаем фоновые задачи
    if interest_scheduler:
        await interest_scheduler.stop()
    logger.info("Фоновые задачи остановлены")


async def main():
    # from handlers.user_private import user_private_router
    # from handlers.games import games_router
    # from handlers.bank_handlers import bank_router
    # from handlers.user_group import user_group_router
    from handlers.common_cmds import common_router



    # dp.include_router(user_private_router)
    # dp.include_router(games_router
    # dp.include_router(bank_router)
    # dp.include_router(admin_router)
    # dp.include_router(user_group_router)
    dp.include_router(common_router)





    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await bot.delete_webhook(drop_pending_updates=True)
    
    
    await bot.delete_my_commands(scope=types.BotCommandScopeDefault())
    await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    await bot.delete_my_commands(scope=types.BotCommandScopeAllGroupChats())
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllChatAdministrators())
    # await bot.delete_my_commands(scope=types.BotCommandScopeChat(chat_id=GROUP_CHAT_ID))
    # await bot.delete_my_commands(scope=types.BotCommandScopeChatAdministrators(chat_id=GROUP_CHAT_ID))


    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await bot.set_my_commands(commands=group, scope=types.BotCommandScopeAllGroupChats())

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

asyncio.run(main())
