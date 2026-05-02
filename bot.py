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
BASE_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "mecita-bot-production.up.railway.app")

WAITING_PROVINCIA, WAITING_TRAMITE, WAITING_OFICINA = range(3)

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


# STEP 1 — Provincia
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


# STEP 2 — Tramite
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


# STEP 3 — Oficina
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


# FINAL — Oficina selected → send form link directly
async def seleccionar_oficina(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.replace("ofic_", ""))
    pid = context.user_data["provincia_id"]
    oficina = PROVINCIA_DATA[pid]["oficinas"][idx]
    provincia = context.user_data["provincia_name"]
    tramite = context.user_data["tramite_name"]

    # Build form URL with pre-filled oficina/tramite/provincia
    params = {
        "oficina": oficina,
        "tramite": tramite,
        "provincia": provincia,
    }
    form_url = f"https://{BASE_URL}/form?{urlencode(params)}"

    keyboard = [[InlineKeyboardButton("📋 Abrir Formulario ICP Clave", url=form_url)]]

    await query.edit_message_text(
        f"✅ *Selección completada:*\n\n"
        f"📍 Provincia: {provincia}\n"
        f"📋 Trámite: {tramite}\n"
        f"🏢 Oficina: {oficina}\n\n"
        f"👇 *Abre el formulario y rellena tus datos:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    context.user_data.clear()
    return ConversationHandler.END


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("nueva_busqueda", nueva_busqueda)],
        states={
            WAITING_PROVINCIA: [CallbackQueryHandler(seleccionar_provincia, pattern="^prov_")],
            WAITING_TRAMITE:   [CallbackQueryHandler(seleccionar_tramite, pattern="^tram_")],
            WAITING_OFICINA:   [CallbackQueryHandler(seleccionar_oficina, pattern="^ofic_")],
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
