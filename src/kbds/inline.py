from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder




def get_callback_btns(btns: dict[str, str], sizes: tuple[int] = (1,), urls=None):
    """
    Функция для генерации inline клавиатуры

    btns = {
            'название кнопки':'callback_data', 
            'перейти на сайт':'url' # --> автоматичекое преобразование в url
        }

    sizes - (1, 2, 1) кол-во кнопок в i ряду.
    Если кнопок больше, чем указано в sizes, к ним применится последнее

    urls = {
            'перейти на сайт':'url' # --> всегда url
        }
    """

    

    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        if "http" in data:
            keyboard.add(InlineKeyboardButton(text=text, url=data))
        else:
            keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    if urls is not None:
        for text, data in urls.items():
            keyboard.add(InlineKeyboardButton(text=text, url=data))
    

    return keyboard.adjust(*sizes).as_markup()





