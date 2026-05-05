"""
RobotCitaBot — Exact same as Robot Cita 2.0
Flow: /nueva_busqueda → Province → Tramite → Oficina → Form Link
FREE — No payment system
"""
import logging, asyncio, os, re, json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from aiohttp import web

from config import BOT_TOKEN, ADMIN_IDS, WEB_PORT, WEB_HOST, WEB_URL
from database import db
from data import PROVINCIA_DATA

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ── States ────────────────────────────────────────────────────────────────────
(SELECT_PROVINCE, SELECT_TRAMITE, SELECT_OFFICE,
 ENTER_OTP) = range(4)

# ── Province Keyboard (3 columns, paginated) ──────────────────────────────────

def province_keyboard(page=0):
    provs = sorted(PROVINCIA_DATA.items(), key=lambda x: x[1]["name"])
    per   = 18
    chunk = provs[page*per:(page+1)*per]
    rows, row = [], []
    for pid, pd in chunk:
        row.append(InlineKeyboardButton(pd["name"], callback_data=f"PROV|{pid}"))
        if len(row) == 3:
            rows.append(row); row = []
    if row:
        rows.append(row)
    total = (len(provs) + per - 1) // per
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Atrás", callback_data=f"PROVPAGE|{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total}", callback_data="NOOP"))
    if (page+1)*per < len(provs):
        nav.append(InlineKeyboardButton("Siguiente ▶️", callback_data=f"PROVPAGE|{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("❌ Cancelar", callback_data="CANCEL")])
    return InlineKeyboardMarkup(rows)

def tramite_keyboard(pid):
    tramites = PROVINCIA_DATA[pid]["tramites"]
    rows = []
    for i, tname in enumerate(tramites):
        short = tname[:58]
        rows.append([InlineKeyboardButton(f"- {short}", callback_data=f"TRAM|{pid}|{i}")])
    rows.append([InlineKeyboardButton("◀️ Volver a Provincias", callback_data="BACK_PROV")])
    rows.append([InlineKeyboardButton("❌ Cancelar", callback_data="CANCEL")])
    return InlineKeyboardMarkup(rows)

def office_keyboard(pid):
    oficinas = PROVINCIA_DATA[pid]["oficinas"]
    rows = []
    rows.append([InlineKeyboardButton(
        "🌐 Cualquier oficina", callback_data=f"OFIC|{pid}|ANY"
    )])
    for i, oname in enumerate(oficinas):
        short = oname.replace("CNP - COMISARIA ", "").replace("CNP - ", "")[:55]
        rows.append([InlineKeyboardButton(f"🏢 {short}", callback_data=f"OFIC|{pid}|{i}")])
    rows.append([InlineKeyboardButton(f"◀️ Volver a Trámites", callback_data=f"BACK_TRAM|{pid}")])
    rows.append([InlineKeyboardButton("❌ Cancelar", callback_data="CANCEL")])
    return InlineKeyboardMarkup(rows)

# ── /start ────────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.save_user(user.id, user.first_name, user.last_name or "", user.username or "")

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Nueva búsqueda", callback_data="GO_NUEVA")],
        [InlineKeyboardButton("📋 Mis búsquedas",  callback_data="GO_MIS")],
    ])
    await update.message.reply_text(
        f"🤖 *Bienvenido, {user.first_name}!*\n\n"
        f"Comandos disponibles:\n"
        f"/nueva\\_busqueda — Iniciar nueva búsqueda\n"
        f"/mis\\_busquedas — Ver tus búsquedas\n"
        f"/ayuda — Ayuda",
        parse_mode="Markdown",
        reply_markup=kb
    )

# ── /nueva_busqueda ───────────────────────────────────────────────────────────

async def nueva_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "🔍 *Extranjería*\n\nSelecciona la provincia:",
        parse_mode="Markdown",
        reply_markup=province_keyboard(0)
    )
    return SELECT_PROVINCE

async def nueva_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear()
    await q.edit_message_text(
        "🔍 *Extranjería*\n\nSelecciona la provincia:",
        parse_mode="Markdown",
        reply_markup=province_keyboard(0)
    )
    return SELECT_PROVINCE

# ── Province ──────────────────────────────────────────────────────────────────

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
        f"🔍 Extranjería\n\n📍 Provincia: *{pname}*\n\nSelecciona el trámite:",
        parse_mode="Markdown",
        reply_markup=tramite_keyboard(pid)
    )
    return SELECT_TRAMITE

