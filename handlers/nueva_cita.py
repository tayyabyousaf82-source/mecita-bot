"""
/nueva_cita handler — FSM flow for creating a monitoring profile.
Uses | as separator in callback_data to avoid split issues.
"""
from datetime import date, datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import os

from states.nueva_cita import NuevaCitaStates
from keyboards.inline import (
    province_keyboard, tramite_keyboard, confirm_keyboard, skip_keyboard, province_keyboard_page
)
from db_models import User, Profile

router = Router()
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


def build_summary(data: dict) -> str:
    phones = ", ".join(data.get("phones", [])) or "No especificado"
    emails = ", ".join(data.get("emails", [])) or "No especificado"
    return (
        "📋 <b>Resumen de tu perfil de monitoreo:</b>\n\n"
        f"🗺 <b>Provincia:</b> {data.get('province_name', '—')}\n"
        f"📄 <b>Trámite:</b> {data.get('tramite_name', '—')}\n"
        f"🏢 <b>Oficina:</b> {data.get('oficina_name', 'Cualquiera')}\n"
        f"📅 <b>Fechas:</b> {data.get('date_from', '—')} → {data.get('date_to', '—')}\n"
        f"📱 <b>Teléfonos:</b> {phones}\n"
        f"📧 <b>Emails:</b> {emails}\n\n"
        "¿Confirmas la activación del monitoreo?"
    )


