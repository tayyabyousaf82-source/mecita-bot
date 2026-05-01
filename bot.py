import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

logging.basicConfig(level=logging.INFO)

SELECT_TRAMITE, SELECT_PROVINCIA, ENTER_NIE, ENTER_NAME, ENTER_PHONE, CONFIRM = range(6)

PROVINCIAS = ["Madrid", "Barcelona", "Valencia", "Sevilla", "Málaga", "Albacete", "Alicante", "Granada", "Murcia", "Zaragoza"]
TRAMITES = ["TOMA DE HUELLAS (NIE)", "RENOVACIONES Y PRÓRROGAS", "CARTA DE INVITACIÓN", "CÉDULA DE INSCRIPCIÓN"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bienvenido Robot Cita!\n\n/nueva_busqueda - Nueva cita\n/ayuda - Ayuda")

async def nueva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    kb = [[InlineKeyboardButton(t, callback_data=f"t_{i}")] for i, t in enumerate(TRAMITES)]
    await update.message.reply_text("Selecciona tramite:", reply_markup=InlineKeyboardMarkup(kb))
    return SELECT_TRAMITE

async def sel_tramite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data['tramite'] = TRAMITES[int(q.data.split('_')[1])]
    kb = []
    row = []
    for i, p in enumerate(PROVINCIAS):
        row.append(InlineKeyboardButton(p, callback_data=f"p_{i}"))
        if len(row) == 3:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    await q.edit_message_text("Selecciona provincia:", reply_markup=InlineKeyboardMarkup(kb))
    return SELECT_PROVINCIA

async def sel_prov(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data['provincia'] = PROVINCIAS[int(q.data.split('_')[1])]
    await q.edit_message_text("Escribe tu NIE o Pasaporte:")
    return ENTER_NIE

async def enter_nie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nie'] = update.message.text.upper()
    await update.message.reply_text("Nombre completo:")
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nombre'] = update.message.text
    await update.message.reply_text("Telefono (+34...):")
    return ENTER_PHONE

async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['telefono'] = update.message.text
    d = context.user_data
    kb = [[InlineKeyboardButton("✅ Confirmar", callback_data="yes")], [InlineKeyboardButton("❌ Cancelar", callback_data="no")]]
    await update.message.reply_text(f"Confirma:\nTramite: {d['tramite']}\nProvincia: {d['provincia']}\nNIE: {d['nie']}\nNombre: {d['nombre']}\nTel: {d['telefono']}", reply_markup=InlineKeyboardMarkup(kb))
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == 'no':
        await q.edit_message_text("Cancelado.")
        return ConversationHandler.END
    await q.edit_message_text("✅ Busqueda iniciada! Bot monitoreando ICP Clave cada 2-3 min. Te avisare cuando haya cita disponible!")
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelado.")
    return ConversationHandler.END

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/nueva_busqueda - Nueva cita\n/ayuda - Ayuda")

def main():
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    app = Application.builder().token(token).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('nueva_busqueda', nueva)],
        states={
            SELECT_TRAMITE: [CallbackQueryHandler(sel_tramite, pattern='^t_')],
            SELECT_PROVINCIA: [CallbackQueryHandler(sel_prov, pattern='^p_')],
            ENTER_NIE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_nie)],
            ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
            ENTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone)],
            CONFIRM: [CallbackQueryHandler(confirm, pattern='^(yes|no)$')],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)]
    )
    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv)
    app.add_handler(CommandHandler('ayuda', ayuda))
    app.run_polling()

if __name__ == '__main__':
    main()
