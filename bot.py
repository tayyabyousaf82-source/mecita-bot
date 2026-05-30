#!/usr/bin/env python3
import os, logging, asyncio, aiohttp, sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHECK_INTERVAL = 60
FREE_LIMIT = 3
DB_PATH = "/tmp/extranjeria.db"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

SELECT_PROVINCIA, SELECT_TRAMITE, SELECT_OFICINA = range(3)

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
    "POLICÍA-TOMA DE HUELLAS (EXPEDICIÓN DE TARJETA) INICIAL, RENOVACIÓN, DUPLICADO Y LEY 14/2013",
    "POLICÍA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
    "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
    "POLICÍA TARJETA CONFLICTO UCRANIA",
    "POLICÍA-EXP.TARJETA ASOCIADA AL ACUERDO DE RETIRADA (BREXIT)",
    "POLICÍA-EXPEDICIÓN DE TARJETAS CUYA AUTORIZACIÓN RESUELVE OTRA ADMINISTRACIÓN",
    "AUTORIZACIÓN DE REGRESO",
    "POLICIA - CERTIFICADOS CONCORDANCIA",
    "POLICIA- EXPEDICIÓN/RENOVACIÓN DE DOCUMENTOS DE VIAJE",
    "POLICIA-CARTA DE INVITACIÓN",
    "POLICIA-CERTIFICADOS (DE RESIDENCIA, DE NO RESIDENTE, DE CONCORDANCIA)",
    "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
    "POLICIA-ASIGNACIÓN DE NIE",
    "POLICIA - TÍTULOS DE VIAJE",
    "POLICÍA-ASIGNACIÓN NIE NO RESIDENTE NO COMUNITARIO",
    "POLICÍA-CERTIFICADOS (RESIDENCIA Y CONCORDANCIA)",
]

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
                 (uid, uname, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def is_pro(uid):
    conn = sqlite3.connect(DB_PATH)
    r = conn.execute("SELECT is_pro FROM users WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return r and r[0] == 1

def set_pro(uid):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET is_pro=1 WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()

def count_subs(uid):
    conn = sqlite3.connect(DB_PATH)
    n = conn.execute("SELECT COUNT(*) FROM subscriptions WHERE user_id=? AND active=1", (uid,)).fetchone()[0]
    conn.close()
    return n

def add_sub(uid, prov, tram, ofic):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO subscriptions (user_id,provincia,tramite,oficina,created_at) VALUES (?,?,?,?,?)",
                 (uid, prov, tram, ofic, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_subs(uid):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id,provincia,tramite,oficina,last_notified FROM subscriptions WHERE user_id=? AND active=1",
        (uid,)).fetchall()
    conn.close()
    return rows

def del_sub(sid, uid):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE subscriptions SET active=0 WHERE id=? AND user_id=?", (sid, uid))
    conn.commit()
    conn.close()

def all_active_subs():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id,user_id,provincia,tramite,oficina,last_notified FROM subscriptions WHERE active=1"
    ).fetchall()
    conn.close()
    return rows

def update_notified(sid):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE subscriptions SET last_notified=? WHERE id=?",
                 (datetime.now().isoformat(), sid))
    conn.commit()
    conn.close()

async def check_availability(provincia, tramite, oficina):
    pcode = PROVINCIA_CODES.get(provincia, "28")
    try:
        async with aiohttp.ClientSession() as s:
            hdrs = {"User-Agent": "Mozilla/5.0", "Accept-Language": "es-ES,es;q=0.9"}
            url = f"https://icp.administracionelectronica.gob.es/icpplus/citar?p={pcode}&locale=es"
            async with s.get(url, headers=hdrs, timeout=aiohttp.ClientTimeout(total=20)) as r:
                if r.status != 200:
                    return None
                html = await r.text()
            no_cita = ["en este momento no hay citas", "no hay citas disponibles", "sin citas disponibles"]
            for sig in no_cita:
                if sig in html.lower():
                    return None
            return {
                "provincia": provincia, "tramite": tramite, "oficina": oficina,
                "url": f"https://icp.administracionelectronica.gob.es/icpplus/citar?p={pcode}&locale=es"
            }
    except Exception as e:
        logger.warning(f"Check error: {e}")
        return None