# ── /nueva_cita ────────────────────────────────────────────────
@router.message(Command("nueva_cita"))
async def cmd_nueva_cita(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(NuevaCitaStates.SELECT_PROVINCE)
    await message.answer(
        "🗺 <b>Paso 1/6 — Selecciona la provincia:</b>\n\n"
        "Elige la provincia donde necesitas la cita:",
        reply_markup=province_keyboard()
    )


# ── Province select ────────────────────────────────────────────
@router.callback_query(F.data.startswith("prov|"))
async def cb_select_province(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("|")
    code = parts[1]
    name = parts[2]
    await state.update_data(province_code=code, province_name=name)
    await state.set_state(NuevaCitaStates.SELECT_TRAMITE)
    await callback.message.edit_text(
        f"✅ Provincia: <b>{name}</b>\n\n"
        "📄 <b>Paso 2/6 — Selecciona el trámite:</b>",
        reply_markup=tramite_keyboard(code)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("prov_more|"))
async def cb_province_more(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("|")[1])
    await callback.message.edit_reply_markup(reply_markup=province_keyboard_page(page))
    await callback.answer()


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()


# ── Tramite select ─────────────────────────────────────────────
@router.callback_query(F.data.startswith("tram|"))
async def cb_select_tramite(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("|")
    code = parts[1]
    name = parts[2]
    await state.update_data(tramite_code=code, tramite_name=name)
    await state.set_state(NuevaCitaStates.SELECT_OFICINA)
    await callback.message.edit_text(
        f"✅ Trámite: <b>{name[:60]}</b>\n\n"
        "🏢 <b>Paso 3/6 — Oficina (opcional):</b>\n\n"
        "Escribe el nombre de la oficina, o pulsa <i>Omitir</i> para buscar en todas:",
        reply_markup=skip_keyboard("oficina")
    )
    await callback.answer()


# ── Oficina ────────────────────────────────────────────────────
@router.callback_query(F.data == "skip|oficina")
async def cb_skip_oficina(callback: CallbackQuery, state: FSMContext):
    await state.update_data(oficina_code=None, oficina_name="Cualquiera")
    await state.set_state(NuevaCitaStates.SELECT_DATE_FROM)
    await callback.message.edit_text(
        "📅 <b>Paso 4/6 — Fecha de inicio:</b>\n\n"
        "Escribe la fecha mínima para la cita:\n"
        "<i>Formato: DD/MM/AAAA — Ejemplo: 15/06/2025</i>"
    )
    await callback.answer()


@router.message(NuevaCitaStates.SELECT_OFICINA)
async def msg_oficina(message: Message, state: FSMContext):
    await state.update_data(oficina_name=message.text, oficina_code="custom")
    await state.set_state(NuevaCitaStates.SELECT_DATE_FROM)
    await message.answer("📅 <b>Paso 4/6 — Fecha de inicio (DD/MM/AAAA):</b>")


# ── Date from ──────────────────────────────────────────────────
@router.message(NuevaCitaStates.SELECT_DATE_FROM)
async def msg_date_from(message: Message, state: FSMContext):
    try:
        d = datetime.strptime(message.text.strip(), "%d/%m/%Y").date()
        if d < date.today():
            raise ValueError("past date")
    except ValueError:
        await message.answer("❌ Fecha no válida. Usa el formato DD/MM/AAAA y una fecha futura.\n<i>Ejemplo: 20/07/2025</i>")
        return
    await state.update_data(date_from=d.isoformat())
    await state.set_state(NuevaCitaStates.SELECT_DATE_TO)
    await message.answer("📅 <b>Fecha de fin (DD/MM/AAAA):</b>")


# ── Date to ────────────────────────────────────────────────────
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
        "Escribe tu número (o varios separados por comas):\n"
        "<i>Ejemplo: +34600000001</i>",
        reply_markup=skip_keyboard("phones")
    )


# ── Phones ─────────────────────────────────────────────────────
@router.callback_query(F.data == "skip|phones")
async def cb_skip_phones(callback: CallbackQuery, state: FSMContext):
    await state.update_data(phones=[])
    await state.set_state(NuevaCitaStates.ADD_EMAILS)
    await callback.message.edit_text(
        "📧 <b>Email(s):</b>\n\nEscribe tu email (o varios separados por comas):",
        reply_markup=skip_keyboard("emails")
    )
    await callback.answer()


@router.message(NuevaCitaStates.ADD_PHONES)
async def msg_phones(message: Message, state: FSMContext):
    phones = [p.strip() for p in message.text.split(",") if p.strip()]
    await state.update_data(phones=phones)
    await state.set_state(NuevaCitaStates.ADD_EMAILS)
    await message.answer(
        "📧 <b>Email(s):</b>\n\nEscribe tu email (o varios separados por comas):",
        reply_markup=skip_keyboard("emails")
    )


# ── Emails ─────────────────────────────────────────────────────
@router.callback_query(F.data == "skip|emails")
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


# ── Confirm ────────────────────────────────────────────────────
@router.callback_query(NuevaCitaStates.CONFIRM, F.data == "confirm|yes")
async def cb_confirm(callback: CallbackQuery, state: FSMContext, user: User, db: AsyncSession):
    data = await state.get_data()
    await state.clear()

    if db:
        profile = Profile(
            user_id=user.id,
            name=f"{data['province_name']} — {data['tramite_name'][:50]}",
            province_code=data["province_code"],
            province_name=data["province_name"],
            tramite_code=data["tramite_code"],
            tramite_name=data["tramite_name"],
            oficina_code=data.get("oficina_code"),
            oficina_name=data.get("oficina_name", "Cualquiera"),
            date_from=date.fromisoformat(data["date_from"]),
            date_to=date.fromisoformat(data["date_to"]),
            phones=data.get("phones", []),
            emails=data.get("emails", []),
            certificates=[],
            is_active=True,
        )
        db.add(profile)
        await db.commit()

    await callback.message.edit_text(
        "✅ <b>¡Monitoreo activado!</b>\n\n"
        f"🗺 Provincia: <b>{data['province_name']}</b>\n"
        f"📄 Trámite: <b>{data['tramite_name'][:60]}</b>\n"
        f"📅 Rango: {data['date_from']} → {data['date_to']}\n\n"
        "🔔 Te notificaré en cuanto detecte disponibilidad.\n"
        "Usa /mis_citas para ver el estado."
    )
    await callback.answer("¡Monitoreo iniciado!")


@router.callback_query(NuevaCitaStates.CONFIRM, F.data == "confirm|cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Cancelado. Usa /nueva_cita para empezar de nuevo.")
    await callback.answer()


@router.callback_query(NuevaCitaStates.CONFIRM, F.data.startswith("edit|"))
async def cb_edit_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split("|")[1]
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
