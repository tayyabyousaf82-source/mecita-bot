"""Common bot commands: /start, /help, /mis_citas."""
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db_models import User, Profile
from keyboards.inline import profile_list_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, user: User):
    await message.answer(
        f"👋 <b>Hola, {user.first_name}!</b>\n\n"
        "Soy <b>CitaMonitor</b> — tu asistente para monitorear citas en el sistema ICP del Gobierno de España.\n\n"
        "📋 <b>Comandos disponibles:</b>\n"
        "• /nueva_cita — Crear un nuevo perfil de monitoreo\n"
        "• /mis_citas — Ver tus perfiles activos\n"
        "• /ayuda — Ayuda y más información\n\n"
        "🔔 Te notificaré <b>inmediatamente</b> cuando encuentre disponibilidad."
    )


@router.message(Command("ayuda"))
async def cmd_help(message: Message):
    await message.answer(
        "ℹ️ <b>Cómo funciona CitaMonitor:</b>\n\n"
        "1️⃣ Usa /nueva_cita para configurar tu búsqueda\n"
        "2️⃣ Selecciona provincia, trámite y rango de fechas\n"
        "3️⃣ Confirma para iniciar el monitoreo\n"
        "4️⃣ Recibirás una notificación en cuanto haya cita disponible\n\n"
        "⚠️ <b>Importante:</b>\n"
        "• El sistema monitorea la disponibilidad de forma automática\n"
        "• No realiza reservas automáticas\n"
        "• Respeta los tiempos de espera del servidor\n\n"
        "🔒 Tus datos están protegidos y encriptados."
    )


@router.message(Command("mis_citas"))
async def cmd_mis_citas(message: Message, user: User, db: AsyncSession):
    result = await db.execute(
        select(Profile).where(Profile.user_id == user.id).order_by(Profile.created_at.desc())
    )
    profiles = result.scalars().all()

    if not profiles:
        await message.answer(
            "📭 No tienes perfiles de monitoreo configurados.\n\n"
            "Usa /nueva_cita para crear uno."
        )
        return

    text = f"📋 <b>Tus perfiles de monitoreo ({len(profiles)}):</b>\n\n"
    profile_data = []
    for p in profiles:
        status = "🟢 Activo" if p.is_active else "🔴 Inactivo"
        text += f"{status} — <b>{p.province_name}</b>\n"
        text += f"   📌 {p.tramite_name[:50]}...\n"
        text += f"   📅 {p.date_from} → {p.date_to}\n\n"
        profile_data.append({
            "id": p.id,
            "province_name": p.province_name,
            "tramite_name": p.tramite_name,
            "is_active": p.is_active,
        })

    await message.answer(
        text,
        reply_markup=profile_list_keyboard(profile_data)
    )
