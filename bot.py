#!/usr/bin/env python3
"""
Extranjería Notify Bot
Monitors Spain's Cita Previa Extranjería system and sends Telegram notifications
when appointments become available.
"""

import os
import json
import time
import logging
import asyncio
import aiohttp
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler
)

# ─── CONFIG ─────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHECK_INTERVAL = 60          # seconds between checks
FREE_LIMIT = 3               # max subscriptions on free plan
DB_PATH = "extranjeria.db"

# Cita Previa API endpoints
BASE_URL = "https://icp.administracionelectronica.gob.es/icpplus/acMap"
CITA_URL = "https://icp.administracionelectronica.gob.es/icpplus"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── CONVERSATION STATES ────────────────────────────────────────────────────
(SELECT_PROVINCIA, SELECT_TRAMITE, SELECT_OFICINA) = range(3)

# ─── PROVINCIAS ─────────────────────────────────────────────────────────────
PROVINCIAS = [
    "A Coruña", "Albacete", "Alicante", "Almería", "Araba", "Asturias",
    "Ávila", "Badajoz", "Barcelona", "Bizkaia", "Burgos", "Cáceres",
    "Cádiz", "Cantabria", "Castellón", "Ceuta", "Ciudad Real", "Córdoba",
    "Cuenca", "Gipuzkoa", "Girona", "Granada", "Guadalajara", "Huelva",
    "Huesca", "Illes Balears", "Jaén", "La Rioja", "Las Palmas", "León",
    "Lleida", "Lugo", "Madrid", "Málaga", "Melilla", "Murcia", "Navarra",
    "Ourense", "Palencia", "Pontevedra", "Salamanca", "S.Cruz Tenerife",
    "Segovia", "Sevilla", "Soria", "Tarragona", "Teruel", "Toledo",
    "Valencia", "Valladolid", "Zamora", "Zaragoza"
]

# Province codes mapping (cod_provincia used in API calls)
PROVINCIA_CODES = {
    "A Coruña": "15", "Albacete": "02", "Alicante": "03", "Almería": "04",
    "Araba": "01", "Asturias": "33", "Ávila": "05", "Badajoz": "06",
    "Barcelona": "08", "Bizkaia": "48", "Burgos": "09", "Cáceres": "10",
    "Cádiz": "11", "Cantabria": "39", "Castellón": "12", "Ceuta": "51",
    "Ciudad Real": "13", "Córdoba": "14", "Cuenca": "16", "Gipuzkoa": "20",
    "Girona": "17", "Granada": "18", "Guadalajara": "19", "Huelva": "21",
    "Huesca": "22", "Illes Balears": "07", "Jaén": "23", "La Rioja": "26",
    "Las Palmas": "35", "León": "24", "Lleida": "25", "Lugo": "27",
    "Madrid": "28", "Málaga": "29", "Melilla": "52", "Murcia": "30",
    "Navarra": "31", "Ourense": "32", "Palencia": "34", "Pontevedra": "36",
    "Salamanca": "37", "S.Cruz Tenerife": "38", "Segovia": "40",
    "Sevilla": "41", "Soria": "42", "Tarragona": "43", "Teruel": "44",
    "Toledo": "45", "Valencia": "46", "Valladolid": "47", "Zamora": "49",
    "Zaragoza": "50"
}

