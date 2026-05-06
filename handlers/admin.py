"""Admin-only handler for OTP resolution via Telegram."""
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import httpx

from config import settings

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == settings.ADMIN_TELEGRAM_ID


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "🔐 <b>Panel Admin — CitaMonitor</b>\n\n"
        "Comandos disponibles:\n"
        "• /admin_stats — Estadísticas del sistema\n"
        "• /admin_jobs — Listar trabajos activos\n"
        "• /admin_otp — OTPs pendientes\n\n"
        "El dashboard completo está disponible en la web."
    )


@router.message(Command("admin_stats"))
async def cmd_admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.BACKEND_URL}/api/system/stats", timeout=10)
            stats = resp.json()
        await message.answer(
            "📊 <b>Estadísticas del sistema:</b>\n\n"
            f"👥 Usuarios: <b>{stats['total_users']}</b>\n"
            f"🔄 Jobs activos: <b>{stats['active_jobs']}</b>\n"
            f"✅ Jobs encontrados: <b>{stats['found_jobs']}</b>\n"
            f"📋 Total jobs: <b>{stats['total_jobs']}</b>\n"
            f"🔐 OTPs pendientes: <b>{stats['pending_otp']}</b>\n"
            f"📈 Tasa de éxito: <b>{stats['success_rate']}%</b>"
        )
    except Exception as e:
        await message.answer(f"❌ Error al obtener estadísticas: {e}")


async def notify_admin_otp(bot: Bot, job_id: int, user_name: str, otp_id: int, screenshot_path: str = None):
    """Send OTP alert to admin via Telegram."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Resolver OTP", callback_data=f"admin_otp_resolve:{otp_id}")

    text = (
        "🔐 <b>OTP REQUERIDA</b>\n\n"
        f"👤 Usuario: <b>{user_name}</b>\n"
        f"🔧 Job ID: <b>{job_id}</b>\n"
        f"🆔 OTP ID: <b>{otp_id}</b>\n\n"
        "⚡ <b>Acción requerida inmediatamente.</b>\n"
        "Responde con el código OTP o usa el dashboard."
    )

    if screenshot_path:
        try:
            from aiogram.types import FSInputFile
            photo = FSInputFile(screenshot_path)
            await bot.send_photo(
                settings.ADMIN_TELEGRAM_ID,
                photo=photo,
                caption=text,
                reply_markup=builder.as_markup()
            )
            return
        except Exception:
            pass

    await bot.send_message(
        settings.ADMIN_TELEGRAM_ID,
        text,
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("admin_otp_resolve:"))
async def cb_admin_otp_resolve(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Acceso denegado")
        return
    otp_id = callback.data.split(":")[1]
    await callback.message.answer(
        f"✏️ Escribe el código OTP para la solicitud #{otp_id}:\n"
        f"(Responde a este mensaje con el código)"
    )
    await callback.answer()
