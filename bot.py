#!/usr/bin/env python3
import os, logging, asyncio, aiohttp, sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHECK_INTERVAL = 60
FREE_LIMIT = 3
DB_PATH = "/tmp/extranjeria.db"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
ASK_PROVINCIA, ASK_TRAMITE, ASK_OFICINA = range(3)

PROVINCIAS = [
    "A Coruña","Albacete","Alicante","Almería","Araba","Asturias",
    "Ávila","Badajoz","Barcelona","Bizkaia","Burgos","Cáceres",
    "Cádiz","Cantabria","Castellón","Ceuta","Ciudad Real","Córdoba",
    "Cuenca","Gipuzkoa","Girona","Granada","Guadalajara","Huelva",
    "Huesca","Illes Balears","Jaén","La Rioja","Las Palmas","León",
    "Lleida","Lugo","Madrid","Málaga","Melilla","Murcia","Navarra",
    "Ourense","Palencia","Pontevedra","Salamanca","S.Cruz Tenerife",
    "Segovia","Sevilla","Soria","Tarragona","Teruel","Toledo",
    "Valencia","Valladolid","Zamora","Zaragoza"
]

PROVINCIA_CODES = {
    "A Coruña":"15","Albacete":"02","Alicante":"03","Almería":"04",
    "Araba":"01","Asturias":"33","Ávila":"05","Badajoz":"06",
    "Barcelona":"08","Bizkaia":"48","Burgos":"09","Cáceres":"10",
    "Cádiz":"11","Cantabria":"39","Castellón":"12","Ceuta":"51",
    "Ciudad Real":"13","Córdoba":"14","Cuenca":"16","Gipuzkoa":"20",
    "Girona":"17","Granada":"18","Guadalajara":"19","Huelva":"21",
    "Huesca":"22","Illes Balears":"07","Jaén":"23","La Rioja":"26",
    "Las Palmas":"35","León":"24","Lleida":"25","Lugo":"27",
    "Madrid":"28","Málaga":"29","Melilla":"52","Murcia":"30",
    "Navarra":"31","Ourense":"32","Palencia":"34","Pontevedra":"36",
    "Salamanca":"37","S.Cruz Tenerife":"38","Segovia":"40",
    "Sevilla":"41","Soria":"42","Tarragona":"43","Teruel":"44",
    "Toledo":"45","Valencia":"46","Valladolid":"47","Zamora":"49",
    "Zaragoza":"50"
}

TRAMITES = [
    "TOMA DE HUELLAS (TIE) INICIAL/RENOVACION/DUPLICADO",
    "CERTIFICADO REGISTRO CIUDADANO UE",
    "RECOGIDA TARJETA IDENTIDAD EXTRANJERO (TIE)",
    "TARJETA CONFLICTO UCRANIA",
    "TARJETA ACUERDO RETIRADA BREXIT",
    "EXPEDICION TARJETAS AUTORIZACION OTRA ADMINISTRACION",
    "AUTORIZACION DE REGRESO",
    "CERTIFICADOS CONCORDANCIA",
    "EXPEDICION/RENOVACION DOCUMENTOS DE VIAJE",
    "CARTA DE INVITACION",
    "CERTIFICADOS DE RESIDENCIA/NO RESIDENTE",
    "CERTIFICADOS Y ASIGNACION NIE NO RESIDENTES",
    "ASIGNACION DE NIE",
    "TITULOS DE VIAJE",
    "ASIGNACION NIE NO RESIDENTE NO COMUNITARIO",
    "CERTIFICADOS RESIDENCIA Y CONCORDANCIA",
]

