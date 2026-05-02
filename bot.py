"""
MiCitaBot (@mecita_bot)
Complete Telegram bot with:
- Admin approval system
- Province/Tramite selection
- User details collection
- Auto appointment booking via Playwright
"""

import logging
import asyncio
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from config import BOT_TOKEN, ADMIN_IDS
from database import db
from data import PROVINCIA_DATA
from booking import book_appointment

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ─── Conversation States ───────────────────────────────────────────────────────
(
    SELECT_PROVINCE,
    SELECT_TRAMITE,
    ENTER_NOMBRE,
    ENTER_APELLIDO,
    ENTER_NIE,
    ENTER_FECHA_NAC,
    ENTER_NACIONALIDAD,
    ENTER_EMAIL,
    ENTER_TELEFONO,
    CONFIRM_BOOKING,
) = range(10)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_province_keyboard(page=0):
    """Build inline keyboard grid for provinces (3 columns, paginated)"""
    provinces = sorted(PROVINCIA_DATA.items(), key=lambda x: x[1]["name"])
    per_page = 18
    start = page * per_page
    chunk = provinces[start:start + per_page]

    buttons = []
    row = []
    for i, (pid, pdata) in enumerate(chunk):
        row.append(InlineKeyboardButton(
            pdata["name"],
            callback_data=f"prov_{pid}"
        ))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Navigation row
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Anterior", callback_data=f"provpage_{page-1}"))
    total_pages = (len(provinces) + per_page - 1) // per_page
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if start + per_page < len(provinces):
        nav.append(InlineKeyboardButton("Siguiente ▶️", callback_data=f"provpage_{page+1}"))
    buttons.append(nav)
    buttons.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel")])

    return InlineKeyboardMarkup(buttons)


def get_tramite_keyboard(province_id):
    """Build inline keyboard for tramites of a province"""
    tramites = PROVINCIA_DATA[province_id]["tramites"]
    buttons = []
    for tid, tname in tramites.items():
        short = tname.replace("POLICIA - ", "")
        buttons.append([InlineKeyboardButton(short, callback_data=f"tram_{province_id}_{tid}")])
    buttons.append([InlineKeyboardButton("◀️ Volver", callback_data="back_provinces")])
    buttons.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)


def get_oficina_keyboard(province_id, tramite_id):
    """Build inline keyboard for offices"""
    oficinas = PROVINCIA_DATA[province_id]["oficinas"]
    buttons = []
    for i, oficina in enumerate(oficinas):
        # Shorten for button display
        short = oficina.replace("CNP - COMISARIA ", "").replace("CNP - ", "")
        buttons.append([InlineKeyboardButton(
            f"🏢 {short[:45]}",
            callback_data=f"ofic_{province_id}_{tramite_id}_{i}"
        )])
    buttons.append([InlineKeyboardButton("◀️ Volver", callback_data=f"prov_{province_id}")])
    buttons.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)


def summary_text(data: dict) -> str:
    """Format user data as a readable summary"""
    prov = PROVINCIA_DATA[data["province_id"]]["name"]
    tram = PROVINCIA_DATA[data["province_id"]]["tramites"][data["tramite_id"]]
    ofic = PROVINCIA_DATA[data["province_id"]]["oficinas"][data["oficina_idx"]]
    tram_short = tram.replace("POLICIA - ", "")

    return (
        f"📋 *RESUMEN DE CITA*\n\n"
        f"🗺️ *Provincia:* {prov}\n"
        f"📌 *Trámite:* {tram_short}\n"
        f"🏢 *Oficina:* {ofic}\n\n"
        f"👤 *Nombre:* {data['nombre']} {data['apellido']}\n"
        f"🪪 *NIE/Pasaporte:* `{data['nie']}`\n"
        f"🎂 *Fecha Nacimiento:* {data['fecha_nac']}\n"
        f"🌍 *Nacionalidad:* {data['nacionalidad']}\n"
        f"📧 *Email:* {data['email']}\n"
        f"📞 *Teléfono:* {data['telefono']}\n"
    )


# ─── Access Control ────────────────────────────────────────────────────────────

