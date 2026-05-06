from aiogram import Router
from handlers import common, nueva_cita, profile, admin

router = Router()
router.include_router(common.router)
router.include_router(nueva_cita.router)
router.include_router(profile.router)
router.include_router(admin.router)
