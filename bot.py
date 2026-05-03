"""
MiCitaBot v2 — @mecita_bot
Full features:
  - Admin approval + credits system
  - Telegram bot flow + HTML web form
  - 24/7 background booking worker
  - 2Captcha solver
  - OTP via Spanish phone
  - PDF confirmation download
  - Date range selection
"""
import logging, asyncio, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from aiohttp import web
import json

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
 CONFIRM, WAIT_OTP) = range(14)


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def check_access(update: Update) -> bool:
    uid = update.effective_user.id
    if uid in ADMIN_IDS: return True
    return db.get_user_status(uid) == "approved"

def province_keyboard(page=0):
    provs = sorted(PROVINCIA_DATA.items(), key=lambda x: x[1]["name"])
    per = 18
    chunk = provs[page*per:(page+1)*per]
    rows = []
    row = []
    for i,(pid,pd) in enumerate(chunk):
        row.append(InlineKeyboardButton(pd["name"], callback_data=f"p_{pid}"))
        if len(row)==3: rows.append(row); row=[]
    if row: rows.append(row)
    nav = []
    if page>0: nav.append(InlineKeyboardButton("◀️",callback_data=f"pp_{page-1}"))
    total = (len(provs)+per-1)//per
    nav.append(InlineKeyboardButton(f"{page+1}/{total}",callback_data="noop"))
    if (page+1)*per < len(provs): nav.append(InlineKeyboardButton("▶️",callback_data=f"pp_{page+1}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton("❌ Cancelar",callback_data="cancel")])
    return InlineKeyboardMarkup(rows)

def tramite_keyboard(pid):
    tramites = PROVINCIA_DATA[pid]["tramites"]
    rows = [[InlineKeyboardButton(
        v.replace("POLICIA - ",""), callback_data=f"t_{pid}_{k}"
    )] for k,v in tramites.items()]
    rows.append([InlineKeyboardButton("◀️ Volver",callback_data="back_p")])
    return InlineKeyboardMarkup(rows)

def office_keyboard(pid):
    oficinas = PROVINCIA_DATA[pid]["oficinas"]
    rows = [[InlineKeyboardButton(
        f"🏢 {o.replace('CNP - COMISARIA ','').replace('CNP - ','')[:50]}",
        callback_data=f"o_{pid}_{i}"
    )] for i,o in enumerate(oficinas)]
    rows.append([InlineKeyboardButton("◀️ Volver",callback_data=f"back_t_{pid}")])
    return InlineKeyboardMarkup(rows)

def summary_text(d):
    p  = PROVINCIA_DATA[d["province_id"]]
    t  = p["tramites"][d["tramite_id"]].replace("POLICIA - ","")
    o  = p["oficinas"][int(d["oficina_idx"])]
    df = d.get("date_from","—"); dt = d.get("date_to","—")
    return (
        f"📋 *RESUMEN DE CITA*\n\n"
        f"🗺️ *Provincia:* {p['name']}\n"
        f"📌 *Trámite:* {t}\n"
        f"🏢 *Oficina:* {o}\n"
        f"📅 *Desde:* {df}  →  *Hasta:* {dt}\n\n"
        f"👤 *Nombre:* {d['nombre']}\n"
        f"👥 *Apellido:* {d['apellido']}\n"
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
            f"Comandos admin:\n"
            f"/pending — Solicitudes pendientes\n"
            f"/users — Todos los usuarios\n"
            f"/addcredits — Añadir créditos\n"
            f"/cita — Pedir cita (admin también puede)",
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
        await update.message.reply_text("⏳ Tu solicitud está *pendiente*. El admin la revisará pronto.", parse_mode="Markdown")
    elif status == "rejected":
        await update.message.reply_text("❌ Tu solicitud ha sido rechazada. Contacta al admin.", parse_mode="Markdown")
    else:
        db.set_user_status(user.id, "pending")
        name = f"{user.first_name} {user.last_name or ''}".strip()
        uname = f"@{user.username}" if user.username else "sin username"
        for aid in ADMIN_IDS:
            try:
                await ctx.bot.send_message(aid,
                    f"🔔 *Nueva solicitud de acceso*\n\n"
                    f"👤 {name}\n{uname}\nID: `{user.id}`",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("✅ Aprobar", callback_data=f"approve_{user.id}"),
                        InlineKeyboardButton("❌ Rechazar", callback_data=f"reject_{user.id}"),
                    ]]))
            except: pass
        await update.message.reply_text(
            "🔔 *Solicitud enviada al admin.*\nTe notificaremos cuando sea aprobada. ⏳",
            parse_mode="Markdown")


