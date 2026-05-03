"""
MiCitaBot v2 — @mecita_bot — FIXED VERSION
"""
import logging, asyncio, os, re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from aiohttp import web

from config import BOT_TOKEN, ADMIN_IDS, WEB_PORT, WEB_HOST
from database import db
from data import PROVINCIA_DATA
from booking import book_appointment

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ─── States ───────────────────────────────────────────────────────────────────
(SELECT_PROVINCE, SELECT_TRAMITE, SELECT_OFFICE,
 DATE_FROM, DATE_TO,
 ENTER_NOMBRE, ENTER_APELLIDO, ENTER_NIE, ENTER_FECHA,
 ENTER_NACIO, ENTER_EMAIL, ENTER_TEL,
 CONFIRM) = range(13)


# ─── Keyboards ────────────────────────────────────────────────────────────────

def province_keyboard(page=0):
    # No pagination — show all 52 provinces at once (scroll to see all)
    provs = sorted(PROVINCIA_DATA.items(), key=lambda x: x[1]["name"])
    rows = []
    row = []
    for pid, pd in provs:
        row.append(InlineKeyboardButton(pd["name"], callback_data=f"PROV|{pid}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("❌ Cancelar", callback_data="CANCEL")])
    return InlineKeyboardMarkup(rows)


def tramite_keyboard(pid):
    tramites = PROVINCIA_DATA[pid]["tramites"]
    rows = []
    for tid, tname in tramites.items():
        short = tname.replace("POLICIA - ", "")
        rows.append([InlineKeyboardButton(short, callback_data=f"TRAM|{pid}|{tid}")])
    rows.append([InlineKeyboardButton("◀️ Volver a Provincias", callback_data="BACK_PROV")])
    rows.append([InlineKeyboardButton("❌ Cancelar", callback_data="CANCEL")])
    return InlineKeyboardMarkup(rows)


def office_keyboard(pid):
    oficinas = PROVINCIA_DATA[pid]["oficinas"]
    rows = []
    # ── ANY OFFICE option at top ──────────────────────────────────────────────
    rows.append([InlineKeyboardButton(
        "🌐 CUALQUIER OFICINA (primera disponible)",
        callback_data=f"OFIC|{pid}|ANY"
    )])
    # ── Individual offices ────────────────────────────────────────────────────
    for i, oname in enumerate(oficinas):
        short = oname.replace("CNP - COMISARIA ", "").replace("CNP - ", "")[:55]
        rows.append([InlineKeyboardButton(f"🏢 {short}", callback_data=f"OFIC|{pid}|{i}")])
    rows.append([InlineKeyboardButton("◀️ Volver a Trámites", callback_data=f"BACK_TRAM|{pid}")])
    rows.append([InlineKeyboardButton("❌ Cancelar", callback_data="CANCEL")])
    return InlineKeyboardMarkup(rows)


def summary_text(d):
    p  = PROVINCIA_DATA[d["province_id"]]
    t  = p["tramites"][d["tramite_id"]].replace("POLICIA - ", "")
    o  = "🌐 Cualquier oficina disponible" if d.get("oficina_idx") == "ANY" else p["oficinas"][int(d["oficina_idx"])]
    df = d.get("date_from", "—")
    dt = d.get("date_to", "—")
    return (
        f"📋 *RESUMEN DE CITA*\n\n"
        f"🗺️ *Provincia:* {p['name']}\n"
        f"📌 *Trámite:* {t}\n"
        f"🏢 *Oficina:* {o}\n"
        f"📅 *Desde:* `{df}`  →  *Hasta:* `{dt}`\n\n"
        f"👤 *Nombre completo:* {d['nombre']}\n"
        f"🪪 *NIE/Pasaporte:* `{d['nie']}`\n"
        f"🎂 *Fecha Nac:* {d['fecha_nac']}\n"
        f"🌍 *Nacionalidad:* {d['nacionalidad']}\n"
        f"📧 *Email:* {d['email']}\n"
        f"📞 *Teléfono:* {d['telefono']}\n"
    )


# ─── /start ───────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.save_user(user.id, user.first_name, user.last_name or "", user.username or "")

    if user.id in ADMIN_IDS:
        await update.message.reply_text(
            f"👑 *Bienvenido Admin {user.first_name}!*\n\n"
            f"*Comandos admin:*\n"
            f"/pending — Solicitudes pendientes\n"
            f"/users — Todos los usuarios\n"
            f"/addcredits — Añadir créditos\n"
            f"/cita — Pedir cita\n"
            f"/miscitas — Ver reservas",
            parse_mode="Markdown")
        return

    status = db.get_user_status(user.id)
    if status == "approved":
        credits = db.get_credits(user.id)
        await update.message.reply_text(
            f"¡Hola *{user.first_name}*! 👋\n\n"
            f"💳 Tus créditos: *{credits}*\n\n"
            f"Usa /cita para pedir una cita.\n"
            f"Usa /miscitas para ver tus reservas.",
            parse_mode="Markdown")
    elif status == "pending":
        await update.message.reply_text(
            "⏳ Tu solicitud está *pendiente*.\nEl admin la revisará pronto.",
            parse_mode="Markdown")
    elif status == "rejected":
        await update.message.reply_text(
            "❌ Tu solicitud fue rechazada.\nContacta al admin.",
            parse_mode="Markdown")
    else:
        db.set_user_status(user.id, "pending")
        name  = f"{user.first_name} {user.last_name or ''}".strip()
        uname = f"@{user.username}" if user.username else "sin username"
        for aid in ADMIN_IDS:
            try:
                await ctx.bot.send_message(
                    aid,
                    f"🔔 *Nueva solicitud de acceso*\n\n"
                    f"👤 {name}\n{uname}\nID: `{user.id}`",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("✅ Aprobar", callback_data=f"APPROVE|{user.id}"),
                        InlineKeyboardButton("❌ Rechazar", callback_data=f"REJECT|{user.id}"),
                    ]]))
            except:
                pass
        await update.message.reply_text(
            "🔔 *Solicitud enviada al admin.*\nTe notificaremos cuando sea aprobada. ⏳",
            parse_mode="Markdown")


