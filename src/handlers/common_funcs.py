



from aiogram.types import CallbackQuery


async def send_msg_call(event, **kwargs):
    # msg_obj = {"text": text, "reply_markup": kbds}

    if isinstance(event, CallbackQuery):
        # await event.answer()
        await event.message.edit_text(**kwargs)
    else:
        await event.answer(**kwargs)