# ─── Admin Callbacks ──────────────────────────────────────────────────────────

async def admin_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.from_user.id not in ADMIN_IDS: return

    action, uid = q.data.split("_", 1)
    uid = int(uid)
    if action == "approve":
        db.set_user_status(uid, "approved")
        await q.edit_message_text(q.message.text + "\n\n✅ *APROBADO*", parse_mode="Markdown")
        try: await ctx.bot.send_message(uid, "✅ *¡Acceso aprobado!*\nUsa /cita para reservar. 🎉", parse_mode="Markdown")
        except: pass
    else:
        db.set_user_status(uid, "rejected")
        await q.edit_message_text(q.message.text + "\n\n❌ *RECHAZADO*", parse_mode="Markdown")
        try: await ctx.bot.send_message(uid, "❌ Tu solicitud fue rechazada.", parse_mode="Markdown")
        except: pass


# ─── /addcredits ─────────────────────────────────────────────────────────────

async def add_credits(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    # Usage: /addcredits @username 5  OR  /addcredits 123456789 5
    args = ctx.args
    if len(args) < 2:
        await update.message.reply_text(
            "Uso: `/addcredits @username 5`\nO: `/addcredits 123456789 5`",
            parse_mode="Markdown"); return
    try:
        amount = int(args[1])
        target = args[0].replace("@","")
        # Find user by username or ID
        users = db.get_all_users()
        found = None
        for u in users:
            if str(u["user_id"]) == target or u.get("username","") == target:
                found = u; break
        if not found:
            await update.message.reply_text(f"❌ Usuario `{target}` no encontrado.", parse_mode="Markdown"); return
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
                f"Total disponible: *{new_credits}* créditos.\n\n"
                f"Usa /cita para reservar.",
                parse_mode="Markdown")
        except: pass
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# ─── /cita Conversation ───────────────────────────────────────────────────────

async def cita_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        await update.message.reply_text("⛔ Sin acceso. Usa /start."); return ConversationHandler.END
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        credits = db.get_credits(uid)
        if credits <= 0:
            await update.message.reply_text(
                "❌ *No tienes créditos disponibles.*\n\n"
                "Contacta al admin para obtener créditos.",
                parse_mode="Markdown"); return ConversationHandler.END
    ctx.user_data.clear()
    await update.message.reply_text(
        "🗺️ *Selecciona la provincia:*",
        parse_mode="Markdown",
        reply_markup=province_keyboard())
    return SELECT_PROVINCE

