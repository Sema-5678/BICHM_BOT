import logging
from typing import Callable, Awaitable, Any, TypeVar, Optional
from functools import wraps
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

T = TypeVar('T')

logger = logging.getLogger(__name__)

def protected_callback(handler: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[Optional[T]]]:
    """
    Decorator to protect callbacks from being used by unauthorized users.
    Checks if the callback's user_id matches the message's user_id.
    """
    @wraps(handler)
    async def wrapper(callback: CallbackQuery, *args: Any, **kwargs: Any) -> Optional[T]:
        # Extract callback data if it's a ShopCallback
        if isinstance(callback, CallbackQuery):
            print(callback.data)
            callback_data = callback.data.split(":")

            # if 'callback_data' in kwargs and hasattr(kwargs['callback_data'], 'user_id'):
            #     callback_data = kwargs['callback_data']
            #     if callback.from_user.id != callback_data.user_id:
            #         await callback.answer("❌ Эта кнопка не для вас!", show_alert=True)
            #         return None

            if len(callback_data)>=2:
                if callback.from_user.id != int(callback_data[1]):
                    await callback.answer("❌ Эта кнопка не для вас!", show_alert=True)
                    return None
                # else:
                    # print("✅ Callback принят от пользователя")
                    # logger.info(f"✅ Callback {callback.data} принят от пользователя {callback.from_user.id}")
            else:
                print('В колбеке нет id')

        

        # For other callbacks, check if there's a state with user_id




        # state: Optional[FSMContext] = kwargs.get('state')
        # if state:
        #     state_data = await state.get_data()
        #     if 'user_id' in state_data and state_data['user_id'] != callback.from_user.id:
        #         await callback.answer("❌ Эта кнопка не для вас!", show_alert=True)
        #         return None
        


        # If all checks pass, call the original handler
        return await handler(callback, *args, **kwargs)
    
    return wrapper




