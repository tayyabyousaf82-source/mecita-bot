import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler
)
from data import PROVINCIA_DATA

logging.basicConfig(
    format="%(asctime)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "8719883446:AAHBcWG_VNvxd25NTGWPrVC_TDPiP47UIzc"
FORM_LINK = os.environ.get("WEB_URL", "https://notifybotstg.com")

# ── States ────────────────────────────────────────────────
WAITING_NIE, WAITING_PROVINCIA, WAITING_TRAMITE, WAITING_OFICINA = range(4)

# ── Sorted province list ─────────────────────────────────
SORTED_PROVINCIAS = sorted(PROVINCIA_DATA.items(), key=lambda x: x[1]["name"])


# ══════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ══════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Bienvenido a MiCitaBot\\!*\n\n"
        "/nueva\\_busqueda \\- Nueva cita\n"
        "/mis\\_busquedas \\- Ver búsquedas\n"
        "/ayuda \\- Ayuda\n"
        "/cancelar \\- Cancelar operación",
        parse_mode="MarkdownV2"
    )


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Comandos disponibles:*\n\n"
        "/nueva\\_busqueda \\- Iniciar nueva búsqueda de cita\n"
        "/mis\\_busquedas \\- Ver búsquedas activas\n"
        "/cancelar \\- Cancelar operación actual\n"
        "/ayuda \\- Mostrar esta ayuda",
        parse_mode="MarkdownV2"
    )


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Operación cancelada.")
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════
#  STEP 1 — Start: ask for NIE/Passport
# ══════════════════════════════════════════════════════════

async def nueva_busqueda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📄 *Paso 1/4* — Escribe tu *NIE o Pasaporte*:",
        parse_mode="Markdown"
    )
    return WAITING_NIE


# ══════════════════════════════════════════════════════════
#  STEP 2 — Receive NIE → Show Provincias
# ══════════════════════════════════════════════════════════

async def recibir_nie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nie = update.message.text.strip().upper()
    context.user_data["nie"] = nie

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
        f"✅ NIE/Pasaporte: *{nie}*\n\n"
        f"🗺️ *Paso 2/4* — Selecciona tu *Provincia*:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return WAITING_PROVINCIA


# ══════════════════════════════════════════════════════════
#  STEP 3 — Provincia selected → Show Tramites
# ══════════════════════════════════════════════════════════

async def seleccionar_provincia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    pid = query.data.replace("prov_", "")
    if pid not in PROVINCIA_DATA:
        await query.edit_message_text("❌ Provincia no encontrada.")
        return ConversationHandler.END

    pdata = PROVINCIA_DATA[pid]
    context.user_data["provincia_id"] = pid
    context.user_data["provincia_name"] = pdata["name"]

    tramites = pdata["tramites"]
    keyboard = [
        [InlineKeyboardButton(nombre, callback_data=f"tram_{code}")]
        for code, nombre in tramites.items()
    ]

    await query.edit_message_text(
        f"✅ NIE: *{context.user_data['nie']}*\n"
        f"📍 Provincia: *{pdata['name']}*\n\n"
        f"📋 *Paso 3/4* — Selecciona el *Trámite*:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return WAITING_TRAMITE


# ══════════════════════════════════════════════════════════
#  STEP 4 — Tramite selected → Show Oficinas
# ══════════════════════════════════════════════════════════

async def seleccionar_tramite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    tcode = query.data.replace("tram_", "")
    pid = context.user_data.get("provincia_id")
    pdata = PROVINCIA_DATA[pid]
    tname = pdata["tramites"].get(tcode, tcode)

    context.user_data["tramite_code"] = tcode
    context.user_data["tramite_name"] = tname

    oficinas = pdata.get("oficinas", [])
    if not oficinas:
        await query.edit_message_text("❌ No hay oficinas disponibles para este trámite.")
        return ConversationHandler.END

    # Split into pages of 10 if more than 10 offices
    keyboard = [
        [InlineKeyboardButton(oficinas[i], callback_data=f"ofic_{i}")]
        for i in range(len(oficinas))
    ]

    await query.edit_message_text(
        f"✅ NIE: *{context.user_data['nie']}*\n"
        f"📍 Provincia: *{context.user_data['provincia_name']}*\n"
        f"📋 Trámite: *{tname}*\n\n"
        f"🏢 *Paso 4/4* — Selecciona la *Oficina*:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return WAITING_OFICINA


# ══════════════════════════════════════════════════════════
#  FINAL — Oficina selected → Send Form Link
# ══════════════════════════════════════════════════════════

async def seleccionar_oficina(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    idx = int(query.data.replace("ofic_", ""))
    pid = context.user_data["provincia_id"]
    oficinas = PROVINCIA_DATA[pid]["oficinas"]

    if idx >= len(oficinas):
        await query.edit_message_text("❌ Oficina no encontrada.")
        return ConversationHandler.END

    oficina = oficinas[idx]
    nie = context.user_data.get("nie", "")
    provincia = context.user_data.get("provincia_name", "")
    tramite = context.user_data.get("tramite_name", "")

    await query.edit_message_text(
        f"✅ *Resumen de tu búsqueda:*\n\n"
        f"📄 NIE/Pasaporte: `{nie}`\n"
        f"📍 Provincia: {provincia}\n"
        f"📋 Trámite: {tramite}\n"
        f"🏢 Oficina: {oficina}\n\n"
        f"🔗 *Rellena el formulario aquí:*\n{FORM_LINK}",
        parse_mode="Markdown"
    )

    context.user_data.clear()
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════

def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN environment variable not set!")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("nueva_busqueda", nueva_busqueda)],
        states={
            WAITING_NIE:       [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nie)],
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

    logger.info("✅ MiCitaBot started successfully!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
  