async def province_page(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    page = int(q.data.split("_")[1])
    await q.edit_message_reply_markup(province_keyboard(page))
    return SELECT_PROVINCE

async def province_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    pid = q.data.split("_")[1]
    ctx.user_data["province_id"] = pid
    await q.edit_message_text(
        f"🗺️ *{PROVINCIA_DATA[pid]['name']}*\n\n📋 Selecciona el trámite:",
        parse_mode="Markdown", reply_markup=tramite_keyboard(pid))
    return SELECT_TRAMITE

async def back_provinces(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.edit_message_text("🗺️ *Selecciona la provincia:*", parse_mode="Markdown", reply_markup=province_keyboard())
    return SELECT_PROVINCE

async def tramite_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    _, pid, tid = q.data.split("_", 2)
    ctx.user_data["province_id"] = pid
    ctx.user_data["tramite_id"]  = tid
    pname = PROVINCIA_DATA[pid]["name"]
    tname = PROVINCIA_DATA[pid]["tramites"][tid].replace("POLICIA - ","")
    await q.edit_message_text(
        f"🗺️ *{pname}* → *{tname}*\n\n🏢 Selecciona la oficina:",
        parse_mode="Markdown", reply_markup=office_keyboard(pid))
    return SELECT_OFFICE

async def back_tramite(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    pid = q.data.replace("back_t_","")
    await q.edit_message_text(
        f"🗺️ *{PROVINCIA_DATA[pid]['name']}*\n\n📋 Selecciona el trámite:",
        parse_mode="Markdown", reply_markup=tramite_keyboard(pid))
    return SELECT_TRAMITE

async def office_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    parts = q.data.split("_")
    pid = parts[1]; idx = int(parts[2])
    ctx.user_data["oficina_idx"] = idx
    oname = PROVINCIA_DATA[pid]["oficinas"][idx]
    await q.edit_message_text(
        f"🏢 *{oname}*\n\n"
        f"📅 Escribe la *fecha desde* (YYYY-MM-DD):\n"
        f"_(Ej: 2025-06-01)_",
        parse_mode="Markdown")
    return DATE_FROM

async def enter_date_from(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    import re
    text = update.message.text.strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        await update.message.reply_text("⚠️ Formato: YYYY-MM-DD\n_(Ej: 2025-06-01)_", parse_mode="Markdown")
        return DATE_FROM
    ctx.user_data["date_from"] = text
    await update.message.reply_text(
        f"📅 Fecha *desde*: `{text}`\n\n"
        f"Ahora escribe la *fecha hasta* (YYYY-MM-DD):",
        parse_mode="Markdown")
    return DATE_TO

async def enter_date_to(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    import re
    text = update.message.text.strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        await update.message.reply_text("⚠️ Formato: YYYY-MM-DD\n_(Ej: 2025-07-31)_", parse_mode="Markdown")
        return DATE_TO
    ctx.user_data["date_to"] = text
    await update.message.reply_text("👤 Escribe tu *nombre*:", parse_mode="Markdown")
    return ENTER_NOMBRE

async def e_nombre(u,c): c.user_data["nombre"]=u.message.text.strip(); await u.message.reply_text("👥 *Apellido/s:*",parse_mode="Markdown"); return ENTER_APELLIDO
async def e_apellido(u,c): c.user_data["apellido"]=u.message.text.strip(); await u.message.reply_text("🪪 *NIE/Pasaporte:*",parse_mode="Markdown"); return ENTER_NIE
async def e_nie(u,c): c.user_data["nie"]=u.message.text.strip().upper(); await u.message.reply_text("🎂 *Fecha de nacimiento* (YYYY-MM-DD):",parse_mode="Markdown"); return ENTER_FECHA

async def e_fecha(u,c):
    import re
    t=u.message.text.strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$",t):
        await u.message.reply_text("⚠️ Formato: YYYY-MM-DD"); return ENTER_FECHA
    c.user_data["fecha_nac"]=t
    await u.message.reply_text("🌍 *Nacionalidad:*",parse_mode="Markdown"); return ENTER_NACIO

async def e_nacio(u,c): c.user_data["nacionalidad"]=u.message.text.strip(); await u.message.reply_text("📧 *Email:*",parse_mode="Markdown"); return ENTER_EMAIL

async def e_email(u,c):
    import re
    e=u.message.text.strip()
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$",e):
        await u.message.reply_text("⚠️ Email inválido. Intenta de nuevo:"); return ENTER_EMAIL
    c.user_data["email"]=e
    await u.message.reply_text("📞 *Teléfono* (con prefijo, ej: +34612345678):",parse_mode="Markdown"); return ENTER_TEL

async def e_tel(u,c):
    c.user_data["telefono"]=u.message.text.strip()
    c.user_data["telegram_id"]=str(u.effective_user.id)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Confirmar",callback_data="confirm"),
        InlineKeyboardButton("✏️ Editar",callback_data="edit"),
    ],[InlineKeyboardButton("❌ Cancelar",callback_data="cancel")]])
    await u.message.reply_text(
        summary_text(c.user_data) + "\n¿Confirmas?",
        parse_mode="Markdown", reply_markup=kb)
    return CONFIRM

async def confirm_booking(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.data == "edit":
        await q.edit_message_text("✏️ Escribe tu *nombre* de nuevo:", parse_mode="Markdown")
        return ENTER_NOMBRE
    uid = q.from_user.id
    data = ctx.user_data.copy()

    # Deduct credit (not for admins)
    if uid not in ADMIN_IDS:
        db.deduct_credit(uid)
        remaining = db.get_credits(uid)
    else:
        remaining = "∞"

    bid = db.save_booking(uid, data, data.get("date_from",""), data.get("date_to",""))
    data["booking_id"] = bid

    await q.edit_message_text(
        f"⏳ *Solicitud registrada!*\n\n"
        f"🆔 Booking ID: `{bid}`\n"
        f"💳 Créditos restantes: *{remaining}*\n\n"
        f"🤖 El bot está buscando cita *24/7* en el rango de fechas seleccionado.\n"
        f"Te notificaremos aquí cuando encuentre una cita disponible.",
        parse_mode="Markdown")

    # Notify admins
    for aid in ADMIN_IDS:
        try:
            await ctx.bot.send_message(aid,
                f"🔔 *Nueva solicitud de cita*\n"
                f"👤 {q.from_user.first_name} (`{uid}`)\n"
                f"🆔 `{bid}`\n\n" + summary_text(data),
                parse_mode="Markdown")
        except: pass

    return ConversationHandler.END


# ─── OTP Handler ──────────────────────────────────────────────────────────────

async def otp_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """User sends OTP code — save to DB for booking worker"""
    import re
    text = update.message.text.strip()
    if re.match(r"^\d{4,8}$", text):
        uid = update.effective_user.id
        last = db.get_last_booking(uid)
        if last and last["status"] in ["queued","retrying"]:
            db.save_otp(last["id"], text)
            await update.message.reply_text("✅ Código OTP recibido. Procesando...", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ No se encontró una reserva activa esperando OTP.")


# ─── /miscitas ────────────────────────────────────────────────────────────────

async def mis_citas(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update): return
    bookings = db.get_user_bookings(update.effective_user.id)
    if not bookings:
        await update.message.reply_text("No tienes reservas. Usa /cita para empezar."); return
    status_map = {"queued":"⏳ Buscando","retrying":"🔄 Reintentando","completed":"✅ Completada","failed":"❌ Fallida","error":"⚠️ Error"}
    lines = ["📋 *Tus últimas reservas:*\n"]
    for b in bookings:
        st = status_map.get(b["status"], b["status"])
        lines.append(f"{st} — `{b['id']}` — {b['created_at'][:10]}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ─── /pending /users ──────────────────────────────────────────────────────────

async def pending_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    users = db.get_pending_users()
    if not users:
        await update.message.reply_text("✅ No hay solicitudes pendientes."); return
    for u in users:
        name = f"{u['first_name']} {u['last_name']}".strip()
        await update.message.reply_text(
            f"👤 *{name}*\n@{u['username'] or 'N/A'}\nID: `{u['user_id']}`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅",callback_data=f"approve_{u['user_id']}"),
                InlineKeyboardButton("❌",callback_data=f"reject_{u['user_id']}"),
            ]]))

async def list_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    users = db.get_all_users()
    em = {"approved":"✅","pending":"⏳","rejected":"❌","new":"🆕"}
    lines = ["👥 *Usuarios:*\n"]
    for u in users:
        c = db.get_credits(u["user_id"])
        lines.append(f"{em.get(u['status'],'❓')} {u['first_name']} `{u['user_id']}` 💳{c}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ─── Cancel ───────────────────────────────────────────────────────────────────

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ Cancelado. Usa /cita para empezar.")
    else:
        await update.message.reply_text("❌ Cancelado.")
    ctx.user_data.clear()
    return ConversationHandler.END

async def noop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()


# ─── 24/7 Background Worker ───────────────────────────────────────────────────

async def booking_worker(bot):
    """Runs forever — processes queued bookings every 5 minutes"""
    logger.info("🤖 24/7 Booking worker started")
    while True:
        try:
            bookings = db.get_queued_bookings()
            for b in bookings:
                bid  = b["id"]
                uid  = b["user_id"]
                data = b["data"]
                data["booking_id"]  = bid
                data["date_from"]   = b.get("date_from","")
                data["date_to"]     = b.get("date_to","")

                logger.info(f"Worker processing booking {bid} (attempt {b['attempts']+1})")
                db.update_booking(bid, "retrying")
                db.increment_attempts(bid)

                result = await book_appointment(data, bot=bot, db=db)

                if result["success"]:
                    pdf_path = result.get("pdf_path","")
                    db.update_booking(bid, "completed", result.get("confirmation",""), pdf_path)

                    # Send success to user
                    msg = (
                        f"🎉 *¡Cita encontrada y reservada!*\n\n"
                        f"📅 *Fecha:* {result.get('fecha','—')}\n"
                        f"🕐 *Hora:* {result.get('hora','—')}\n"
                        f"🏢 *Oficina:* {result.get('oficina','—')}\n"
                        f"🔢 *Confirmación:* `{result.get('confirmation','—')}`\n\n"
                        f"📧 Revisa tu email: {data.get('email','')}"
                    )
                    try: await bot.send_message(uid, msg, parse_mode="Markdown")
                    except: pass

                    # Send PDF
                    if pdf_path and os.path.exists(pdf_path):
                        try:
                            with open(pdf_path,"rb") as f:
                                await bot.send_document(
                                    uid, f,
                                    filename=f"cita_{bid}.pdf",
                                    caption="📄 *PDF de tu confirmación*",
                                    parse_mode="Markdown")
                        except Exception as e:
                            logger.error(f"PDF send error: {e}")

                    # Notify admin
                    for aid in ADMIN_IDS:
                        try:
                            await bot.send_message(aid,
                                f"✅ Cita completada\nBooking: `{bid}`\nRef: {result.get('confirmation','')}",
                                parse_mode="Markdown")
                        except: pass
                else:
                    error = result.get("error","")
                    # Keep retrying unless permanent error
                    permanent = ["rechazado","bloqueado","datos incorrectos"]
                    if any(p in error.lower() for p in permanent):
                        db.update_booking(bid,"failed",error)
                        try: await bot.send_message(uid,
                            f"❌ *Error permanente*\n{error}\n\nContacta al admin.",
                            parse_mode="Markdown")
                        except: pass
                    else:
                        db.update_booking(bid,"queued",error)
                        logger.info(f"Booking {bid} will retry in 5 min: {error}")

        except Exception as e:
            logger.error(f"Worker error: {e}")

        await asyncio.sleep(300)  # 5 minutes between rounds


# ─── Web Server (HTML Form) ───────────────────────────────────────────────────

async def form_page(request):
    with open("templates/form.html","r",encoding="utf-8") as f:
        html = f.read()
    return web.Response(text=html, content_type="text/html")

async def form_submit(request):
    try:
        data = await request.json()
        uid  = int(data.get("telegram_id",0))

        # Check user access
        status = db.get_user_status(uid)
        if status != "approved" and uid not in ADMIN_IDS:
            return web.json_response({"success":False,"error":"Usuario no aprobado"})

        # Check credits
        if uid not in ADMIN_IDS:
            credits = db.get_credits(uid)
            if credits <= 0:
                return web.json_response({"success":False,"error":"Sin créditos disponibles"})
            db.deduct_credit(uid)

        bid = db.save_booking(uid, data, data.get("date_from",""), data.get("date_to",""))
        return web.json_response({"success":True,"booking_id":bid})
    except Exception as e:
        return web.json_response({"success":False,"error":str(e)})

def create_web_app():
    app = web.Application()
    app.router.add_get("/", form_page)
    app.router.add_post("/submit", form_submit)
    return app


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    tg_app = Application.builder().token(BOT_TOKEN).build()

    # Admin callbacks
    tg_app.add_handler(CallbackQueryHandler(admin_cb, pattern="^(approve|reject)_"))
    tg_app.add_handler(CallbackQueryHandler(noop, pattern="^noop$"))

    # Cita conversation
    conv = ConversationHandler(
        entry_points=[CommandHandler("cita", cita_start)],
        states={
            SELECT_PROVINCE: [
                CallbackQueryHandler(province_page,     pattern="^pp_"),
                CallbackQueryHandler(province_selected, pattern="^p_"),
                CallbackQueryHandler(cancel,            pattern="^cancel$"),
            ],
            SELECT_TRAMITE: [
                CallbackQueryHandler(tramite_selected,  pattern="^t_"),
                CallbackQueryHandler(back_provinces,    pattern="^back_p$"),
                CallbackQueryHandler(cancel,            pattern="^cancel$"),
            ],
            SELECT_OFFICE: [
                CallbackQueryHandler(office_selected,   pattern="^o_"),
                CallbackQueryHandler(back_tramite,      pattern="^back_t_"),
                CallbackQueryHandler(cancel,            pattern="^cancel$"),
            ],
            DATE_FROM:    [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_date_from)],
            DATE_TO:      [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_date_to)],
            ENTER_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, e_nombre)],
            ENTER_APELLIDO:[MessageHandler(filters.TEXT & ~filters.COMMAND, e_apellido)],
            ENTER_NIE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, e_nie)],
            ENTER_FECHA:  [MessageHandler(filters.TEXT & ~filters.COMMAND, e_fecha)],
            ENTER_NACIO:  [MessageHandler(filters.TEXT & ~filters.COMMAND, e_nacio)],
            ENTER_EMAIL:  [MessageHandler(filters.TEXT & ~filters.COMMAND, e_email)],
            ENTER_TEL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, e_tel)],
            CONFIRM: [
                CallbackQueryHandler(confirm_booking,   pattern="^confirm$"),
                CallbackQueryHandler(confirm_booking,   pattern="^edit$"),
                CallbackQueryHandler(cancel,            pattern="^cancel$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel), CallbackQueryHandler(cancel, pattern="^cancel$")],
        allow_reentry=True,
    )

    tg_app.add_handler(conv)
    tg_app.add_handler(CommandHandler("start",      start))
    tg_app.add_handler(CommandHandler("pending",    pending_users))
    tg_app.add_handler(CommandHandler("users",      list_users))
    tg_app.add_handler(CommandHandler("addcredits", add_credits))
    tg_app.add_handler(CommandHandler("miscitas",   mis_citas))
    tg_app.add_handler(MessageHandler(filters.Regex(r"^\d{4,8}$"), otp_handler))

    async def post_init(app):
        asyncio.create_task(booking_worker(app.bot))
        # Start web server
        web_app = create_web_app()
        runner  = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, WEB_HOST, WEB_PORT)
        await site.start()
        logger.info(f"🌐 Web form running on port {WEB_PORT}")

    tg_app.post_init = post_init
    logger.info("🤖 MiCitaBot v2 started!")
    tg_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
