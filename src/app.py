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



from aiogram.client.session.aiohttp import AiohttpSession
# Ошибки Telegram API и сети
from aiogram.exceptions import TelegramNetworkError, TelegramAPIError

# Ошибки aiohttp (например, не удалось подключиться)
from aiohttp import ClientConnectorError, ClientOSError

# Ошибки socks-прокси
from python_socks._errors import ProxyError

# ENABLE_TELEGRAM_LOGGING = os.getenv('ENABLE_TELEGRAM_LOGGING').lower()


from aiogram.types import Message

def patch_message_methods(
    retries: int = 3,
    base_delay: float = 1.0,
    methods: tuple[str, ...] = (
        "answer",
        "reply",
        "edit_text",
        "edit_caption",
        "edit_reply_markup",
        "delete",
        "forward",
        "copy_to",
        "send_copy",
    ),
):
    """
    Добавляет retry-логику ко всем основным методам Message.
    """

    def make_safe_method(func_name: str):
        original_func = getattr(Message, func_name)

        async def safe_wrapper(self: Message, *args, **kwargs):
            delay = base_delay
            for attempt in range(1, retries + 1):
                try:
                    return await original_func(self, *args, **kwargs)
                except (ProxyError, ClientConnectorError, TelegramNetworkError, asyncio.TimeoutError) as e:
                    logger.warning(
                        f"[Retry {attempt}/{retries}] Ошибка при вызове Message.{func_name}: {e.__class__.__name__}: {e}"
                    )
                    if attempt == retries:
                        logger.error(
                            f"❌ Message.{func_name} окончательно не выполнен после {retries} попыток."
                        )
                        raise
                    await asyncio.sleep(delay)
                    delay *= 2  # экспоненциальная задержка

        return safe_wrapper

    for name in methods:
        if hasattr(Message, name):
            setattr(Message, name, make_safe_method(name))
            logger.debug(f"✅ Переопределён метод Message.{name} с retry-логикой")







# try:
#     session = AiohttpSession(proxy='http://proxy.server:3128')
#     bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML), session=session)
# except:
#     bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))



bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# ALLOWED_UPDATES = ['message', 'edited_message', 'callback_query']


bot.my_admins_list = []

# Настраиваем логирование
logger = setup_logging(bot, enable_telegram_logging=config.ENABLE_TELEGRAM_LOGGING)
patch_message_methods()


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