async def cb_back_prov(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(
        "🔍 *Extranjería*\n\nSelecciona la provincia:",
        parse_mode="Markdown",
        reply_markup=province_keyboard(0)
    )
    return SELECT_PROVINCE

# ── Tramite ───────────────────────────────────────────────────────────────────

async def cb_tramite(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    _, pid, tidx = q.data.split("|")
    tidx = int(tidx)
    ctx.user_data["province_id"] = pid
    ctx.user_data["tramite_id"]  = tidx
    pname = PROVINCIA_DATA[pid]["name"]
    tname = PROVINCIA_DATA[pid]["tramites"][tidx]
    await q.edit_message_text(
        f"📍 Provincia: *{pname}*\n"
        f"📋 Trámite: *{tname[:50]}*\n\n"
        f"Selecciona la oficina:",
        parse_mode="Markdown",
        reply_markup=office_keyboard(pid)
    )
    return SELECT_OFFICE

async def cb_back_tram(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    pid = q.data.split("|")[1]
    pname = PROVINCIA_DATA[pid]["name"]
    await q.edit_message_text(
        f"📍 Provincia: *{pname}*\n\nSelecciona el trámite:",
        parse_mode="Markdown",
        reply_markup=tramite_keyboard(pid)
    )
    return SELECT_TRAMITE

# ── Office → Send Form Link ───────────────────────────────────────────────────

async def cb_office(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    _, pid, idx = q.data.split("|")
    ctx.user_data["province_id"] = pid
    ctx.user_data["oficina_idx"] = idx

    pname = PROVINCIA_DATA[pid]["name"]
    tidx  = ctx.user_data.get("tramite_id", 0)
    tname = PROVINCIA_DATA[pid]["tramites"][int(tidx)]
    if idx == "ANY":
        oname = "Cualquier oficina"
    else:
        oname = PROVINCIA_DATA[pid]["oficinas"][int(idx)]

    # Build form link
    uid      = q.from_user.id
    form_url = f"{WEB_URL}/form?pid={pid}&tid={tidx}&oidx={idx}&uid={uid}"

    await q.edit_message_text(
        f"📍 Provincia: *{pname}*\n"
        f"📋 Trámite: *{tname[:55]}*\n"
        f"🏢 Oficina: *{oname[:55]}*\n\n"
        f"🔍 Rellena este formulario para completar el proceso de solicitud "
        f"_(enlace válido por 24h)_\n\n"
        f"{form_url}",
        parse_mode="Markdown",
        disable_web_page_preview=False
    )

    # Save search to DB
    try:
        booking_id = db.create_booking(uid, {
            "province_id": pid,
            "tramite_id":  str(tidx),
            "oficina_idx": idx,
            "tramite_name": tname,
            "oficina_name": oname,
            "province_name": pname,
        })
        logger.info(f"Booking created: {booking_id} for user {uid}")
    except Exception as e:
        logger.error(f"DB error: {e}")

    return ConversationHandler.END

# ── OTP Handler ───────────────────────────────────────────────────────────────

async def handle_otp(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """User sends OTP after bot notifies them"""
    user_id = update.effective_user.id
    otp     = update.message.text.strip()
    if re.match(r"^\d{4,8}$", otp):
        # Find active booking for this user
        bookings = db.get_user_bookings(user_id)
        active = [b for b in bookings if b["status"] in ("otp_wait", "running")]
        if active:
            booking_id = active[0]["id"]
            db.save_otp(booking_id, otp)
            await update.message.reply_text(
                f"✅ *OTP recibido: `{otp}`*\n\nProcesando confirmación...",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("⚠️ No hay ninguna cita esperando OTP ahora mismo.")
    return ENTER_OTP

# ── /mis_busquedas ────────────────────────────────────────────────────────────

async def mis_busquedas(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid      = update.effective_user.id
    bookings = db.get_user_bookings(uid)
    if not bookings:
        await update.message.reply_text(
            "📋 No tienes búsquedas activas.\n\n/nueva\\_busqueda para empezar.",
            parse_mode="Markdown"
        )
        return

    text = "📋 *Tus búsquedas:*\n\n"
    kb   = []
    for b in bookings:
        data   = json.loads(b["data"]) if isinstance(b["data"], str) else b["data"]
        status = b["status"]
        emoji  = {"queued":"⏳","running":"🔄","success":"✅","failed":"❌","otp_wait":"📱"}.get(status,"⏳")
        pname  = data.get("province_name", "")
        tname  = data.get("tramite_name", "")[:30]
        text  += f"#{b['id'][:6]} {emoji} *{pname}*\n_{tname}_\n\n"
        if status in ("queued","running","otp_wait"):
            kb.append([InlineKeyboardButton(f"❌ Cancelar #{b['id'][:6]}", callback_data=f"CANCEL_BOOKING|{b['id']}")])

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb) if kb else None
    )

async def cancel_booking_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    bid = q.data.split("|")[1]
    db.update_booking_status(bid, "cancelled")
    await q.edit_message_text(f"✅ Búsqueda `{bid[:6]}` cancelada.", parse_mode="Markdown")

# ── /ayuda ────────────────────────────────────────────────────────────────────

async def ayuda(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Ayuda — RobotCitaBot*\n\n"
        "/nueva\\_busqueda — Iniciar nueva búsqueda de cita\n"
        "/mis\\_busquedas — Ver estado de búsquedas\n"
        "/ayuda — Mostrar esta ayuda\n\n"
        "El bot monitorea ICP Clave y te avisa cuando hay cita disponible.\n"
        "Cuando llegues al OTP, el bot te notificará — envía el código y el bot lo confirmará automáticamente.",
        parse_mode="Markdown"
    )

# ── Cancel ────────────────────────────────────────────────────────────────────

async def cb_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear()
    await q.edit_message_text("❌ Cancelado.")
    return ConversationHandler.END

async def cb_noop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

async def mis_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid      = q.from_user.id
    bookings = db.get_user_bookings(uid)
    if not bookings:
        await q.edit_message_text("📋 No tienes búsquedas.\n\nUsa /nueva\\_busqueda para empezar.", parse_mode="Markdown")
        return
    text = "📋 *Tus búsquedas:*\n\n"
    for b in bookings:
        data   = json.loads(b["data"]) if isinstance(b["data"], str) else b["data"]
        status = b["status"]
        emoji  = {"queued":"⏳","running":"🔄","success":"✅","failed":"❌","otp_wait":"📱"}.get(status,"⏳")
        text  += f"{emoji} *{data.get('province_name','')}* — {data.get('tramite_name','')[:30]}\n"
    await q.edit_message_text(text, parse_mode="Markdown")

# ── Web Server (form endpoint) ────────────────────────────────────────────────

async def handle_form(request):
    """Serve the booking form"""
    import os
    template_path = os.path.join(os.path.dirname(__file__), "templates", "form.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    return web.Response(text=html, content_type="text/html")

async def handle_submit(request):
    """Receive form submission and start booking"""
    try:
        data = await request.json()
        uid  = int(data.get("telegram_id", 0))

        booking_id = db.create_booking(uid, data)
        db.update_booking_status(booking_id, "queued")

        # Notify user
        try:
            app = request.app["tg_app"]
            await app.bot.send_message(
                uid,
                f"✅ *¡Solicitud recibida!*\n\n"
                f"📍 {data.get('province_name','')}\n"
                f"📋 {data.get('tramite_name','')[:50]}\n"
                f"📅 {data.get('date_from','')} → {data.get('date_to','')}\n\n"
                f"🤖 El bot empezará a buscar cita ahora.\n"
                f"_Te avisaré cuando encuentre algo o necesite OTP._",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Notify error: {e}")

        # Start booking worker
        asyncio.create_task(booking_worker(booking_id, data, request.app["tg_app"].bot))

        return web.json_response({"success": True, "booking_id": booking_id})
    except Exception as e:
        logger.error(f"Submit error: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def handle_otp_submit(request):
    """Receive OTP from user via web"""
    try:
        data = await request.json()
        db.save_otp(data["booking_id"], data["otp"])
        return web.json_response({"success": True})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)})

async def handle_health(request):
    return web.Response(text="OK")

# ── Booking Worker ────────────────────────────────────────────────────────────

async def booking_worker(booking_id: str, data: dict, bot):
    """Background worker — tries to book appointment 24/7"""
    from booking import book_appointment
    from config import MAX_RETRIES, RETRY_DELAY

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            b = db.get_booking(booking_id)
            if not b or b["status"] in ("cancelled", "success"):
                break

            db.update_booking_status(booking_id, "running")
            db.increment_attempts(booking_id)

            logger.info(f"[{booking_id}] Attempt {attempt}")
            result = await book_appointment(data, bot=bot, db=db, booking_id=booking_id)

            if result.get("success"):
                db.update_booking_status(booking_id, "success", result)
                uid = int(data.get("telegram_id", 0))

                msg = (
                    f"🎉 *¡CITA RESERVADA!*\n\n"
                    f"📅 Fecha: *{result.get('fecha','')}*\n"
                    f"🕐 Hora: *{result.get('hora','')}*\n"
                    f"🏢 Oficina: {result.get('oficina','')}\n"
                    f"🔖 Localizador: `{result.get('confirmation','')}`"
                )
                await bot.send_message(uid, msg, parse_mode="Markdown")

                # Send PDF if available
                pdf = result.get("pdf_path","")
                if pdf and os.path.exists(pdf):
                    with open(pdf, "rb") as f:
                        await bot.send_document(uid, f, filename=f"cita_{booking_id}.pdf",
                            caption="📄 Justificante de cita")
                break
            else:
                error = result.get("error","")
                if "No hay citas" in error:
                    db.update_booking_status(booking_id, "queued")
                    logger.info(f"[{booking_id}] No citas — retry in {RETRY_DELAY}s")
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    logger.error(f"[{booking_id}] Error: {error}")
                    db.update_booking_status(booking_id, "queued")
                    await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"[{booking_id}] Worker error: {e}")
            db.update_booking_status(booking_id, "queued")
            await asyncio.sleep(60)

# ── Main ──────────────────────────────────────────────────────────────────────

async def run_web(tg_app):
    web_app = web.Application()
    web_app["tg_app"] = tg_app
    web_app.router.add_get("/form",         handle_form)
    web_app.router.add_get("/",             handle_form)
    web_app.router.add_post("/submit",      handle_submit)
    web_app.router.add_post("/otp",         handle_otp_submit)
    web_app.router.add_get("/health",       handle_health)

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, WEB_HOST, WEB_PORT)
    await site.start()
    logger.info(f"Web server started on port {WEB_PORT}")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("nueva_busqueda", nueva_cmd),
            CallbackQueryHandler(nueva_cb, pattern="^GO_NUEVA$"),
        ],
        states={
            SELECT_PROVINCE: [
                CallbackQueryHandler(cb_provpage,  pattern=r"^PROVPAGE\|"),
                CallbackQueryHandler(cb_province,  pattern=r"^PROV\|"),
                CallbackQueryHandler(cb_back_prov, pattern="^BACK_PROV$"),
                CallbackQueryHandler(cb_cancel,    pattern="^CANCEL$"),
            ],
            SELECT_TRAMITE: [
                CallbackQueryHandler(cb_tramite,   pattern=r"^TRAM\|"),
                CallbackQueryHandler(cb_back_tram, pattern=r"^BACK_TRAM\|"),
                CallbackQueryHandler(cb_cancel,    pattern="^CANCEL$"),
            ],
            SELECT_OFFICE: [
                CallbackQueryHandler(cb_office,    pattern=r"^OFIC\|"),
                CallbackQueryHandler(cb_back_tram, pattern=r"^BACK_TRAM\|"),
                CallbackQueryHandler(cb_cancel,    pattern="^CANCEL$"),
            ],
            ENTER_OTP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_otp),
            ],
        },
        fallbacks=[CommandHandler("cancelar", lambda u,c: ConversationHandler.END)],
        per_message=False,
    )

    application.add_handler(CommandHandler("start",          start))
    application.add_handler(conv)
    application.add_handler(CommandHandler("nueva_busqueda", nueva_cmd))
    application.add_handler(CommandHandler("mis_busquedas",  mis_busquedas))
    application.add_handler(CommandHandler("ayuda",          ayuda))
    application.add_handler(CallbackQueryHandler(mis_cb,            pattern="^GO_MIS$"))
    application.add_handler(CallbackQueryHandler(cancel_booking_cb, pattern=r"^CANCEL_BOOKING\|"))
    application.add_handler(CallbackQueryHandler(cb_noop,           pattern="^NOOP$"))

    # Global OTP listener — user sends 4-8 digit code after bot notifies
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r"^\d{4,8}$"),
        handle_otp
    ))
    application.add_handler(CommandHandler("otp", handle_otp))

    async def post_init(app):
        await run_web(app)
        logger.info("Bot started!")

    application.post_init = post_init
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
