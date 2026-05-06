"""
/nueva_cita handler — full FSM flow for creating a monitoring profile.
"""
from datetime import date, datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from states.nueva_cita import NuevaCitaStates
from keyboards.inline import (
    province_keyboard, tramite_keyboard, confirm_keyboard, skip_keyboard
)
from db_models import User, Profile
from config import settings

router = Router()


def build_summary(data: dict) -> str:
    """Build a human-readable summary of the profile data."""
    phones = ", ".join(data.get("phones", [])) or "No especificado"
    emails = ", ".join(data.get("emails", [])) or "No especificado"
    certs = ", ".join(data.get("certificates", [])) or "No especificado"

    return (
        "📋 <b>Resumen de tu perfil de monitoreo:</b>\n\n"
        f"🗺 <b>Provincia:</b> {data.get('province_name', '—')}\n"
        f"📄 <b>Trámite:</b> {data.get('tramite_name', '—')}\n"
        f"🏢 <b>Oficina:</b> {data.get('oficina_name', 'Cualquiera')}\n"
        f"📅 <b>Fechas:</b> {data.get('date_from', '—')} → {data.get('date_to', '—')}\n"
        f"📱 <b>Teléfonos:</b> {phones}\n"
        f"📧 <b>Emails:</b> {emails}\n"
        f"📜 <b>Certificados:</b> {certs}\n\n"
        "¿Confirmas la activación del monitoreo?"
    )


