"""Profile management handler."""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.db_models import User, Profile
from bot.keyboards.inline import profile_action_keyboard

router = Router()


@router.callback_query(F.data.startswith("profile:"))
async def cb_profile_detail(callback: CallbackQuery, user: User, db: AsyncSession):
    profile_id = int(callback.data.split(":")[1])
    result = await db.execute(
        select(Profile).where(Profile.id == profile_id, Profile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        await callback.answer("Perfil no encontrado")
        return

    status = "🟢 Activo" if profile.is_active else "🔴 Inactivo"
    phones = ", ".join(profile.phones) if profile.phones else "No especificado"
    emails = ", ".join(profile.emails) if profile.emails else "No especificado"

    await callback.message.edit_text(
        f"{status}\n\n"
        f"🗺 <b>Provincia:</b> {profile.province_name}\n"
        f"📄 <b>Trámite:</b> {profile.tramite_name}\n"
        f"🏢 <b>Oficina:</b> {profile.oficina_name or 'Cualquiera'}\n"
        f"📅 <b>Fechas:</b> {profile.date_from} → {profile.date_to}\n"
        f"📱 <b>Teléfonos:</b> {phones}\n"
        f"📧 <b>Emails:</b> {emails}\n\n"
        f"🔢 ID: {profile.id}",
        reply_markup=profile_action_keyboard(profile.id, profile.is_active)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("profile_action:"))
async def cb_profile_action(callback: CallbackQuery, user: User, db: AsyncSession):
    parts = callback.data.split(":")
    if parts[1] == "back":
        await callback.message.delete()
        await callback.answer()
        return

    profile_id, action = int(parts[1]), parts[2]
    result = await db.execute(
        select(Profile).where(Profile.id == profile_id, Profile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        await callback.answer("Perfil no encontrado")
        return

    if action == "stop":
        profile.is_active = False
        await db.commit()
        await callback.answer("⏹ Monitoreo detenido")
    elif action == "start":
        profile.is_active = True
        await db.commit()
        await callback.answer("▶️ Monitoreo activado")
    elif action == "delete":
        await db.delete(profile)
        await db.commit()
        await callback.message.edit_text("🗑 Perfil eliminado.")
        await callback.answer("Perfil eliminado")
        return

    await callback.message.edit_text(
        f"✅ Perfil actualizado — {'🟢 Activo' if profile.is_active else '🔴 Inactivo'}",
        reply_markup=profile_action_keyboard(profile.id, profile.is_active)
    )
