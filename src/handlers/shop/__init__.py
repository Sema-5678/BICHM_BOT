from aiogram import Router

from .minecraft.shop import minecraft_shop_router
from .replenishment import replenishment_router


shop_router = Router()
shop_router.include_router(minecraft_shop_router)
shop_router.include_router(replenishment_router)

__all__ = [
    "minecraft_shop_router",
    "replenishment_router",
]