async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Returns True if user is approved"""
    user_id = update.effective_user.id
    if user_id in ADMIN_IDS:
        return True
    status = db.get_user_status(user_id)
    if status == "approved":
        return True
    return False


# ─── /start ───────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # Always save/update user info
    db.save_user(user_id, user.first_name, user.last_name or "", user.username or "")

    # Admin
    if user_id in ADMIN_IDS:
        await update.message.reply_text(
            f"👑 *Bienvenido Admin {user.first_name}!*\n\n"
            f"Bot está activo. Usa /pending para ver solicitudes pendientes.",
            parse_mode="Markdown"
        )
        return

    status = db.get_user_status(user_id)

    if status == "approved":
        await update.message.reply_text(
            f"¡Hola *{user.first_name}*! 👋\n\n"
            f"Bienvenido a *MiCitaBot*.\n"
            f"Usa /cita para pedir una cita de extranjería.",
            parse_mode="Markdown"
        )

    elif status == "pending":
        await update.message.reply_text(
            "⏳ Tu solicitud de acceso está *pendiente*.\n\n"
            "El administrador la revisará pronto. Recibirás una notificación cuando sea aprobada.",
            parse_mode="Markdown"
        )

    elif status == "rejected":
        await update.message.reply_text(
            "❌ Tu solicitud ha sido *rechazada*.\n\n"
            "Contacta al administrador si crees que es un error.",
            parse_mode="Markdown"
        )

    else:
        # New user — send access request
        db.set_user_status(user_id, "pending")

        # Notify all admins
        for admin_id in ADMIN_IDS:
            try:
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(f"✅ Aprobar", callback_data=f"approve_{user_id}"),
                        InlineKeyboardButton(f"❌ Rechazar", callback_data=f"reject_{user_id}"),
                    ]
                ])
                name = f"{user.first_name} {user.last_name or ''}".strip()
                username = f"@{user.username}" if user.username else "sin username"
                await context.bot.send_message(
                    admin_id,
                    f"🔔 *Nueva solicitud de acceso*\n\n"
                    f"👤 Nombre: *{name}*\n"
                    f"🆔 Username: {username}\n"
                    f"🔢 User ID: `{user_id}`",
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Could not notify admin {admin_id}: {e}")

        await update.message.reply_text(
            "🔔 *Solicitud enviada*\n\n"
            "Tu solicitud de acceso ha sido enviada al administrador.\n"
            "Te notificaremos cuando sea aprobada. ⏳",
            parse_mode="Markdown"
        )


# ─── Admin: Approve / Reject ───────────────────────────────────────────────────

async def handle_admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admin_id = query.from_user.id

    if admin_id not in ADMIN_IDS:
        await query.answer("No tienes permisos.", show_alert=True)
        return

    data = query.data
    if data.startswith("approve_"):
        target_id = int(data.split("_")[1])
        db.set_user_status(target_id, "approved")

        # Edit admin message
        await query.edit_message_text(
            query.message.text + "\n\n✅ *APROBADO*",
            parse_mode="Markdown"
        )

        # Notify user
        try:
            await context.bot.send_message(
                target_id,
                "✅ *¡Acceso aprobado!*\n\n"
                "Ya puedes usar el bot. Escribe /cita para pedir tu cita. 🎉",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Could not notify user {target_id}: {e}")

    elif data.startswith("reject_"):
        target_id = int(data.split("_")[1])
        db.set_user_status(target_id, "rejected")

        await query.edit_message_text(
            query.message.text + "\n\n❌ *RECHAZADO*",
            parse_mode="Markdown"
        )

        try:
            await context.bot.send_message(
                target_id,
                "❌ *Solicitud rechazada*\n\n"
                "Tu solicitud de acceso ha sido rechazada.\n"
                "Contacta al administrador para más información.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Could not notify user {target_id}: {e}")


# ─── Admin: /pending ──────────────────────────────────────────────────────────

async def pending_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    users = db.get_pending_users()
    if not users:
        await update.message.reply_text("✅ No hay solicitudes pendientes.")
        return

    for u in users:
        uid, fname, lname, username = u["user_id"], u["first_name"], u["last_name"], u["username"]
        name = f"{fname} {lname}".strip()
        uname = f"@{username}" if username else "sin username"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Aprobar", callback_data=f"approve_{uid}"),
            InlineKeyboardButton("❌ Rechazar", callback_data=f"reject_{uid}"),
        ]])
        await update.message.reply_text(
            f"👤 *{name}*\n{uname}\nID: `{uid}`",
            parse_mode="Markdown",
            reply_markup=keyboard
        )


# ─── Admin: /users ────────────────────────────────────────────────────────────

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    users = db.get_all_users()
    if not users:
        await update.message.reply_text("No hay usuarios registrados.")
        return
    lines = ["📋 *Todos los usuarios:*\n"]
    for u in users:
        status_emoji = {"approved": "✅", "pending": "⏳", "rejected": "❌"}.get(u["status"], "❓")
        name = f"{u['first_name']} {u['last_name']}".strip()
        lines.append(f"{status_emoji} {name} — @{u['username'] or 'N/A'} (`{u['user_id']}`)")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ─── /cita Flow ───────────────────────────────────────────────────────────────

async def cita_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context):
        await update.message.reply_text(
            "⛔ No tienes acceso. Usa /start para solicitar acceso.",
        )
        return ConversationHandler.END

    context.user_data.clear()
    await update.message.reply_text(
        "🗺️ *Selecciona la provincia:*",
        parse_mode="Markdown",
        reply_markup=get_province_keyboard(0)
    )
    return SELECT_PROVINCE


async def province_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = int(query.data.split("_")[1])
    await query.edit_message_reply_markup(get_province_keyboard(page))
    return SELECT_PROVINCE


async def province_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    province_id = query.data.split("_")[1]
    context.user_data["province_id"] = province_id
    pname = PROVINCIA_DATA[province_id]["name"]

    await query.edit_message_text(
        f"🗺️ *{pname}*\n\n📋 Selecciona el trámite:",
        parse_mode="Markdown",
        reply_markup=get_tramite_keyboard(province_id)
    )
    return SELECT_TRAMITE


async def back_to_provinces(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🗺️ *Selecciona la provincia:*",
        parse_mode="Markdown",
        reply_markup=get_province_keyboard(0)
    )
    return SELECT_PROVINCE


async def tramite_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, province_id, tramite_id = query.data.split("_", 2)
    context.user_data["tramite_id"] = tramite_id
    pname = PROVINCIA_DATA[province_id]["name"]
    tname = PROVINCIA_DATA[province_id]["tramites"][tramite_id].replace("POLICIA - ", "")

    await query.edit_message_text(
        f"🗺️ *{pname}* → 📋 *{tname}*\n\n🏢 Selecciona la oficina:",
        parse_mode="Markdown",
        reply_markup=get_oficina_keyboard(province_id, tramite_id)
    )
    return SELECT_TRAMITE


async def oficina_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    province_id = parts[1]
    tramite_id = parts[2]
    oficina_idx = int(parts[3])

    context.user_data["province_id"] = province_id
    context.user_data["tramite_id"] = tramite_id
    context.user_data["oficina_idx"] = oficina_idx

    await query.edit_message_text(
        "👤 *Introduce tus datos personales*\n\n"
        "Primero, escribe tu *nombre* (solo el nombre, sin apellidos):",
        parse_mode="Markdown"
    )
    return ENTER_NOMBRE


# ─── User Details Steps ────────────────────────────────────────────────────────

async def enter_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nombre"] = update.message.text.strip()
    await update.message.reply_text("📝 Ahora escribe tu *apellido/s*:", parse_mode="Markdown")
    return ENTER_APELLIDO


async def enter_apellido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["apellido"] = update.message.text.strip()
    await update.message.reply_text(
        "🪪 Escribe tu *NIE o número de pasaporte*:\n_(Ejemplo: X1234567A o AB123456)_",
        parse_mode="Markdown"
    )
    return ENTER_NIE


async def enter_nie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nie"] = update.message.text.strip().upper()
    await update.message.reply_text(
        "🎂 Escribe tu *fecha de nacimiento*:\n_(Formato: DD/MM/AAAA, ejemplo: 15/03/1990)_",
        parse_mode="Markdown"
    )
    return ENTER_FECHA_NAC


async def enter_fecha_nac(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    # Basic validation
    import re
    if not re.match(r"^\d{2}/\d{2}/\d{4}$", text):
        await update.message.reply_text(
            "⚠️ Formato incorrecto. Usa DD/MM/AAAA\n_(Ejemplo: 15/03/1990)_",
            parse_mode="Markdown"
        )
        return ENTER_FECHA_NAC
    context.user_data["fecha_nac"] = text
    await update.message.reply_text(
        "🌍 Escribe tu *nacionalidad*:\n_(Ejemplo: Pakistaní, Marroquí, Colombiano...)_",
        parse_mode="Markdown"
    )
    return ENTER_NACIONALIDAD


async def enter_nacionalidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nacionalidad"] = update.message.text.strip()
    await update.message.reply_text(
        "📧 Escribe tu *correo electrónico*:",
        parse_mode="Markdown"
    )
    return ENTER_EMAIL


async def enter_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import re
    email = update.message.text.strip()
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        await update.message.reply_text("⚠️ Email inválido. Escribe un email correcto:")
        return ENTER_EMAIL
    context.user_data["email"] = email
    await update.message.reply_text(
        "📞 Escribe tu *número de teléfono* (con prefijo):\n_(Ejemplo: +34612345678)_",
        parse_mode="Markdown"
    )
    return ENTER_TELEFONO


async def enter_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["telefono"] = update.message.text.strip()

    # Show summary + confirm
    summary = summary_text(context.user_data)
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirmar y Reservar", callback_data="confirm_booking"),
            InlineKeyboardButton("✏️ Editar", callback_data="edit_data"),
        ],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
    ])
    await update.message.reply_text(
        summary + "\n¿Los datos son correctos?",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    return CONFIRM_BOOKING


# ─── Confirm & Book ────────────────────────────────────────────────────────────

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = context.user_data.copy()
    user_id = query.from_user.id
    user_name = query.from_user.first_name

    await query.edit_message_text(
        "⏳ *Procesando tu cita...*\n\n"
        "Estoy accediendo a la web del gobierno. Por favor espera 1-2 minutos. 🤖",
        parse_mode="Markdown"
    )

    # Save booking request to DB
    booking_id = db.save_booking(user_id, data)

    # Notify admin
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"🔔 *Nueva solicitud de cita*\n\n"
                f"👤 Usuario: {user_name} (`{user_id}`)\n"
                f"🆔 Booking ID: `{booking_id}`\n\n"
                + summary_text(data),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Admin notify error: {e}")

    # Run booking in background
    asyncio.create_task(
        run_booking(context.bot, query.message.chat_id, user_id, booking_id, data)
    )

    return ConversationHandler.END


async def run_booking(bot, chat_id, user_id, booking_id, data):
    """Background task: run Playwright booking"""
    try:
        result = await book_appointment(data)

        if result["success"]:
            db.update_booking_status(booking_id, "completed", result.get("confirmation", ""))
            msg = (
                f"✅ *¡Cita reservada con éxito!*\n\n"
                f"📅 *Fecha:* {result.get('fecha', 'Ver email')}\n"
                f"🕐 *Hora:* {result.get('hora', 'Ver email')}\n"
                f"🏢 *Oficina:* {result.get('oficina', data['oficina_idx'])}\n"
                f"📧 Recibirás confirmación en: {data['email']}\n\n"
                f"🔢 *Ref:* `{result.get('confirmation', booking_id)}`"
            )
            # Notify admins too
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(
                        admin_id,
                        f"✅ Cita completada — Booking `{booking_id}`\n"
                        f"Ref: {result.get('confirmation', '')}",
                        parse_mode="Markdown"
                    )
                except:
                    pass
        else:
            db.update_booking_status(booking_id, "failed", result.get("error", ""))
            msg = (
                f"⚠️ *No se pudo reservar automáticamente*\n\n"
                f"*Motivo:* {result.get('error', 'No hay citas disponibles en este momento')}\n\n"
                f"💡 Puedes intentarlo manualmente en:\n"
                f"[icp.administracionelectronica.gob.es](https://icp.administracionelectronica.gob.es/icpplustieb/index.html)\n\n"
                f"Tus datos han sido guardados (Ref: `{booking_id}`). "
                f"Puedes reintentarlo con /reintentar"
            )

        await bot.send_message(chat_id, msg, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Booking error: {e}")
        db.update_booking_status(booking_id, "error", str(e))
        await bot.send_message(
            chat_id,
            f"❌ *Error inesperado*\n\n`{str(e)[:200]}`\n\n"
            f"Contacta al administrador con ref: `{booking_id}`",
            parse_mode="Markdown"
        )


async def edit_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✏️ Vamos a empezar de nuevo.\n\nEscribe tu *nombre*:",
        parse_mode="Markdown"
    )
    return ENTER_NOMBRE


# ─── /reintentar ─────────────────────────────────────────────────────────────

async def reintentar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context):
        return
    user_id = update.effective_user.id
    last = db.get_last_booking(user_id)
    if not last:
        await update.message.reply_text("No tienes reservas previas. Usa /cita para empezar.")
        return

    msg = await update.message.reply_text(
        f"🔄 Reintentando tu última cita...\n\n{summary_text(last['data'])}",
        parse_mode="Markdown"
    )
    asyncio.create_task(
        run_booking(context.bot, update.message.chat_id, user_id, last["id"], last["data"])
    )


# ─── /help ───────────────────────────────────────────────────────────────────

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_admin = update.effective_user.id in ADMIN_IDS
    text = (
        "🤖 *MiCitaBot — Ayuda*\n\n"
        "📋 *Comandos disponibles:*\n"
        "/cita — Pedir nueva cita de extranjería\n"
        "/reintentar — Reintentar última cita fallida\n"
        "/start — Inicio / solicitar acceso\n"
        "/help — Esta ayuda\n"
    )
    if is_admin:
        text += (
            "\n👑 *Comandos de Admin:*\n"
            "/pending — Ver solicitudes pendientes\n"
            "/users — Ver todos los usuarios\n"
        )
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── Cancel ──────────────────────────────────────────────────────────────────

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ Operación cancelada. Usa /cita para empezar de nuevo.")
    else:
        await update.message.reply_text("❌ Operación cancelada. Usa /cita para empezar de nuevo.")
    context.user_data.clear()
    return ConversationHandler.END


async def noop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Admin decision handlers (outside conversation)
    app.add_handler(CallbackQueryHandler(handle_admin_decision, pattern="^(approve|reject)_"))
    app.add_handler(CallbackQueryHandler(noop, pattern="^noop$"))

    # Conversation handler for /cita flow
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("cita", cita_start)],
        states={
            SELECT_PROVINCE: [
                CallbackQueryHandler(province_page, pattern="^provpage_"),
                CallbackQueryHandler(province_selected, pattern="^prov_"),
                CallbackQueryHandler(cancel, pattern="^cancel$"),
            ],
            SELECT_TRAMITE: [
                CallbackQueryHandler(tramite_selected, pattern="^tram_"),
                CallbackQueryHandler(oficina_selected, pattern="^ofic_"),
                CallbackQueryHandler(back_to_provinces, pattern="^back_provinces$"),
                CallbackQueryHandler(province_selected, pattern="^prov_"),
                CallbackQueryHandler(cancel, pattern="^cancel$"),
            ],
            ENTER_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_nombre)],
            ENTER_APELLIDO: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_apellido)],
            ENTER_NIE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_nie)],
            ENTER_FECHA_NAC: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_fecha_nac)],
            ENTER_NACIONALIDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_nacionalidad)],
            ENTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_email)],
            ENTER_TELEFONO: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_telefono)],
            CONFIRM_BOOKING: [
                CallbackQueryHandler(confirm_booking, pattern="^confirm_booking$"),
                CallbackQueryHandler(edit_data, pattern="^edit_data$"),
                CallbackQueryHandler(cancel, pattern="^cancel$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel, pattern="^cancel$"),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("pending", pending_users))
    app.add_handler(CommandHandler("users", list_users))
    app.add_handler(CommandHandler("reintentar", reintentar))

    logger.info("🤖 MiCitaBot started!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