# ─── Admin Approve/Reject ─────────────────────────────────────────────────────

async def admin_approve(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.from_user.id not in ADMIN_IDS:
        await q.answer("Sin permisos.", show_alert=True)
        return
    _, uid = q.data.split("|")
    uid = int(uid)
    db.set_user_status(uid, "approved")
    await q.edit_message_text(q.message.text + "\n\n✅ *APROBADO*", parse_mode="Markdown")
    try:
        await ctx.bot.send_message(
            uid,
            "✅ *¡Acceso aprobado!*\n\nYa puedes usar el bot.\nUsa /cita para reservar tu cita. 🎉",
            parse_mode="Markdown")
    except:
        pass


async def admin_reject(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.from_user.id not in ADMIN_IDS:
        return
    _, uid = q.data.split("|")
    uid = int(uid)
    db.set_user_status(uid, "rejected")
    await q.edit_message_text(q.message.text + "\n\n❌ *RECHAZADO*", parse_mode="Markdown")
    try:
        await ctx.bot.send_message(uid, "❌ Tu solicitud fue rechazada.\nContacta al admin.", parse_mode="Markdown")
    except:
        pass


# ─── /addcredits ─────────────────────────────────────────────────────────────

async def add_credits(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    args = ctx.args
    if len(args) < 2:
        await update.message.reply_text(
            "Uso: `/addcredits @username 5`\nO: `/addcredits 123456789 5`",
            parse_mode="Markdown")
        return
    try:
        amount = int(args[1])
        target = args[0].replace("@", "")
        users  = db.get_all_users()
        found  = None
        for u in users:
            if str(u["user_id"]) == target or u.get("username", "") == target:
                found = u
                break
        if not found:
            await update.message.reply_text(f"❌ Usuario `{target}` no encontrado.", parse_mode="Markdown")
            return
        db.add_credits(found["user_id"], amount)
        new_credits = db.get_credits(found["user_id"])
        name = f"{found['first_name']} {found['last_name']}".strip()
        await update.message.reply_text(
            f"✅ *{amount} créditos añadidos* a {name}\n💳 Total: *{new_credits}*",
            parse_mode="Markdown")
        try:
            await ctx.bot.send_message(
                found["user_id"],
                f"💳 *{amount} crédito(s) añadido(s)* a tu cuenta.\n"
                f"Total: *{new_credits}* créditos.\n\nUsa /cita para reservar.",
                parse_mode="Markdown")
        except:
            pass
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# ─── /cita — Conversation ─────────────────────────────────────────────────────

async def cita_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    # Check access
    if uid not in ADMIN_IDS:
        if db.get_user_status(uid) != "approved":
            await update.message.reply_text("⛔ Sin acceso. Usa /start.")
            return ConversationHandler.END
        # Check credits
        if db.get_credits(uid) <= 0:
            await update.message.reply_text(
                "❌ *No tienes créditos.*\nContacta al admin para obtener créditos.",
                parse_mode="Markdown")
            return ConversationHandler.END

    ctx.user_data.clear()
    await update.message.reply_text(
        "🗺️ *Selecciona la provincia:*",
        parse_mode="Markdown",
        reply_markup=province_keyboard(0))
    return SELECT_PROVINCE


# Step 1 — Province
async def cb_provpage(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    page = int(q.data.split("|")[1])
    await q.edit_message_reply_markup(province_keyboard(page))
    return SELECT_PROVINCE

async def cb_province(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    pid = q.data.split("|")[1]
    ctx.user_data["province_id"] = pid
    pname = PROVINCIA_DATA[pid]["name"]
    await q.edit_message_text(
        f"🗺️ *{pname}*\n\n📋 Selecciona el trámite:",
        parse_mode="Markdown",
        reply_markup=tramite_keyboard(pid))
    return SELECT_TRAMITE

async def cb_back_prov(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(
        "🗺️ *Selecciona la provincia:*",
        parse_mode="Markdown",
        reply_markup=province_keyboard(0))
    return SELECT_PROVINCE


# Step 2 — Tramite
async def cb_tramite(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    parts = q.data.split("|")   # TRAM|pid|tid
    pid = parts[1]
    tid = parts[2]
    ctx.user_data["province_id"] = pid
    ctx.user_data["tramite_id"]  = tid
    pname = PROVINCIA_DATA[pid]["name"]
    tname = PROVINCIA_DATA[pid]["tramites"][tid].replace("POLICIA - ", "")
    await q.edit_message_text(
        f"🗺️ *{pname}* → 📌 *{tname}*\n\n🏢 Selecciona la oficina:",
        parse_mode="Markdown",
        reply_markup=office_keyboard(pid))
    return SELECT_OFFICE

async def cb_back_tram(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    pid = q.data.split("|")[1]
    pname = PROVINCIA_DATA[pid]["name"]
    await q.edit_message_text(
        f"🗺️ *{pname}*\n\n📋 Selecciona el trámite:",
        parse_mode="Markdown",
        reply_markup=tramite_keyboard(pid))
    return SELECT_TRAMITE


# Step 3 — Office
async def cb_office(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    parts = q.data.split("|")   # OFIC|pid|idx or OFIC|pid|ANY
    pid = parts[1]
    idx = parts[2]  # string: number or "ANY"
    ctx.user_data["province_id"] = pid
    ctx.user_data["oficina_idx"] = idx

    if idx == "ANY":
        oname = "🌐 Cualquier oficina disponible"
    else:
        oname = PROVINCIA_DATA[pid]["oficinas"][int(idx)]

    pname = PROVINCIA_DATA[pid]["name"]
    tname = PROVINCIA_DATA[pid]["tramites"][ctx.user_data["tramite_id"]].replace("POLICIA - ", "")

    # Build web form URL with pre-filled params
    import os
    base_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
    if base_url:
        form_url = f"https://{base_url}/?pid={pid}&tid={ctx.user_data['tramite_id']}&oidx={idx}&uid={q.from_user.id}"
    else:
        form_url = f"http://localhost:8080/?pid={pid}&tid={ctx.user_data['tramite_id']}&oidx={idx}&uid={q.from_user.id}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Abrir Formulario Web", url=form_url)],
        [InlineKeyboardButton("✏️ Continuar en Bot (sin form)", callback_data="CONTINUE_IN_BOT")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="CANCEL")],
    ])

    await q.edit_message_text(
        f"✅ *Selección completa:*\n\n"
        f"🗺️ *Provincia:* {pname}\n"
        f"📌 *Trámite:* {tname}\n"
        f"🏢 *Oficina:* {oname}\n\n"
        f"Elige cómo quieres rellenar tus datos:",
        parse_mode="Markdown",
        reply_markup=keyboard)
    return SELECT_OFFICE



async def cb_continue_in_bot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(
        "📅 Escribe la *fecha desde* (YYYY-MM-DD):\n_(Ej: 2025-06-01)_",
        parse_mode="Markdown")
    return DATE_FROM


# Steps 4-5 — Date Range
async def enter_date_from(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        await update.message.reply_text(
            "⚠️ Formato incorrecto.\nEscribe: YYYY-MM-DD\n_(Ej: 2025-06-01)_",
            parse_mode="Markdown")
        return DATE_FROM
    ctx.user_data["date_from"] = text
    await update.message.reply_text(
        f"✅ Fecha desde: `{text}`\n\n"
        f"📅 Ahora escribe la *fecha hasta* (YYYY-MM-DD):\n"
        f"_(Ej: 2025-07-31)_",
        parse_mode="Markdown")
    return DATE_TO

async def enter_date_to(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        await update.message.reply_text(
            "⚠️ Formato incorrecto.\nEscribe: YYYY-MM-DD\n_(Ej: 2025-07-31)_",
            parse_mode="Markdown")
        return DATE_TO
    if text < ctx.user_data.get("date_from", ""):
        await update.message.reply_text("⚠️ La fecha hasta debe ser después de la fecha desde.")
        return DATE_TO
    ctx.user_data["date_to"] = text
    await update.message.reply_text(
        f"✅ Rango: `{ctx.user_data['date_from']}` → `{text}`\n\n"
        f"👤 Escribe tu *nombre*:",
        parse_mode="Markdown")
    return ENTER_NOMBRE


# Steps 6-12 — Personal Data
async def e_nombre(u, c):
    c.user_data["nombre"] = u.message.text.strip()
    c.user_data["apellido"] = ""
    await u.message.reply_text("🪪 Escribe tu *NIE o número de pasaporte*:", parse_mode="Markdown")
    return ENTER_NIE

async def e_apellido(u, c):
    c.user_data["apellido"] = u.message.text.strip()
    await u.message.reply_text("🪪 Escribe tu *NIE o número de pasaporte*:", parse_mode="Markdown")
    return ENTER_NIE

async def e_nie(u, c):
    c.user_data["nie"] = u.message.text.strip().upper()
    await u.message.reply_text(
        "🎂 Escribe tu *fecha de nacimiento* (YYYY-MM-DD):\n_(Ej: 1990-05-15)_",
        parse_mode="Markdown")
    return ENTER_FECHA

async def e_fecha(u, c):
    text = u.message.text.strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        await u.message.reply_text("⚠️ Formato: YYYY-MM-DD\n_(Ej: 1990-05-15)_", parse_mode="Markdown")
        return ENTER_FECHA
    c.user_data["fecha_nac"] = text
    await u.message.reply_text("🌍 Escribe tu *nacionalidad*:", parse_mode="Markdown")
    return ENTER_NACIO

async def e_nacio(u, c):
    c.user_data["nacionalidad"] = u.message.text.strip()
    await u.message.reply_text("📧 Escribe tu *email*:", parse_mode="Markdown")
    return ENTER_EMAIL

async def e_email(u, c):
    email = u.message.text.strip()
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        await u.message.reply_text("⚠️ Email inválido. Escribe un email correcto:")
        return ENTER_EMAIL
    c.user_data["email"] = email
    await u.message.reply_text(
        "📞 Escribe tu *teléfono* (con prefijo):\n_(Ej: +34612345678)_",
        parse_mode="Markdown")
    return ENTER_TEL

async def e_tel(u, c):
    c.user_data["telefono"]   = u.message.text.strip()
    c.user_data["telegram_id"] = str(u.effective_user.id)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Confirmar y Reservar", callback_data="CONFIRM"),
        InlineKeyboardButton("✏️ Editar", callback_data="EDIT"),
    ], [InlineKeyboardButton("❌ Cancelar", callback_data="CANCEL")]])
    await u.message.reply_text(
        summary_text(c.user_data) + "\n¿Los datos son correctos?",
        parse_mode="Markdown",
        reply_markup=kb)
    return CONFIRM


# Step 13 — Confirm
async def cb_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid  = q.from_user.id
    data = ctx.user_data.copy()

    # Deduct credit
    if uid not in ADMIN_IDS:
        db.deduct_credit(uid)
        remaining = db.get_credits(uid)
    else:
        remaining = "∞ (Admin)"

    bid = db.save_booking(uid, data, data.get("date_from", ""), data.get("date_to", ""))
    data["booking_id"] = bid

    await q.edit_message_text(
        f"🎯 *¡Solicitud registrada!*\n\n"
        f"🆔 Booking ID: `{bid}`\n"
        f"💳 Créditos restantes: *{remaining}*\n\n"
        f"🤖 El bot buscará cita *24/7* en tu rango de fechas.\n"
        f"📲 Te notificaremos aquí cuando encuentre una cita.\n"
        f"📄 También recibirás el PDF de confirmación.",
        parse_mode="Markdown")

    # Notify admins
    for aid in ADMIN_IDS:
        try:
            await ctx.bot.send_message(
                aid,
                f"🔔 *Nueva solicitud de cita*\n"
                f"👤 {q.from_user.first_name} (`{uid}`)\n"
                f"🆔 `{bid}`\n\n" + summary_text(data),
                parse_mode="Markdown")
        except:
            pass

    ctx.user_data.clear()
    return ConversationHandler.END

async def cb_edit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.edit_message_text("✏️ Escribe tu *nombre* de nuevo:", parse_mode="Markdown")
    return ENTER_NOMBRE


# ─── Cancel / Noop ────────────────────────────────────────────────────────────

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ Cancelado. Usa /cita para empezar de nuevo.")
    else:
        await update.message.reply_text("❌ Cancelado. Usa /cita para empezar de nuevo.")
    ctx.user_data.clear()
    return ConversationHandler.END

async def noop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()


# ─── OTP Handler ──────────────────────────────────────────────────────────────

async def otp_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if re.match(r"^\d{4,8}$", text):
        uid  = update.effective_user.id
        last = db.get_last_booking(uid)
        if last and last["status"] in ["queued", "retrying"]:
            db.save_otp(last["id"], text)
            await update.message.reply_text(
                "✅ *Código OTP recibido.* Procesando...",
                parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ No hay reserva activa esperando OTP.")


# ─── /miscitas ────────────────────────────────────────────────────────────────

async def mis_citas(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS and db.get_user_status(uid) != "approved":
        return
    bookings = db.get_user_bookings(uid)
    if not bookings:
        await update.message.reply_text("No tienes reservas. Usa /cita para empezar.")
        return
    status_map = {
        "queued":    "⏳ Buscando",
        "retrying":  "🔄 Reintentando",
        "completed": "✅ Completada",
        "failed":    "❌ Fallida",
        "error":     "⚠️ Error"
    }
    lines = ["📋 *Tus últimas reservas:*\n"]
    for b in bookings:
        st = status_map.get(b["status"], b["status"])
        lines.append(f"{st} — `{b['id']}` — {b['created_at'][:10]}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ─── /pending /users ──────────────────────────────────────────────────────────

async def pending_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    users = db.get_pending_users()
    if not users:
        await update.message.reply_text("✅ No hay solicitudes pendientes.")
        return
    for u in users:
        name = f"{u['first_name']} {u['last_name']}".strip()
        await update.message.reply_text(
            f"👤 *{name}*\n@{u['username'] or 'N/A'}\nID: `{u['user_id']}`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Aprobar", callback_data=f"APPROVE|{u['user_id']}"),
                InlineKeyboardButton("❌ Rechazar", callback_data=f"REJECT|{u['user_id']}"),
            ]]))

async def list_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    users = db.get_all_users()
    em = {"approved": "✅", "pending": "⏳", "rejected": "❌", "new": "🆕"}
    lines = ["👥 *Todos los usuarios:*\n"]
    for u in users:
        c = db.get_credits(u["user_id"])
        lines.append(f"{em.get(u['status'], '❓')} {u['first_name']} `{u['user_id']}` 💳{c}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ─── /help ───────────────────────────────────────────────────────────────────

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    is_admin = update.effective_user.id in ADMIN_IDS
    text = (
        "🤖 *MiCitaBot — Ayuda*\n\n"
        "/start — Inicio / solicitar acceso\n"
        "/cita — Pedir nueva cita\n"
        "/miscitas — Ver mis reservas\n"
        "/help — Esta ayuda\n"
    )
    if is_admin:
        text += (
            "\n👑 *Admin:*\n"
            "/pending — Solicitudes pendientes\n"
            "/users — Todos los usuarios\n"
            "/addcredits @user N — Añadir créditos\n"
        )
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── 24/7 Booking Worker ─────────────────────────────────────────────────────

async def booking_worker(bot):
    logger.info("🤖 24/7 Booking worker started")
    while True:
        try:
            bookings = db.get_queued_bookings()
            for b in bookings:
                bid  = b["id"]
                uid  = b["user_id"]
                data = b["data"]
                data["booking_id"] = bid
                data["date_from"]  = b.get("date_from", "")
                data["date_to"]    = b.get("date_to", "")

                logger.info(f"Worker: booking {bid} attempt {b['attempts']+1}")
                db.update_booking(bid, "retrying")
                db.increment_attempts(bid)

                result = await book_appointment(data, bot=bot, db=db)

                if result["success"]:
                    pdf_path = result.get("pdf_path", "")
                    db.update_booking(bid, "completed", result.get("confirmation", ""), pdf_path)

                    msg = (
                        f"🎉 *¡Cita reservada con éxito!*\n\n"
                        f"📅 *Fecha:* {result.get('fecha', '—')}\n"
                        f"🕐 *Hora:* {result.get('hora', '—')}\n"
                        f"🏢 *Oficina:* {result.get('oficina', '—')}\n"
                        f"🔢 *Confirmación:* `{result.get('confirmation', '—')}`\n\n"
                        f"📧 Confirmar en email: {data.get('email', '')}"
                    )
                    try:
                        await bot.send_message(uid, msg, parse_mode="Markdown")
                    except:
                        pass

                    # Send PDF
                    if pdf_path and os.path.exists(pdf_path):
                        try:
                            with open(pdf_path, "rb") as f:
                                await bot.send_document(
                                    uid, f,
                                    filename=f"cita_{bid}.pdf",
                                    caption="📄 *PDF de confirmación de tu cita*",
                                    parse_mode="Markdown")
                        except Exception as e:
                            logger.error(f"PDF send error: {e}")

                    # Notify admin
                    for aid in ADMIN_IDS:
                        try:
                            await bot.send_message(
                                aid,
                                f"✅ *Cita completada*\nBooking: `{bid}`\n"
                                f"Ref: {result.get('confirmation', '')}",
                                parse_mode="Markdown")
                        except:
                            pass
                else:
                    error = result.get("error", "")
                    permanent = ["rechazado", "bloqueado", "datos incorrectos"]
                    if any(p in error.lower() for p in permanent):
                        db.update_booking(bid, "failed", error)
                        try:
                            await bot.send_message(
                                uid,
                                f"❌ *Error permanente*\n{error}\n\nContacta al admin.",
                                parse_mode="Markdown")
                        except:
                            pass
                    else:
                        db.update_booking(bid, "queued", error)
                        logger.info(f"Booking {bid} queued for retry: {error}")

        except Exception as e:
            logger.error(f"Worker error: {e}")

        await asyncio.sleep(300)  # 5 min


# ─── Web Server ───────────────────────────────────────────────────────────────

async def form_page(request):
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base_dir, "templates", "form.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    return web.Response(text=html, content_type="text/html")

async def form_submit(request):
    try:
        data = await request.json()
        uid  = int(data.get("telegram_id", 0))

        if uid not in ADMIN_IDS:
            status = db.get_user_status(uid)
            if status != "approved":
                return web.json_response({"success": False, "error": "Usuario no aprobado. Usa /start en el bot."})
            if db.get_credits(uid) <= 0:
                return web.json_response({"success": False, "error": "Sin créditos disponibles. Contacta al admin."})
            db.deduct_credit(uid)

        bid = db.save_booking(uid, data, data.get("date_from", ""), data.get("date_to", ""))
        return web.json_response({"success": True, "booking_id": bid})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)})

