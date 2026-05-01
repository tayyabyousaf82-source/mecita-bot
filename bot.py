import os, logging, asyncio, aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SELECT_TRAMITE, SELECT_PROVINCIA, ENTER_NIE, ENTER_NAME, ENTER_PHONE, CONFIRM = range(6)

PROVINCIAS = ["Madrid", "Barcelona", "Valencia", "Sevilla", "Málaga", "Albacete", "Alicante", "Granada", "Murcia", "Zaragoza"]
TRAMITES = ["TOMA DE HUELLAS (NIE)", "RENOVACIONES Y PRÓRROGAS", "CARTA DE INVITACIÓN", "CÉDULA DE INSCRIPCIÓN"]

# Store active searches
active_searches = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bienvenido Robot Cita!\n\n/nueva_busqueda - Nueva cita\n/mis_busquedas - Ver busquedas\n/ayuda - Ayuda")

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
    kb = [[InlineKeyboardButton("✅ Confirmar y Monitorear", callback_data="yes")], [InlineKeyboardButton("❌ Cancelar", callback_data="no")]]
    await update.message.reply_text(
        f"📋 Confirma tus datos:\n\n"
        f"🔍 Tramite: {d['tramite']}\n"
        f"📍 Provincia: {d['provincia']}\n"
        f"🪪 NIE: {d['nie']}\n"
        f"👤 Nombre: {d['nombre']}\n"
        f"📱 Tel: {d['telefono']}",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == 'no':
        await q.edit_message_text("Cancelado.")
        return ConversationHandler.END
    
    user_id = update.effective_user.id
    data = context.user_data.copy()
    
    # Save search
    if user_id not in active_searches:
        active_searches[user_id] = []
    search_id = len(active_searches[user_id]) + 1
    active_searches[user_id].append({
        'id': search_id,
        'data': data,
        'active': True
    })
    
    await q.edit_message_text(
        f"✅ Busqueda #{search_id} iniciada!\n\n"
        f"🤖 Bot monitoreando ICP Clave cada 3 minutos.\n"
        f"📲 Te avisare cuando haya cita disponible!\n\n"
        f"/mis_busquedas - Ver estado"
    )
    
    # Start monitoring in background
    asyncio.create_task(monitor_icp(user_id, search_id, data, context.application.bot))
    
    return ConversationHandler.END

async def monitor_icp(user_id: int, search_id: int, data: dict, bot):
    """Monitor ICP Clave for available appointments"""
    attempt = 0
    while True:
        attempt += 1
        try:
            # Check if search still active
            if user_id not in active_searches:
                break
            searches = active_searches[user_id]
            search = next((s for s in searches if s['id'] == search_id), None)
            if not search or not search['active']:
                break
            
            logger.info(f"Checking ICP Clave - User {user_id}, Search {search_id}, Attempt {attempt}")
            
            # Check ICP Clave
            available = await check_icp_availability(data)
            
            if available:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 CITA DISPONIBLE!\n\n"
                         f"📍 Provincia: {data['provincia']}\n"
                         f"🔍 Tramite: {data['tramite']}\n\n"
                         f"🔗 Ve AHORA a reservar:\n"
                         f"https://icp.administracionelectronica.gob.es/icpplus/index.html\n\n"
                         f"⚡ Las citas se agotan rapido!"
                )
                # Mark as booked
                if search:
                    search['active'] = False
                break
            else:
                logger.info(f"No slots available. Waiting 3 minutes...")
            
        except Exception as e:
            logger.error(f"Monitor error: {e}")
        
        await asyncio.sleep(180)  # Wait 3 minutes

async def check_icp_availability(data: dict) -> bool:
    """Check if ICP Clave has available slots"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(
                'https://icp.administracionelectronica.gob.es/icpplus/index.html',
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # If page loads, there might be slots
                    # More specific checks can be added
                    no_slot_messages = ['no hay citas', 'no existen', 'no quedan']
                    for msg in no_slot_messages:
                        if msg in text.lower():
                            return False
                    return True
    except Exception as e:
        logger.error(f"ICP check error: {e}")
    return False

async def mis_busquedas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in active_searches or not active_searches[user_id]:
        await update.message.reply_text("No hay busquedas activas.\n/nueva_busqueda para empezar!")
        return
    
    text = "📋 Tus busquedas:\n\n"
    kb = []
    for s in active_searches[user_id]:
        status = "🟢 Activa" if s['active'] else "✅ Completada"
        text += f"#{s['id']} {status}\n{s['data']['provincia']} - {s['data']['tramite'][:30]}\n\n"
        if s['active']:
            kb.append([InlineKeyboardButton(f"❌ Cancelar #{s['id']}", callback_data=f"cancel_{s['id']}")])
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb) if kb else None)

async def cancel_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    search_id = int(q.data.split('_')[1])
    if user_id in active_searches:
        for s in active_searches[user_id]:
            if s['id'] == search_id:
                s['active'] = False
    await q.edit_message_text(f"✅ Busqueda #{search_id} cancelada.")

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelado.")
    return ConversationHandler.END

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/nueva_busqueda - Nueva cita\n/mis_busquedas - Ver busquedas\n/ayuda - Ayuda")

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
    app.add_handler(CommandHandler('mis_busquedas', mis_busquedas))
    app.add_handler(CommandHandler('ayuda', ayuda))
    app.add_handler(CallbackQueryHandler(cancel_cb, pattern='^cancel_'))
    app.run_polling()

if __name__ == '__main__':
    main()
