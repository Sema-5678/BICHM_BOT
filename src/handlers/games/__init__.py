from aiogram import Router

from .blackjack import blackjack_router
from .amateur_blackjack import amateur_blackjack_router
from .casino import casino_router
from .robbery import robbery_router
from .tic_tac_toe import ttt_router
from .farm import farm_router


games_router = Router()
# games_router.include_router(blackjack_router)
# games_router.include_router(amateur_blackjack_router)
games_router.include_router(casino_router)
games_router.include_router(robbery_router)
games_router.include_router(ttt_router)
games_router.include_router(farm_router)

__all__ = [
    "games_router",
    "blackjack_router",
    "amateur_blackjack_router",
    "casino_router",
    "robbery_router",
    "ttt_router",
    "farm_router",
]