async def cmd_start(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ensure_user(u.effective_user.id, u.effective_user.username or "")
    await u.message.reply_text(
        "🤖 *Extranjería Notify Bot*\n\n"
        "Te aviso cuando haya cita disponible\\.\n\n"
        "/agregar\\_aviso — Añadir aviso\n"
        "/borrar\\_aviso — Eliminar aviso\n"
        "/estado\\_cuenta — Ver cuenta\n"
        "/estadisticas — Estadísticas\n"
        "/contratar\\_suscripcion — Plan PRO\n"
        "/help — Ayuda",
        parse_mode="MarkdownV2")

async def cmd_estado(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    ensure_user(uid, u.effective_user.username or "")
    subs = get_subs(uid)
    pro = is_pro(uid)
    plan = "✅ PRO \\(ilimitado\\)" if pro else f"🆓 Gratuito \\({len(subs)}/{FREE_LIMIT}\\)"
    txt = f"👤 *Tu cuenta*\n\n📦 Plan: {plan}\n\n"
    if subs:
        txt += "🔔 *Avisos activos:*\n"
        for sid, prov, tram, ofic, last in subs:
            prov_esc = prov.replace("-","\\-").replace(".","\\.")
            txt += f"\n`[{sid}]` 📍 *{prov_esc}*\n   🏢 {ofic}\n"
    else:
        txt += "No tienes avisos\\. Usa /agregar\\_aviso"
    await u.message.reply_text(txt, parse_mode="MarkdownV2")

async def cmd_agregar(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    ensure_user(uid, u.effective_user.username or "")
    if not is_pro(uid) and count_subs(uid) >= FREE_LIMIT:
        await u.message.reply_text(
            "⚠️ Alcanzaste el límite de suscripciones\\.\n"
            "Contrata PRO: /contratar\\_suscripcion",
            parse_mode="MarkdownV2")
        return ConversationHandler.END
    kb = []
    row = []
    for p in PROVINCIAS:
        row.append(InlineKeyboardButton(p, callback_data=f"prov|{p}"))
        if len(row) == 3:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    await u.message.reply_text("Selecciona la provincia requerida",
                                reply_markup=InlineKeyboardMarkup(kb))
    return SELECT_PROVINCIA

async def cb_provincia(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query
    await q.answer()
    prov = q.data.split("|", 1)[1]
    ctx.user_data["prov"] = prov
    kb = [[InlineKeyboardButton(t[:55] + ("..." if len(t) > 55 else ""),
           callback_data=f"tram|{t[:100]}")] for t in TRAMITES]
    await q.edit_message_text(
        f"✅ Provincia: {prov}\n\nSelecciona el trámite",
        reply_markup=InlineKeyboardMarkup(kb))
    return SELECT_TRAMITE

async def cb_tramite(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query
    await q.answer()
    tram = q.data.split("|", 1)[1]
    ctx.user_data["tram"] = tram
    prov = ctx.user_data["prov"]
    kb = [[InlineKeyboardButton("Cualquiera", callback_data="ofic|Cualquiera")]]
    await q.edit_message_text(
        f"✅ Provincia: {prov}\n✅ Trámite seleccionado\n\nSelecciona la oficina",
        reply_markup=InlineKeyboardMarkup(kb))
    return SELECT_OFICINA

async def cb_oficina(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query
    await q.answer()
    ofic = q.data.split("|", 1)[1]
    prov = ctx.user_data["prov"]
    tram = ctx.user_data["tram"]
    uid = q.from_user.id
    add_sub(uid, prov, tram, ofic)
    await q.edit_message_text(
        f"✅ Aviso añadido!\n\n"
        f"📍 {prov}\n"
        f"📄 {tram[:70]}\n"
        f"🏢 {ofic}\n\n"
        f"Te notificaré cuando haya cita. 🔔")
    return ConversationHandler.END

async def cmd_borrar(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    subs = get_subs(u.effective_user.id)
    if not subs:
        await u.message.reply_text("No tienes avisos activos.")
        return
    kb = []
    for sid, prov, tram, ofic, _ in subs:
        kb.append([InlineKeyboardButton(f"[{sid}] {prov} — {tram[:30]}...",
                   callback_data=f"del|{sid}")])
    kb.append([InlineKeyboardButton("❌ Cancelar", callback_data="del|cancel")])
    await u.message.reply_text("Selecciona el aviso a borrar:",
                                reply_markup=InlineKeyboardMarkup(kb))

async def cb_del(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query
    await q.answer()
    val = q.data.split("|")[1]
    if val == "cancel":
        await q.edit_message_text("Cancelado.")
        return
    del_sub(int(val), q.from_user.id)
    await q.edit_message_text(f"✅ Aviso [{val}] eliminado.")

async def cmd_contratar(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("🔓 Activar PRO (Demo)", callback_data="activate_pro")]]
    await u.message.reply_text(
        "💎 Plan PRO\n\n✅ Avisos ilimitados\n✅ Comprobación rápida",
        reply_markup=InlineKeyboardMarkup(kb))

async def cb_pro(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query
    await q.answer()
    set_pro(q.from_user.id)
    await q.edit_message_text("✅ Plan PRO activado! Avisos ilimitados. 🎉")

async def cmd_stats(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT tramite,COUNT(*) as c FROM subscriptions WHERE active=1 "
        "GROUP BY tramite ORDER BY c DESC LIMIT 8").fetchall()
    conn.close()
    if not rows:
        await u.message.reply_text("Sin datos aún.")
        return
    txt = "📊 Trámites más monitorizados:\n\n"
    for i, (t, c) in enumerate(rows, 1):
        txt += f"{i}. {t[:55]} — {c} aviso(s)\n"
    await u.message.reply_text(txt)

async def cmd_help(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text(
        "ℹ️ Ayuda\n\n"
        "1. /agregar_aviso → elige provincia, trámite, oficina\n"
        "2. El bot comprueba disponibilidad cada minuto\n"
        "3. Cuando hay cita → recibes notificación\n\n"
        "Plan gratis: 3 avisos | PRO: ilimitados")

async def checker(app):
    logger.info("Checker started...")
    while True:
        try:
            for sid, uid, prov, tram, ofic, last in all_active_subs():
                result = await check_availability(prov, tram, ofic)
                if result:
                    if last:
                        elapsed = (datetime.now() - datetime.fromisoformat(last)).total_seconds()
                        if elapsed < 1800:
                            continue
                    msg = (
                        f"🚨 CITA DISPONIBLE!\n\n"
                        f"📍 Provincia: {prov}\n"
                        f"📄 Trámite: {tram}\n"
                        f"🏢 Oficina: {ofic}\n\n"
                        f"🔗 Reservar: {result['url']}\n\n"
                        f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    try:
                        await app.bot.send_message(uid, msg)
                        update_notified(sid)
                        logger.info(f"Notified user {uid}")
                    except Exception as e:
                        logger.error(f"Notify error: {e}")
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Checker error: {e}")
        await asyncio.sleep(CHECK_INTERVAL)

async def post_init(app: Application):
    asyncio.create_task(checker(app))

def main():
    init_db()
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    conv = ConversationHandler(
        entry_points=[CommandHandler("agregar_aviso", cmd_agregar)],
        states={
            SELECT_PROVINCIA: [CallbackQueryHandler(cb_provincia, pattern="^prov\\|")],
            SELECT_TRAMITE:   [CallbackQueryHandler(cb_tramite,   pattern="^tram\\|")],
            SELECT_OFICINA:   [CallbackQueryHandler(cb_oficina,   pattern="^ofic\\|")],
        },
        fallbacks=[]
    )
    app.add_handler(CommandHandler("start",                 cmd_start))
    app.add_handler(CommandHandler("estado_cuenta",         cmd_estado))
    app.add_handler(CommandHandler("contratar_suscripcion", cmd_contratar))
    app.add_handler(CommandHandler("borrar_aviso",          cmd_borrar))
    app.add_handler(CommandHandler("estadisticas",          cmd_stats))
    app.add_handler(CommandHandler("help",                  cmd_help))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(cb_del, pattern="^del\\|"))
    app.add_handler(CallbackQueryHandler(cb_pro, pattern="^activate_pro$"))
    logger.info("Bot running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