@router.message(Command("nueva_cita"))
async def cmd_nueva_cita(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(NuevaCitaStates.SELECT_PROVINCE)
    await message.answer(
        "🗺 <b>Paso 1/6 — Selecciona la provincia:</b>\n\n"
        "Elige la provincia donde necesitas la cita:",
        reply_markup=province_keyboard()
    )


@router.callback_query(NuevaCitaStates.SELECT_PROVINCE, F.data.startswith("province:"))
async def cb_select_province(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":", 2)
    if parts[1] == "more":
        await callback.answer("Por favor, escribe el nombre de tu provincia")
        return

    code, name = parts[1], parts[2]
    await state.update_data(province_code=code, province_name=name)
    await state.set_state(NuevaCitaStates.SELECT_TRAMITE)

    await callback.message.edit_text(
        f"✅ Provincia: <b>{name}</b>\n\n"
        "📄 <b>Paso 2/6 — Selecciona el trámite:</b>",
        reply_markup=tramite_keyboard(code)
    )
    await callback.answer()


@router.callback_query(NuevaCitaStates.SELECT_TRAMITE, F.data.startswith("tramite:"))
async def cb_select_tramite(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":", 2)
    code, name = parts[1], parts[2]
    await state.update_data(tramite_code=code, tramite_name=name)
    await state.set_state(NuevaCitaStates.SELECT_OFICINA)

    await callback.message.edit_text(
        f"✅ Trámite: <b>{name[:60]}</b>\n\n"
        "🏢 <b>Paso 3/6 — Oficina (opcional):</b>\n\n"
        "Escribe el nombre de la oficina, o pulsa <i>Omitir</i> para buscar en todas:",
        reply_markup=skip_keyboard("oficina")
    )
    await callback.answer()


@router.callback_query(NuevaCitaStates.SELECT_OFICINA, F.data == "skip:oficina")
async def cb_skip_oficina(callback: CallbackQuery, state: FSMContext):
    await state.update_data(oficina_code=None, oficina_name="Cualquiera")
    await state.set_state(NuevaCitaStates.SELECT_DATE_FROM)
    await callback.message.edit_text(
        "📅 <b>Paso 4/6 — Fecha de inicio:</b>\n\n"
        "Escribe la fecha mínima para la cita (formato: DD/MM/AAAA):\n"
        "<i>Ejemplo: 15/06/2025</i>"
    )
    await callback.answer()


@router.message(NuevaCitaStates.SELECT_OFICINA)
async def msg_oficina(message: Message, state: FSMContext):
    await state.update_data(oficina_name=message.text, oficina_code="custom")
    await state.set_state(NuevaCitaStates.SELECT_DATE_FROM)
    await message.answer(
        "📅 <b>Paso 4/6 — Fecha de inicio:</b>\n\n"
        "Escribe la fecha mínima (formato: DD/MM/AAAA):"
    )


@router.message(NuevaCitaStates.SELECT_DATE_FROM)
async def msg_date_from(message: Message, state: FSMContext):
    try:
        d = datetime.strptime(message.text.strip(), "%d/%m/%Y").date()
        if d < date.today():
            raise ValueError("past date")
    except ValueError:
        await message.answer("❌ Fecha no válida. Usa el formato DD/MM/AAAA y una fecha futura.")
        return

    await state.update_data(date_from=d.isoformat())
    await state.set_state(NuevaCitaStates.SELECT_DATE_TO)
    await message.answer(
        "📅 <b>Fecha de fin:</b>\n\n"
        "Escribe la fecha máxima (formato: DD/MM/AAAA):"
    )


@router.message(NuevaCitaStates.SELECT_DATE_TO)
async def msg_date_to(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        d = datetime.strptime(message.text.strip(), "%d/%m/%Y").date()
        d_from = date.fromisoformat(data["date_from"])
        if d <= d_from:
            raise ValueError("must be after date_from")
    except ValueError:
        await message.answer("❌ Fecha no válida. Debe ser posterior a la fecha de inicio.")
        return

    await state.update_data(date_to=d.isoformat())
    await state.set_state(NuevaCitaStates.ADD_PHONES)
    await message.answer(
        "📱 <b>Paso 5/6 — Teléfono(s):</b>\n\n"
        "Escribe tu número de teléfono (puedes añadir varios separados por comas):\n"
        "<i>Ejemplo: +34600000001, +34600000002</i>",
        reply_markup=skip_keyboard("phones")
    )


@router.callback_query(NuevaCitaStates.ADD_PHONES, F.data == "skip:phones")
async def cb_skip_phones(callback: CallbackQuery, state: FSMContext):
    await state.update_data(phones=[])
    await state.set_state(NuevaCitaStates.ADD_EMAILS)
    await callback.message.edit_text(
        "📧 <b>Email(s):</b>\n\n"
        "Escribe tu email (puedes añadir varios separados por comas):",
        reply_markup=skip_keyboard("emails")
    )
    await callback.answer()


@router.message(NuevaCitaStates.ADD_PHONES)
async def msg_phones(message: Message, state: FSMContext):
    phones = [p.strip() for p in message.text.split(",") if p.strip()]
    await state.update_data(phones=phones)
    await state.set_state(NuevaCitaStates.ADD_EMAILS)
    await message.answer(
        "📧 <b>Email(s):</b>\n\n"
        "Escribe tu email (puedes añadir varios separados por comas):",
        reply_markup=skip_keyboard("emails")
    )


@router.callback_query(NuevaCitaStates.ADD_EMAILS, F.data == "skip:emails")
async def cb_skip_emails(callback: CallbackQuery, state: FSMContext):
    await state.update_data(emails=[])
    await _show_confirm(callback.message, state)
    await callback.answer()


@router.message(NuevaCitaStates.ADD_EMAILS)
async def msg_emails(message: Message, state: FSMContext):
    emails = [e.strip() for e in message.text.split(",") if e.strip()]
    await state.update_data(emails=emails)
    await _show_confirm(message, state)


async def _show_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(NuevaCitaStates.CONFIRM)
    await message.answer(build_summary(data), reply_markup=confirm_keyboard())


@router.callback_query(NuevaCitaStates.CONFIRM, F.data == "confirm:yes")
async def cb_confirm(callback: CallbackQuery, state: FSMContext, user: User, db: AsyncSession):
    data = await state.get_data()
    await state.clear()

    profile = Profile(
        user_id=user.id,
        name=f"{data['province_name']} — {data['tramite_name'][:50]}",
        province_code=data["province_code"],
        province_name=data["province_name"],
        tramite_code=data["tramite_code"],
        tramite_name=data["tramite_name"],
        oficina_code=data.get("oficina_code"),
        oficina_name=data.get("oficina_name"),
        date_from=date.fromisoformat(data["date_from"]),
        date_to=date.fromisoformat(data["date_to"]),
        phones=data.get("phones", []),
        emails=data.get("emails", []),
        certificates=data.get("certificates", []),
        is_active=True,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    # Enqueue monitoring job via backend API
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.BACKEND_URL}/api/jobs/internal/start",
                json={"profile_id": profile.id, "user_id": user.id},
                timeout=10,
            )
    except Exception:
        pass  # Job will be picked up by worker on next scan

    await callback.message.edit_text(
        "✅ <b>¡Monitoreo activado!</b>\n\n"
        f"🗺 Provincia: <b>{profile.province_name}</b>\n"
        f"📄 Trámite: <b>{profile.tramite_name[:60]}</b>\n"
        f"📅 Rango: {profile.date_from} → {profile.date_to}\n\n"
        "🔔 Te notificaré en cuanto detecte disponibilidad.\n"
        "Usa /mis_citas para ver el estado."
    )
    await callback.answer("¡Monitoreo iniciado!")


@router.callback_query(NuevaCitaStates.CONFIRM, F.data == "confirm:cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Monitoreo cancelado. Usa /nueva_cita para empezar de nuevo.")
    await callback.answer()


@router.callback_query(NuevaCitaStates.CONFIRM, F.data.startswith("edit:"))
async def cb_edit_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split(":")[1]
    if field == "province":
        await state.set_state(NuevaCitaStates.SELECT_PROVINCE)
        await callback.message.edit_text("🗺 Selecciona la provincia:", reply_markup=province_keyboard())
    elif field == "tramite":
        data = await state.get_data()
        await state.set_state(NuevaCitaStates.SELECT_TRAMITE)
        await callback.message.edit_text("📄 Selecciona el trámite:", reply_markup=tramite_keyboard(data.get("province_code", "")))
    elif field == "dates":
        await state.set_state(NuevaCitaStates.SELECT_DATE_FROM)
        await callback.message.edit_text("📅 Nueva fecha de inicio (DD/MM/AAAA):")
    elif field == "phones":
        await state.set_state(NuevaCitaStates.ADD_PHONES)
        await callback.message.edit_text("📱 Nuevos teléfonos (separados por comas):")
    elif field == "emails":
        await state.set_state(NuevaCitaStates.ADD_EMAILS)
        await callback.message.edit_text("📧 Nuevos emails (separados por comas):")
    await callback.answer()