# ── DATABASE ─────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT,
        is_pro INTEGER DEFAULT 0, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        provincia TEXT, tramite TEXT, oficina TEXT,
        active INTEGER DEFAULT 1, last_notified TEXT, created_at TEXT)""")
    conn.commit()
    conn.close()

def ensure_user(uid, uname):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR IGNORE INTO users (user_id,username,created_at) VALUES (?,?,?)",
                 (uid, uname or "", datetime.now().isoformat()))
    conn.commit(); conn.close()

def is_pro(uid):
    conn = sqlite3.connect(DB_PATH)
    r = conn.execute("SELECT is_pro FROM users WHERE user_id=?", (uid,)).fetchone()
    conn.close(); return bool(r and r[0])

def set_pro(uid):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET is_pro=1 WHERE user_id=?", (uid,))
    conn.commit(); conn.close()

def count_subs(uid):
    conn = sqlite3.connect(DB_PATH)
    n = conn.execute("SELECT COUNT(*) FROM subscriptions WHERE user_id=? AND active=1",(uid,)).fetchone()[0]
    conn.close(); return n

def add_sub(uid, prov, tram, ofic):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO subscriptions (user_id,provincia,tramite,oficina,created_at) VALUES (?,?,?,?,?)",
                 (uid, prov, tram, ofic, datetime.now().isoformat()))
    conn.commit(); conn.close()

def get_subs(uid):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id,provincia,tramite,oficina,last_notified FROM subscriptions WHERE user_id=? AND active=1",(uid,)
    ).fetchall()
    conn.close(); return rows

def del_sub(sid, uid):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE subscriptions SET active=0 WHERE id=? AND user_id=?",(sid,uid))
    conn.commit(); conn.close()

def all_active_subs():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id,user_id,provincia,tramite,oficina,last_notified FROM subscriptions WHERE active=1"
    ).fetchall()
    conn.close(); return rows

def update_notified(sid):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE subscriptions SET last_notified=? WHERE id=?",(datetime.now().isoformat(),sid))
    conn.commit(); conn.close()

# ── KEYBOARDS ────────────────────────────────────────────────────────────────
def provincia_keyboard():
    kb = []
    row = []
    for i, p in enumerate(PROVINCIAS):
        row.append(InlineKeyboardButton(p, callback_data=f"P:{p}"))
        if len(row) == 3:
            kb.append(row); row = []
    if row: kb.append(row)
    return InlineKeyboardMarkup(kb)

def tramite_keyboard():
    kb = []
    for i, t in enumerate(TRAMITES):
        label = t[:50] + "..." if len(t) > 50 else t
        kb.append([InlineKeyboardButton(label, callback_data=f"T:{i}")])
    return InlineKeyboardMarkup(kb)

def oficina_keyboard():
    kb = [[InlineKeyboardButton("Cualquiera", callback_data="O:Cualquiera")]]
    return InlineKeyboardMarkup(kb)

# ── HANDLERS ─────────────────────────────────────────────────────────────────
async def cmd_start(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ensure_user(u.effective_user.id, u.effective_user.username)
    await u.message.reply_text(
        "🤖 Extranjería Notify Bot\n\n"
        "Te aviso cuando haya cita disponible en Cita Previa.\n\n"
        "Comandos:\n"
        "/agregar_aviso - Añadir aviso\n"
        "/borrar_aviso - Eliminar aviso\n"
        "/estado_cuenta - Ver tu cuenta\n"
        "/estadisticas - Ver estadísticas\n"
        "/contratar_suscripcion - Plan PRO\n"
        "/help - Ayuda"
    )

async def cmd_agregar(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    ensure_user(uid, u.effective_user.username)
    if not is_pro(uid) and count_subs(uid) >= FREE_LIMIT:
        await u.message.reply_text(
            f"⚠️ Alcanzaste el limite de suscripciones ({FREE_LIMIT}).\n"
            "Contrata PRO con /contratar_suscripcion")
        return ConversationHandler.END
    await u.message.reply_text(
        "Selecciona la provincia requerida",
        reply_markup=provincia_keyboard())
    return ASK_PROVINCIA

async def cb_provincia(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query
    await q.answer()
    prov = q.data[2:]  # remove "P:"
    ctx.user_data["prov"] = prov
    logger.info(f"User {q.from_user.id} selected provincia: {prov}")
    await q.edit_message_text(
        f"✅ Provincia: {prov}\n\nSelecciona el tramite:",
        reply_markup=tramite_keyboard())
    return ASK_TRAMITE

async def cb_tramite(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query
    await q.answer()
    idx = int(q.data[2:])  # remove "T:"
    tram = TRAMITES[idx]
    ctx.user_data["tram"] = tram
    prov = ctx.user_data.get("prov", "?")
    logger.info(f"User {q.from_user.id} selected tramite: {tram}")
    await q.edit_message_text(
        f"✅ Provincia: {prov}\n"
        f"✅ Tramite: {tram[:60]}\n\n"
        f"Selecciona la oficina:",
        reply_markup=oficina_keyboard())
    return ASK_OFICINA

async def cb_oficina(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query
    await q.answer()
    ofic = q.data[2:]  # remove "O:"
    prov = ctx.user_data.get("prov", "?")
    tram = ctx.user_data.get("tram", "?")
    uid = q.from_user.id
    add_sub(uid, prov, tram, ofic)
    logger.info(f"Added subscription for user {uid}: {prov} / {tram} / {ofic}")
    await q.edit_message_text(
        f"✅ Aviso anadido correctamente!\n\n"
        f"📍 Provincia: {prov}\n"
        f"📄 Tramite: {tram}\n"
        f"🏢 Oficina: {ofic}\n\n"
        f"Te avisare cuando haya cita disponible. 🔔")
    return ConversationHandler.END

async def cmd_estado(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    ensure_user(uid, u.effective_user.username)
    subs = get_subs(uid)
    pro = is_pro(uid)
    plan = "PRO (ilimitado)" if pro else f"Gratuito ({len(subs)}/{FREE_LIMIT})"
    txt = f"👤 Tu cuenta\n\nPlan: {plan}\n\n"
    if subs:
        txt += "🔔 Avisos activos:\n\n"
        for sid, prov, tram, ofic, last in subs:
            last_str = last[:16] if last else "Nunca"
            txt += f"[{sid}] 📍 {prov}\n    📄 {tram[:50]}\n    🏢 {ofic}\n    🕐 {last_str}\n\n"
    else:
        txt += "No tienes avisos. Usa /agregar_aviso"
    await u.message.reply_text(txt)

async def cmd_borrar(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    subs = get_subs(u.effective_user.id)
    if not subs:
        await u.message.reply_text("No tienes avisos activos."); return
    kb = []
    for sid, prov, tram, ofic, _ in subs:
        kb.append([InlineKeyboardButton(
            f"[{sid}] {prov} - {tram[:35]}",
            callback_data=f"DEL:{sid}")])
    kb.append([InlineKeyboardButton("❌ Cancelar", callback_data="DEL:cancel")])
    await u.message.reply_text("Selecciona el aviso a borrar:",
                                reply_markup=InlineKeyboardMarkup(kb))

async def cb_del(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    val = q.data[4:]  # remove "DEL:"
    if val == "cancel":
        await q.edit_message_text("Cancelado."); return
    del_sub(int(val), q.from_user.id)
    await q.edit_message_text(f"✅ Aviso [{val}] eliminado.")

async def cmd_contratar(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("🔓 Activar PRO (Demo)", callback_data="PRO:activate")]]
    await u.message.reply_text(
        "💎 Plan PRO\n\n"
        "✅ Avisos ilimitados\n"
        "✅ Comprobacion rapida\n"
        "✅ Prioridad alta\n\n"
        "Contacta al admin para activar.",
        reply_markup=InlineKeyboardMarkup(kb))

async def cb_pro(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    set_pro(q.from_user.id)
    await q.edit_message_text("✅ Plan PRO activado! Avisos ilimitados. 🎉")

async def cmd_stats(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT tramite,COUNT(*) c FROM subscriptions WHERE active=1 GROUP BY tramite ORDER BY c DESC LIMIT 8"
    ).fetchall()
    conn.close()
    if not rows: await u.message.reply_text("Sin datos aun."); return
    txt = "📊 Tramites mas monitorizados:\n\n"
    for i,(t,c) in enumerate(rows,1): txt += f"{i}. {t[:50]} - {c}\n"
    await u.message.reply_text(txt)

async def cmd_help(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text(
        "ℹ️ Ayuda\n\n"
        "1. /agregar_aviso - elige provincia, tramite, oficina\n"
        "2. Bot comprueba disponibilidad cada minuto\n"
        "3. Cuando hay cita - recibes notificacion\n\n"
        "Plan gratis: 3 avisos\n"
        "Plan PRO: ilimitados - /contratar_suscripcion")

# ── CHECKER ──────────────────────────────────────────────────────────────────
async def check_availability(provincia, tramite, oficina):
    pcode = PROVINCIA_CODES.get(provincia, "28")
    try:
        async with aiohttp.ClientSession() as s:
            hdrs = {"User-Agent": "Mozilla/5.0", "Accept-Language": "es-ES,es;q=0.9"}
            url = f"https://icp.administracionelectronica.gob.es/icpplus/citar?p={pcode}&locale=es"
            async with s.get(url, headers=hdrs, timeout=aiohttp.ClientTimeout(total=20)) as r:
                if r.status != 200: return None
                html = await r.text()
            for sig in ["en este momento no hay citas","no hay citas disponibles"]:
                if sig in html.lower(): return None
            return {"provincia": provincia, "tramite": tramite, "oficina": oficina,
                    "url": f"https://icp.administracionelectronica.gob.es/icpplus/citar?p={pcode}&locale=es"}
    except Exception as e:
        logger.warning(f"Check error: {e}"); return None

async def checker(app):
    logger.info("Availability checker started")
    while True:
        try:
            for sid, uid, prov, tram, ofic, last in all_active_subs():
                result = await check_availability(prov, tram, ofic)
                if result:
                    if last:
                        elapsed = (datetime.now()-datetime.fromisoformat(last)).total_seconds()
                        if elapsed < 1800: continue
                    msg = (f"🚨 CITA DISPONIBLE!\n\n"
                           f"📍 Provincia: {prov}\n"
                           f"📄 Tramite: {tram}\n"
                           f"🏢 Oficina: {ofic}\n\n"
                           f"🔗 {result['url']}\n\n"
                           f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    try:
                        await app.bot.send_message(uid, msg)
                        update_notified(sid)
                    except Exception as e:
                        logger.error(f"Send error: {e}")
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Checker error: {e}")
        await asyncio.sleep(CHECK_INTERVAL)

async def post_init(app: Application):
    asyncio.create_task(checker(app))

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("agregar_aviso", cmd_agregar)],
        states={
            ASK_PROVINCIA: [CallbackQueryHandler(cb_provincia, pattern="^P:")],
            ASK_TRAMITE:   [CallbackQueryHandler(cb_tramite,   pattern="^T:")],
            ASK_OFICINA:   [CallbackQueryHandler(cb_oficina,   pattern="^O:")],
        },
        fallbacks=[CommandHandler("start", cmd_start)],
        per_message=False,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("start",                 cmd_start))
    app.add_handler(CommandHandler("estado_cuenta",         cmd_estado))
    app.add_handler(CommandHandler("contratar_suscripcion", cmd_contratar))
    app.add_handler(CommandHandler("borrar_aviso",          cmd_borrar))
    app.add_handler(CommandHandler("estadisticas",          cmd_stats))
    app.add_handler(CommandHandler("help",                  cmd_help))
    app.add_handler(CallbackQueryHandler(cb_del,  pattern="^DEL:"))
    app.add_handler(CallbackQueryHandler(cb_pro,  pattern="^PRO:"))

    logger.info("Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
