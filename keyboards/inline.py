"""Keyboard builders for CitaMonitor bot."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Tuple

from services.icp_data import PROVINCES, TRAMITES


def province_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, name in PROVINCES[:25]:  # Show first 25, paginate as needed
        builder.button(text=name, callback_data=f"province:{code}:{name}")
    builder.button(text="📍 Ver más provincias", callback_data="province:more")
    builder.adjust(2)
    return builder.as_markup()


def tramite_keyboard(province_code: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category, items in TRAMITES:
        builder.button(text=f"── {category} ──", callback_data="noop")
        for code, name in items:
            short_name = name[:40] + "..." if len(name) > 40 else name
            builder.button(text=short_name, callback_data=f"tramite:{code}:{name[:50]}")
    builder.adjust(1)
    return builder.as_markup()


def confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Confirmar y Activar", callback_data="confirm:yes")
    builder.button(text="✏️ Editar Provincia", callback_data="edit:province")
    builder.button(text="✏️ Editar Trámite", callback_data="edit:tramite")
    builder.button(text="✏️ Editar Oficina", callback_data="edit:oficina")
    builder.button(text="✏️ Editar Fechas", callback_data="edit:dates")
    builder.button(text="✏️ Editar Teléfonos", callback_data="edit:phones")
    builder.button(text="✏️ Editar Emails", callback_data="edit:emails")
    builder.button(text="❌ Cancelar", callback_data="confirm:cancel")
    builder.adjust(1)
    return builder.as_markup()


def profile_list_keyboard(profiles: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in profiles:
        status = "🟢" if p.get("is_active") else "🔴"
        builder.button(
            text=f"{status} {p['province_name']} — {p['tramite_name'][:30]}",
            callback_data=f"profile:{p['id']}"
        )
    builder.button(text="➕ Nueva cita", callback_data="nueva_cita")
    builder.adjust(1)
    return builder.as_markup()


def profile_action_keyboard(profile_id: int, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if is_active:
        builder.button(text="⏹ Detener", callback_data=f"profile_action:{profile_id}:stop")
    else:
        builder.button(text="▶️ Activar", callback_data=f"profile_action:{profile_id}:start")
    builder.button(text="✏️ Editar", callback_data=f"profile_action:{profile_id}:edit")
    builder.button(text="🗑 Eliminar", callback_data=f"profile_action:{profile_id}:delete")
    builder.button(text="◀️ Volver", callback_data="profile_action:back")
    builder.adjust(2)
    return builder.as_markup()


def skip_keyboard(step: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Omitir", callback_data=f"skip:{step}")
    return builder.as_markup()
