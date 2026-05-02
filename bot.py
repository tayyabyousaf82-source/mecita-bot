import os
import logging
from urllib.parse import urlencode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler
)
from data import PROVINCIA_DATA

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "8719883446:AAHBcWG_VNvxd25NTGWPrVC_TDPiP47UIzc"
BASE_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "http://localhost:5000")

(WAITING_PROVINCIA, WAITING_TRAMITE, WAITING_OFICINA,
 WAITING_NIE, WAITING_NOMBRE, WAITING_ANO, WAITING_PAIS,
 WAITING_TELEFONO, WAITING_EMAIL, WAITING_FECHA_MIN, WAITING_FECHA_MAX) = range(11)

SORTED_PROVINCIAS = sorted(PROVINCIA_DATA.items(), key=lambda x: x[1]["name"])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Bienvenido a MiCitaBot!*\n\n"
        "/nueva\_busqueda - Nueva cita\n"
        "/ayuda - Ayuda\n"
        "/cancelar - Cancelar",
        parse_mode="Markdown"
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Comandos:*\n\n"
        "/nueva\_busqueda - Nueva cita\n"
        "/cancelar - Cancelar\n"
        "/ayuda - Ayuda",
        parse_mode="Markdown"
    )

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Operación cancelada.")
    return ConversationHandler.END

