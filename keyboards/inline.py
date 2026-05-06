"""Keyboard builders for CitaMonitor bot."""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.icp_data import PROVINCES, TRAMITES


def province_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, name in PROVINCES[:24]:
        builder.button(text=name, callback_data=f"prov|{code}|{name[:20]}")
    builder.button(text="📍 Más provincias ▶", callback_data="prov_more|1")
    builder.adjust(2)
    return builder.as_markup()


def province_keyboard_page(page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    start = page * 24
    end = start + 24
    chunk = PROVINCES[start:end]
    for code, name in chunk:
        builder.button(text=name, callback_data=f"prov|{code}|{name[:20]}")
    if end < len(PROVINCES):
        builder.button(text="▶ Más", callback_data=f"prov_more|{page+1}")
    builder.button(text="◀ Anterior", callback_data=f"prov_more|{page-1}" if page > 0 else "noop")
    builder.adjust(2)
    return builder.as_markup()


def tramite_keyboard(province_code: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category, items in TRAMITES:
        for code, name in items:
            short_name = name[:38] + ".." if len(name) > 38 else name
            builder.button(
                text=short_name,
                callback_data=f"tram|{code}|{name[:30]}"
            )
    builder.adjust(1)
    return builder.as_markup()


def confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Confirmar y Activar", callback_data="confirm|yes")
    builder.button(text="✏️ Editar Provincia",    callback_data="edit|province")
    builder.button(text="✏️ Editar Trámite",      callback_data="edit|tramite")
    builder.button(text="✏️ Editar Oficina",      callback_data="edit|oficina")
    builder.button(text="✏️ Editar Fechas",       callback_data="edit|dates")
    builder.button(text="✏️ Editar Teléfonos",    callback_data="edit|phones")
    builder.button(text="✏️ Editar Emails",       callback_data="edit|emails")
    builder.button(text="❌ Cancelar",             callback_data="confirm|cancel")
    builder.adjust(1)
    return builder.as_markup()


def profile_list_keyboard(profiles: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in profiles:
        status = "🟢" if p.get("is_active") else "🔴"
        builder.button(
            text=f"{status} {p['province_name']} — {p['tramite_name'][:25]}",
            callback_data=f"profile|{p['id']}"
        )
    builder.button(text="➕ Nueva cita", callback_data="nueva_cita")
    builder.adjust(1)
    return builder.as_markup()


def profile_action_keyboard(profile_id: int, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if is_active:
        builder.button(text="⏹ Detener", callback_data=f"pact|{profile_id}|stop")
    else:
        builder.button(text="▶️ Activar", callback_data=f"pact|{profile_id}|start")
    builder.button(text="✏️ Editar",   callback_data=f"pact|{profile_id}|edit")
    builder.button(text="🗑 Eliminar", callback_data=f"pact|{profile_id}|delete")
    builder.button(text="◀️ Volver",  callback_data="pact|back")
    builder.adjust(2)
    return builder.as_markup()


def skip_keyboard(step: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Omitir", callback_data=f"skip|{step}")
    return builder.as_markup()