def create_web_app():
    app = web.Application()
    app.router.add_get("/", form_page)
    app.router.add_post("/submit", form_submit)
    return app


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    tg_app = Application.builder().token(BOT_TOKEN).build()

    # ── Cita conversation ──────────────────────────────────────────────────────
    conv = ConversationHandler(
        entry_points=[CommandHandler("cita", cita_start)],
        states={
            SELECT_PROVINCE: [
                CallbackQueryHandler(cb_provpage,  pattern=r"^PROVPAGE\|"),
                CallbackQueryHandler(cb_province,  pattern=r"^PROV\|"),
                CallbackQueryHandler(cancel,       pattern=r"^CANCEL$"),
            ],
            SELECT_TRAMITE: [
                CallbackQueryHandler(cb_tramite,   pattern=r"^TRAM\|"),
                CallbackQueryHandler(cb_back_prov, pattern=r"^BACK_PROV$"),
                CallbackQueryHandler(cancel,       pattern=r"^CANCEL$"),
            ],
            SELECT_OFFICE: [
                CallbackQueryHandler(cb_office,           pattern=r"^OFIC\|"),
                CallbackQueryHandler(cb_back_tram,        pattern=r"^BACK_TRAM\|"),
                CallbackQueryHandler(cb_continue_in_bot,  pattern=r"^CONTINUE_IN_BOT$"),
                CallbackQueryHandler(cancel,              pattern=r"^CANCEL$"),
            ],
            DATE_FROM:     [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_date_from)],
            DATE_TO:       [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_date_to)],
            ENTER_NOMBRE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, e_nombre)],
            ENTER_APELLIDO:[MessageHandler(filters.TEXT & ~filters.COMMAND, e_apellido)],
            ENTER_NIE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, e_nie)],
            ENTER_FECHA:   [MessageHandler(filters.TEXT & ~filters.COMMAND, e_fecha)],
            ENTER_NACIO:   [MessageHandler(filters.TEXT & ~filters.COMMAND, e_nacio)],
            ENTER_EMAIL:   [MessageHandler(filters.TEXT & ~filters.COMMAND, e_email)],
            ENTER_TEL:     [MessageHandler(filters.TEXT & ~filters.COMMAND, e_tel)],
            CONFIRM: [
                CallbackQueryHandler(cb_confirm, pattern=r"^CONFIRM$"),
                CallbackQueryHandler(cb_edit,    pattern=r"^EDIT$"),
                CallbackQueryHandler(cancel,     pattern=r"^CANCEL$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel, pattern=r"^CANCEL$"),
        ],
        allow_reentry=True,
    )

    # ── Handlers ───────────────────────────────────────────────────────────────
    tg_app.add_handler(conv)
    tg_app.add_handler(CallbackQueryHandler(admin_approve, pattern=r"^APPROVE\|"))
    tg_app.add_handler(CallbackQueryHandler(admin_reject,  pattern=r"^REJECT\|"))
    tg_app.add_handler(CallbackQueryHandler(noop,          pattern=r"^NOOP$"))
    tg_app.add_handler(CommandHandler("start",       start))
    tg_app.add_handler(CommandHandler("help",        help_cmd))
    tg_app.add_handler(CommandHandler("pending",     pending_users))
    tg_app.add_handler(CommandHandler("users",       list_users))
    tg_app.add_handler(CommandHandler("addcredits",  add_credits))
    tg_app.add_handler(CommandHandler("miscitas",    mis_citas))
    tg_app.add_handler(MessageHandler(filters.Regex(r"^\d{4,8}$"), otp_handler))

    async def post_init(app):
        # Start 24/7 worker
        asyncio.create_task(booking_worker(app.bot))
        # Start web form server
        web_app = create_web_app()
        runner  = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, WEB_HOST, WEB_PORT)
        await site.start()
        logger.info(f"🌐 Web form: http://0.0.0.0:{WEB_PORT}")

    tg_app.post_init = post_init
    logger.info("🤖 MiCitaBot v2 started!")
    tg_app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