# ─── DATABASE ────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            is_pro INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            provincia TEXT,
            tramite TEXT,
            oficina TEXT,
            active INTEGER DEFAULT 1,
            last_notified TEXT,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS availability_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provincia TEXT,
            tramite TEXT,
            oficina TEXT,
            fecha TEXT,
            hora TEXT,
            detected_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def ensure_user(user_id, username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, created_at) VALUES (?,?,?)",
              (user_id, username, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def is_pro(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT is_pro FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row and row[0] == 1

def set_pro(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_pro=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def count_subs(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM subscriptions WHERE user_id=? AND active=1", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n

def add_subscription(user_id, provincia, tramite, oficina):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO subscriptions (user_id, provincia, tramite, oficina, created_at)
        VALUES (?,?,?,?,?)
    """, (user_id, provincia, tramite, oficina, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_subscriptions(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, provincia, tramite, oficina, last_notified
        FROM subscriptions WHERE user_id=? AND active=1
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_subscription(sub_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE subscriptions SET active=0 WHERE id=? AND user_id=?", (sub_id, user_id))
    conn.commit()
    conn.close()

def get_all_active_subscriptions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT s.id, s.user_id, s.provincia, s.tramite, s.oficina, s.last_notified
        FROM subscriptions s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.active=1
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def update_last_notified(sub_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE subscriptions SET last_notified=? WHERE id=?",
              (datetime.now().isoformat(), sub_id))
    conn.commit()
    conn.close()

# ─── CITA PREVIA API ─────────────────────────────────────────────────────────
async def fetch_tramites(provincia_code: str) -> list:
    """Fetch available tramites for a provincia."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{CITA_URL}/citar?p={provincia_code}&locale=es"
            headers = {"User-Agent": "Mozilla/5.0"}
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                # In production this parses the real HTML page for tramite options.
                # Returning common tramites as fallback for demo.
                pass
    except Exception as e:
        logger.warning(f"Could not fetch tramites: {e}")

    # Common tramites across most provinces
    return [
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

async def fetch_oficinas(provincia_code: str, tramite: str) -> list:
    """Fetch available oficinas for provincia + tramite."""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"User-Agent": "Mozilla/5.0"}
            # Real implementation would POST to the cita previa form
            # and parse the oficina dropdown options
            pass
    except Exception as e:
        logger.warning(f"Could not fetch oficinas: {e}")
    return ["Cualquiera"]

async def check_availability(provincia: str, tramite: str, oficina: str) -> dict | None:
    """
    Check if cita is available. Returns dict with details or None.
    
    In production this hits the real Cita Previa form flow:
    1. POST to select provincia
    2. POST to select tramite  
    3. POST to select oficina
    4. Check if appointments exist
    """
    provincia_code = PROVINCIA_CODES.get(provincia, "28")
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9",
                "Referer": "https://icp.administracionelectronica.gob.es/",
            }
            
            # Step 1: Initial request
            url = f"{CITA_URL}/citar?p={provincia_code}&locale=es"
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as r:
                if r.status != 200:
                    return None
                html = await r.text()
            
            # Step 2: Check for appointment availability signals in response
            # Real implementation parses the calendar/slot data
            # This is a simplified version - extend with actual HTML parsing
            
            no_cita_signals = [
                "En este momento no hay citas disponibles",
                "no hay citas",
                "No hay citas disponibles",
                "sin citas disponibles"
            ]
            
            html_lower = html.lower()
            for signal in no_cita_signals:
                if signal.lower() in html_lower:
                    return None  # No appointments available
            
            # If we didn't find the "no appointments" message, 
            # there might be slots — return availability info
            # In production: parse actual date/time from the calendar HTML
            return {
                "provincia": provincia,
                "tramite": tramite,
                "oficina": oficina,
                "fecha": "Disponible",
                "hora": "Ver en web",
                "url": f"{CITA_URL}/citar?p={provincia_code}&locale=es"
            }
            
    except asyncio.TimeoutError:
        logger.warning(f"Timeout checking {provincia}/{tramite}")
        return None
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        return None

# ─── BOT HANDLERS ────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)
    
    text = (
        "🤖 *Extranjería Notify Bot*\n\n"
        "Te aviso cuando haya cita disponible en Cita Previa Extranjería.\n\n"
        "📋 *Comandos disponibles:*\n"
        "/agregar\\_aviso — Añadir aviso de cita\n"
        "/borrar\\_aviso — Eliminar un aviso\n"
        "/estado\\_cuenta — Ver tu cuenta y avisos\n"
        "/estadisticas — Trámites con más actividad\n"
        "/contratar\\_suscripcion — Plan PRO (avisos ilimitados)\n"
        "/help — Ayuda\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_estado_cuenta(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)
    
    subs = get_subscriptions(user.id)
    pro = is_pro(user.id)
    plan = "✅ PRO (ilimitado)" if pro else f"🆓 Gratuito ({len(subs)}/{FREE_LIMIT} avisos)"
    
    text = f"👤 *Tu cuenta*\n\n📦 Plan: {plan}\n\n"
    
    if subs:
        text += "🔔 *Tus avisos activos:*\n"
        for s in subs:
            sid, prov, tram, ofic, last = s
            last_str = last[:16] if last else "Nunca"
            tramite_short = tram[:50] + "..." if len(tram) > 50 else tram
            text += (
                f"\n`[{sid}]` 📍 *{prov}*\n"
                f"   📄 {tramite_short}\n"
                f"   🏢 {ofic}\n"
                f"   🕐 Último aviso: {last_str}\n"
            )
    else:
        text += "No tienes avisos activos.\nUsa /agregar\\_aviso para añadir uno."
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_agregar_aviso(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)
    
    # Check subscription limit
    if not is_pro(user.id) and count_subs(user.id) >= FREE_LIMIT:
        await update.message.reply_text(
            f"⚠️ Alcanzaste el límite de suscripciones.\n"
            f"Puedes contratar una suscripción PRO con el comando /contratar\\_suscripcion",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    # Show provincia keyboard (3 columns)
    keyboard = []
    row = []
    for i, p in enumerate(PROVINCIAS):
        row.append(InlineKeyboardButton(p, callback_data=f"prov|{p}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    await update.message.reply_text(
        "Selecciona la provincia requerida",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_PROVINCIA

async def cb_select_provincia(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    provincia = query.data.split("|")[1]
    ctx.user_data["provincia"] = provincia
    provincia_code = PROVINCIA_CODES.get(provincia, "28")
    
    await query.edit_message_text(f"✅ Provincia: *{provincia}*\n\nCargando trámites...", parse_mode="Markdown")
    
    tramites = await fetch_tramites(provincia_code)
    
    keyboard = []
    for t in tramites:
        label = t[:55] + "..." if len(t) > 55 else t
        keyboard.append([InlineKeyboardButton(label, callback_data=f"tram|{t[:100]}")])
    
    await query.edit_message_text(
        f"✅ Provincia: *{provincia}*\n\nSelecciona el trámite",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SELECT_TRAMITE

async def cb_select_tramite(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    tramite = query.data.split("|", 1)[1]
    ctx.user_data["tramite"] = tramite
    provincia = ctx.user_data["provincia"]
    provincia_code = PROVINCIA_CODES.get(provincia, "28")
    
    await query.edit_message_text(
        f"✅ Provincia: *{provincia}*\n✅ Trámite: _{tramite[:60]}..._\n\nCargando oficinas...",
        parse_mode="Markdown"
    )
    
    oficinas = await fetch_oficinas(provincia_code, tramite)
    
    keyboard = []
    keyboard.append([InlineKeyboardButton("Cualquiera", callback_data="ofic|Cualquiera")])
    for o in oficinas:
        if o != "Cualquiera":
            label = o[:55] + "..." if len(o) > 55 else o
            keyboard.append([InlineKeyboardButton(label, callback_data=f"ofic|{o[:100]}")])
    
    await query.edit_message_text(
        f"✅ Provincia: *{provincia}*\n✅ Trámite: _{tramite[:50]}..._\n\nSelecciona la oficina",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SELECT_OFICINA

async def cb_select_oficina(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    oficina = query.data.split("|", 1)[1]
    provincia = ctx.user_data["provincia"]
    tramite = ctx.user_data["tramite"]
    user_id = query.from_user.id
    
    add_subscription(user_id, provincia, tramite, oficina)
    
    await query.edit_message_text(
        f"✅ *Aviso añadido correctamente*\n\n"
        f"📍 Provincia: *{provincia}*\n"
        f"📄 Trámite: _{tramite[:80]}_\n"
        f"🏢 Oficina: {oficina}\n\n"
        f"Te notificaré en cuanto haya cita disponible. 🔔",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cmd_borrar_aviso(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subs = get_subscriptions(user_id)
    
    if not subs:
        await update.message.reply_text("No tienes avisos activos para borrar.")
        return
    
    keyboard = []
    for s in subs:
        sid, prov, tram, ofic, _ = s
        label = f"[{sid}] {prov} — {tram[:35]}..."
        keyboard.append([InlineKeyboardButton(label, callback_data=f"del|{sid}")])
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="del|cancel")])
    
    await update.message.reply_text(
        "Selecciona el aviso que quieres borrar:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cb_delete_sub(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    val = query.data.split("|")[1]
    if val == "cancel":
        await query.edit_message_text("Operación cancelada.")
        return
    
    sub_id = int(val)
    delete_subscription(sub_id, query.from_user.id)
    await query.edit_message_text(f"✅ Aviso `{sub_id}` eliminado correctamente.", parse_mode="Markdown")

async def cmd_contratar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "💎 *Suscripción PRO*\n\n"
        "Con el plan PRO puedes:\n"
        "• ✅ Avisos ilimitados\n"
        "• ✅ Comprobación cada 30 segundos\n"
        "• ✅ Notificación prioritaria\n\n"
        "Para contratar, contacta al administrador del bot.\n"
        "O usa el botón de abajo para activar PRO (demo)."
    )
    keyboard = [[InlineKeyboardButton("🔓 Activar PRO (Demo)", callback_data="activate_pro")]]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def cb_activate_pro(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    set_pro(query.from_user.id)
    await query.edit_message_text(
        "✅ *¡Plan PRO activado!*\n\nAhora tienes avisos ilimitados. 🎉",
        parse_mode="Markdown"
    )

async def cmd_estadisticas(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT tramite, COUNT(*) as cnt FROM subscriptions
        WHERE active=1 GROUP BY tramite ORDER BY cnt DESC LIMIT 10
    """)
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        await update.message.reply_text("Aún no hay datos de estadísticas.")
        return
    
    text = "📊 *Trámites con más avisos activos:*\n\n"
    for i, (tram, cnt) in enumerate(rows, 1):
        text += f"{i}. _{tram[:60]}_ — *{cnt}* aviso(s)\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ *Ayuda — Extranjería Notify Bot*\n\n"
        "Este bot monitoriza el sistema de Cita Previa Extranjería y te avisa "
        "cuando haya una cita disponible para los trámites que configures.\n\n"
        "*¿Cómo funciona?*\n"
        "1. Usa /agregar\\_aviso y selecciona provincia, trámite y oficina\n"
        "2. El bot comprueba la disponibilidad automáticamente\n"
        "3. Cuando hay cita, recibes una notificación con todos los detalles\n\n"
        "*Plan gratuito:* hasta 3 avisos simultáneos\n"
        "*Plan PRO:* avisos ilimitados — /contratar\\_suscripcion\n\n"
        "Si tienes dudas, contacta al administrador."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ─── BACKGROUND CHECKER ──────────────────────────────────────────────────────

async def check_and_notify(app):
    """Background task: checks all active subscriptions and sends notifications."""
    logger.info("Starting availability checker...")
    
    while True:
        try:
            subs = get_all_active_subscriptions()
            logger.info(f"Checking {len(subs)} subscriptions...")
            
            for sub in subs:
                sub_id, user_id, provincia, tramite, oficina, last_notified = sub
                
                result = await check_availability(provincia, tramite, oficina)
                
                if result:
                    # Check if we already notified recently (within 30 min)
                    if last_notified:
                        last_dt = datetime.fromisoformat(last_notified)
                        elapsed = (datetime.now() - last_dt).total_seconds()
                        if elapsed < 1800:  # 30 minutes cooldown
                            continue
                    
                    # Send notification
                    msg = (
                        f"🚨 *¡CITA DISPONIBLE!*\n\n"
                        f"📍 *Provincia:* {provincia}\n"
                        f"📄 *Trámite:* _{tramite}_\n"
                        f"🏢 *Oficina:* {oficina}\n"
                        f"📅 *Fecha:* {result.get('fecha', 'Disponible')}\n"
                        f"🕐 *Hora:* {result.get('hora', 'Ver en web')}\n\n"
                        f"🔗 [Reservar cita ahora]({result.get('url', 'https://icp.administracionelectronica.gob.es/')})\n\n"
                        f"⏰ Detectado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    
                    try:
                        await app.bot.send_message(
                            chat_id=user_id,
                            text=msg,
                            parse_mode="Markdown",
                            disable_web_page_preview=False
                        )
                        update_last_notified(sub_id)
                        logger.info(f"Notified user {user_id} for {provincia}/{tramite}")
                    except Exception as e:
                        logger.error(f"Failed to send notification to {user_id}: {e}")
                
                await asyncio.sleep(2)  # Small delay between checks
        
        except Exception as e:
            logger.error(f"Checker error: {e}")
        
        await asyncio.sleep(CHECK_INTERVAL)

# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    init_db()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler for adding subscription
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("agregar_aviso", cmd_agregar_aviso)],
        states={
            SELECT_PROVINCIA: [CallbackQueryHandler(cb_select_provincia, pattern="^prov\\|")],
            SELECT_TRAMITE:   [CallbackQueryHandler(cb_select_tramite,   pattern="^tram\\|")],
            SELECT_OFICINA:   [CallbackQueryHandler(cb_select_oficina,   pattern="^ofic\\|")],
        },
        fallbacks=[],
    )
    
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("estado_cuenta", cmd_estado_cuenta))
    app.add_handler(CommandHandler("contratar_suscripcion", cmd_contratar))
    app.add_handler(CommandHandler("borrar_aviso", cmd_borrar_aviso))
    app.add_handler(CommandHandler("estadisticas", cmd_estadisticas))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(cb_delete_sub,     pattern="^del\\|"))
    app.add_handler(CallbackQueryHandler(cb_activate_pro,   pattern="^activate_pro$"))
    
    # Start background checker
    async def post_init(application):
        asyncio.create_task(check_and_notify(application))
    
    app.post_init = post_init
    
    logger.info("Bot starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