async def nueva_busqueda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for i in range(0, len(SORTED_PROVINCIAS), 2):
        row = []
        pid0, pdata0 = SORTED_PROVINCIAS[i]
        row.append(InlineKeyboardButton(pdata0["name"], callback_data=f"prov_{pid0}"))
        if i + 1 < len(SORTED_PROVINCIAS):
            pid1, pdata1 = SORTED_PROVINCIAS[i + 1]
            row.append(InlineKeyboardButton(pdata1["name"], callback_data=f"prov_{pid1}"))
        keyboard.append(row)
    await update.message.reply_text(
        "🗺️ *Paso 1/3* — Selecciona tu *Provincia*:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return WAITING_PROVINCIA

async def seleccionar_provincia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = query.data.replace("prov_", "")
    pdata = PROVINCIA_DATA[pid]
    context.user_data["provincia_id"] = pid
    context.user_data["provincia_name"] = pdata["name"]
    keyboard = [
        [InlineKeyboardButton(nombre, callback_data=f"tram_{code}")]
        for code, nombre in pdata["tramites"].items()
    ]
    await query.edit_message_text(
        f"📍 Provincia: *{pdata['name']}*\n\n"
        f"📋 *Paso 2/3* — Selecciona el *Trámite*:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return WAITING_TRAMITE

async def seleccionar_tramite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tcode = query.data.replace("tram_", "")
    pid = context.user_data["provincia_id"]
    pdata = PROVINCIA_DATA[pid]
    tname = pdata["tramites"].get(tcode, tcode)
    context.user_data["tramite_code"] = tcode
    context.user_data["tramite_name"] = tname
    oficinas = pdata.get("oficinas", [])
    if not oficinas:
        await query.edit_message_text("❌ No hay oficinas disponibles.")
        return ConversationHandler.END
    keyboard = [
        [InlineKeyboardButton(oficinas[i], callback_data=f"ofic_{i}")]
        for i in range(len(oficinas))
    ]
    await query.edit_message_text(
        f"📍 *{context.user_data['provincia_name']}*\n"
        f"📋 *{tname}*\n\n"
        f"🏢 *Paso 3/3* — Selecciona la *Oficina*:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return WAITING_OFICINA

async def seleccionar_oficina(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.replace("ofic_", ""))
    pid = context.user_data["provincia_id"]
    oficina = PROVINCIA_DATA[pid]["oficinas"][idx]
    context.user_data["oficina"] = oficina
    await query.edit_message_text(
        f"✅ *Selección completada:*\n\n"
        f"📍 {context.user_data['provincia_name']}\n"
        f"📋 {context.user_data['tramite_name']}\n"
        f"🏢 {oficina}\n\n"
        f"Ahora escribe tus datos...",
        parse_mode="Markdown"
    )
    await query.message.reply_text("📄 *NIE o Pasaporte*:", parse_mode="Markdown")
    return WAITING_NIE

async def recibir_nie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nie"] = update.message.text.strip().upper()
    await update.message.reply_text("👤 *Nombre y Apellidos*:", parse_mode="Markdown")
    return WAITING_NOMBRE

async def recibir_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nombre"] = update.message.text.strip()
    await update.message.reply_text("🎂 *Año de nacimiento* (ej: 1990):", parse_mode="Markdown")
    return WAITING_ANO

async def recibir_ano(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ano"] = update.message.text.strip()
    await update.message.reply_text("🌍 *País de nacionalidad* (ej: PAKISTAN):", parse_mode="Markdown")
    return WAITING_PAIS

async def recibir_pais(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["pais"] = update.message.text.strip().upper()
    await update.message.reply_text("📱 *Teléfono*:", parse_mode="Markdown")
    return WAITING_TELEFONO

async def recibir_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["telefono"] = update.message.text.strip()
    await update.message.reply_text("📧 *Email* (o `skip`):", parse_mode="Markdown")
    return WAITING_EMAIL

async def recibir_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    context.user_data["email"] = "" if txt.lower() == "skip" else txt
    await update.message.reply_text(
        "📅 *Fecha mínima* (DD/MM/YYYY)\nEj: 01/06/2026",
        parse_mode="Markdown"
    )
    return WAITING_FECHA_MIN

async def recibir_fecha_min(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["fecha_min"] = update.message.text.strip()
    await update.message.reply_text(
        "📅 *Fecha máxima* (DD/MM/YYYY)\nEj: 31/12/2026",
        parse_mode="Markdown"
    )
    return WAITING_FECHA_MAX

async def recibir_fecha_max(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["fecha_max"] = update.message.text.strip()
    await enviar_form_link(update, context)
    return ConversationHandler.END

async def enviar_form_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data
    params = {
        "nie": d.get("nie", ""),
        "nombre": d.get("nombre", ""),
        "ano": d.get("ano", ""),
        "pais": d.get("pais", ""),
        "telefono": d.get("telefono", ""),
        "email": d.get("email", ""),
        "fecha_min": d.get("fecha_min", ""),
        "fecha_max": d.get("fecha_max", ""),
        "oficina": d.get("oficina", ""),
        "tramite": d.get("tramite_name", ""),
        "provincia": d.get("provincia_name", ""),
    }
    form_url = f"https://{BASE_URL}/form?{urlencode(params)}"

    resumen = (
        f"✅ *Resumen:*\n\n"
        f"📍 {d.get('provincia_name')}\n"
        f"📋 {d.get('tramite_name')}\n"
        f"🏢 {d.get('oficina')}\n\n"
        f"📄 NIE: `{d.get('nie')}`\n"
        f"👤 {d.get('nombre')}\n"
        f"🎂 {d.get('ano')}\n"
        f"🌍 {d.get('pais')}\n"
        f"📱 {d.get('telefono')}\n"
        f"📅 {d.get('fecha_min')} → {d.get('fecha_max')}\n\n"
        f"👇 *Abre el formulario — datos ya rellenados:*"
    )
    keyboard = [[InlineKeyboardButton("📋 Abrir Formulario ICP Clave", url=form_url)]]
    await update.message.reply_text(
        resumen,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    context.user_data.clear()

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("nueva_busqueda", nueva_busqueda)],
        states={
            WAITING_PROVINCIA: [CallbackQueryHandler(seleccionar_provincia, pattern="^prov_")],
            WAITING_TRAMITE:   [CallbackQueryHandler(seleccionar_tramite, pattern="^tram_")],
            WAITING_OFICINA:   [CallbackQueryHandler(seleccionar_oficina, pattern="^ofic_")],
            WAITING_NIE:       [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nie)],
            WAITING_NOMBRE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre)],
            WAITING_ANO:       [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_ano)],
            WAITING_PAIS:      [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_pais)],
            WAITING_TELEFONO:  [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_telefono)],
            WAITING_EMAIL:     [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_email)],
            WAITING_FECHA_MIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_fecha_min)],
            WAITING_FECHA_MAX: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_fecha_max)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
        allow_reentry=True,
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(conv)
    logger.info("✅ MiCitaBot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
