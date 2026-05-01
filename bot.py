import os, logging, asyncio, aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                          MessageHandler, filters, ContextTypes, ConversationHandler)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# States
(SELECT_PROVINCIA, SELECT_TRAMITE, SELECT_OFICINA,
 ENTER_NIE, ENTER_NAME, ENTER_PHONE, CONFIRM) = range(7)

# ── DATA ────────────────────────────────────────────────────────────────────

PROVINCIAS = [
    "A Coruña","Albacete","Alicante","Almería","Araba","Asturias",
    "Ávila","Badajoz","Barcelona","Bizkaia","Burgos","Cáceres",
    "Cádiz","Cantabria","Castellón","Ceuta","Ciudad Real","Córdoba",
    "Cuenca","Gipuzkoa","Girona","Granada","Guadalajara","Huelva",
    "Huesca","Illes Balears","Jaén","La Rioja","Las Palmas","León",
    "Lleida","Lugo","Madrid","Málaga","Melilla","Murcia","Navarra",
    "Ourense","Palencia","Pontevedra","Salamanca","Santa Cruz de Tenerife",
    "Segovia","Sevilla","Soria","Tarragona","Teruel","Toledo","Valencia",
    "Valladolid","Zamora","Zaragoza"
]

# Tramites por provincia (common tramites — customise as needed)
TRAMITES_DEFAULT = [
    "TOMA DE HUELLAS (EXPEDICIÓN DE TARJETA)",
    "RENOVACIONES, PRÓRROGAS Y MODIFICACIONES",
    "CARTA DE INVITACIÓN",
    "CÉDULA DE INSCRIPCIÓN",
    "CERTIFICADOS CONCORDANCIA",
    "TÍTULOS DE VIAJE",
    "SOLICITUD DE APATRIDA",
    "RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO",
]

TRAMITES_EXTRA = {
    "Barcelona": TRAMITES_DEFAULT + [
        "EXPEDICIÓN/RENOVACIÓN DE DOCUMENTOS DE VIAJE",
        "CERTIFICADOS Y ASIGNACION NIE (NO COMUNITARIOS)",
    ],
    "Madrid": TRAMITES_DEFAULT + [
        "EXPEDICIÓN/RENOVACIÓN DE DOCUMENTOS DE VIAJE",
        "CERTIFICADOS Y ASIGNACION NIE (NO COMUNITARIOS)",
        "RESGUARDO PRÓRROGA DE DERECHOS POR RESOLUCIÓN",
        "PRORROGA DE ESTANCIA CON VISADO",
        "PRORROGA DE ESTANCIA SIN VISADO",
    ],
    "Albacete": TRAMITES_DEFAULT + [
        "CERTIFICADOS Y ASIGNACION NIE (NO COMUNITARIOS)",
        "UCRANIA: SOLICITUD PROTECCIÓN TEMPORAL",
    ],
}

def get_tramites(provincia):
    return TRAMITES_EXTRA.get(provincia, TRAMITES_DEFAULT)

# Oficinas por provincia
OFICINAS = {
    "Madrid": [
        "OFICINA DE EXTRANJERÍA MADRID CENTRAL, C/ ADUANA, 27",
        "OFICINA DE EXTRANJERÍA MADRID SUR, AV. DE OPORTO, 40",
        "COMISARÍA MORATALAZ, C/ ARROYO DE LAS PILILLAS, 58",
    ],
    "Barcelona": [
        "OFICINA DE EXTRANJERÍA BARCELONA, AV. MARQUÈS DE L'ARGENTERA, 4",
        "OFICINA RAMBLA GUIPÚSCOA, 74",
        "CNP TARJETAS, LLEIDA",
    ],
    "Albacete": [
        "CNP TARJETAS Expedición, CALDERON DE LA BARCA, 2, ALBACETE",
        "CNP HELLIN, FORTUNATO ARIAS, 2, HELLIN",
    ],
    "Valencia": [
        "OFICINA EXTRANJERÍA VALENCIA, C/ BAILÉN, 9",
        "CNP TORRENT, AV. AL VEDAT, 45",
    ],
    "Sevilla": [
        "OFICINA EXTRANJERÍA SEVILLA, AV. REPÚBLICA ARGENTINA, 21",
    ],
    "Málaga": [
        "OFICINA EXTRANJERÍA MÁLAGA, EXPLANADA DE LA ESTACIÓN, S/N",
        "CNP MARBELLA, AV. JUAN GÓMEZ JUANITO, 4",
    ],
}
OFICINA_DEFAULT = ["OFICINA CENTRAL DE EXTRANJERÍA", "COMISARÍA PROVINCIAL"]

def get_oficinas(provincia):
    return OFICINAS.get(provincia, OFICINA_DEFAULT)

# ── HELPERS ─────────────────────────────────────────────────────────────────

active_searches: dict = {}

def province_keyboard():
    kb = []
    row = []
    for i, p in enumerate(PROVINCIAS):
        row.append(InlineKeyboardButton(p, callback_data=f"prov_{i}"))
        if len(row) == 3:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    return InlineKeyboardMarkup(kb)

def list_keyboard(items, prefix):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(t, callback_data=f"{prefix}_{i}")] for i, t in enumerate(items)]
    )

# ── HANDLERS ────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bienvenido a MiCitaBot!\n\n"
        "/nueva_busqueda - Buscar cita\n"
        "/mis_busquedas - Ver mis búsquedas\n"
        "/ayuda - Ayuda"
    )

async def nueva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🔍 Extranjería\n\nSelecciona la provincia:",
        reply_markup=province_keyboard()
    )
    return SELECT_PROVINCIA

async def sel_provincia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    idx = int(q.data.split("_")[1])
    provincia = PROVINCIAS[idx]
    context.user_data["provincia"] = provincia
    tramites = get_tramites(provincia)
    context.user_data["tramites_list"] = tramites
    await q.edit_message_text(
        f"📍 Provincia: {provincia}\n\nSelecciona el trámite:",
        reply_markup=list_keyboard(tramites, "tram")
    )
    return SELECT_TRAMITE

async def sel_tramite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    idx = int(q.data.split("_")[1])
    tramite = context.user_data["tramites_list"][idx]
    context.user_data["tramite"] = tramite
    provincia = context.user_data["provincia"]
    oficinas = get_oficinas(provincia)
    context.user_data["oficinas_list"] = oficinas
    kb_items = ["Cualquier oficina"] + oficinas
    await q.edit_message_text(
        f"📍 Provincia: {provincia}\n"
        f"🔍 Trámite: {tramite[:40]}\n\n"
        f"Selecciona la oficina:",
        reply_markup=list_keyboard(kb_items, "ofic")
    )
    return SELECT_OFICINA

async def sel_oficina(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    idx = int(q.data.split("_")[1])
    kb_items = ["Cualquier oficina"] + context.user_data["oficinas_list"]
    context.user_data["oficina"] = kb_items[idx]
    await q.edit_message_text("Escribe tu NIE o Pasaporte:")
    return ENTER_NIE

async def enter_nie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nie"] = update.message.text.upper()
    await update.message.reply_text("Nombre completo:")
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nombre"] = update.message.text
    await update.message.reply_text("Teléfono (+34...):")
    return ENTER_PHONE

async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["telefono"] = update.message.text
    d = context.user_data
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirmar y Monitorear", callback_data="yes")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="no")]
    ])
    await update.message.reply_text(
        f"📋 Confirma tus datos:\n\n"
        f"📍 Provincia: {d['provincia']}\n"
        f"🔍 Trámite: {d['tramite'][:50]}\n"
        f"🏢 Oficina: {d['oficina'][:50]}\n"
        f"🪪 NIE: {d['nie']}\n"
        f"👤 Nombre: {d['nombre']}\n"
        f"📱 Tel: {d['telefono']}",
        reply_markup=kb
    )
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "no":
        await q.edit_message_text("❌ Cancelado.")
        return ConversationHandler.END

    user_id = update.effective_user.id
    data = context.user_data.copy()

    if user_id not in active_searches:
        active_searches[user_id] = []
    search_id = len(active_searches[user_id]) + 1
    active_searches[user_id].append({"id": search_id, "data": data, "active": True})

    await q.edit_message_text(
        f"✅ Búsqueda #{search_id} iniciada!\n\n"
        f"🤖 Monitoreando ICP Clave cada 3 minutos.\n"
        f"📲 Te avisaré cuando haya cita disponible!\n\n"
        f"/mis_busquedas - Ver estado"
    )
    asyncio.create_task(monitor_icp(user_id, search_id, data, context.application.bot))
    return ConversationHandler.END

# ── MONITOR ─────────────────────────────────────────────────────────────────

async def monitor_icp(user_id: int, search_id: int, data: dict, bot):
    attempt = 0
    while True:
        attempt += 1
        try:
            searches = active_searches.get(user_id, [])
            search = next((s for s in searches if s["id"] == search_id), None)
            if not search or not search["active"]:
                break

            logger.info(f"Check ICP — user {user_id} search #{search_id} attempt {attempt}")
            available = await check_icp_availability(data)

            if available:
                await bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"🎉 ¡CITA DISPONIBLE!\n\n"
                        f"📍 Provincia: {data['provincia']}\n"
                        f"🔍 Trámite: {data['tramite'][:50]}\n"
                        f"🏢 Oficina: {data['oficina'][:50]}\n\n"
                        f"🔗 Ve AHORA a reservar:\n"
                        f"https://icp.administracionelectronica.gob.es/icpplus/index.html\n\n"
                        f"⚡ ¡Las citas se agotan rápido!"
                    )
                )
                search["active"] = False
                break
        except Exception as e:
            logger.error(f"Monitor error: {e}")
        await asyncio.sleep(180)

async def check_icp_availability(data: dict) -> bool:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(
                "https://icp.administracionelectronica.gob.es/icpplus/index.html",
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    for msg in ["no hay citas", "no existen", "no quedan"]:
                        if msg in text.lower():
                            return False
                    return True
    except Exception as e:
        logger.error(f"ICP check error: {e}")
    return False

# ── SEARCHES ────────────────────────────────────────────────────────────────

async def mis_busquedas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    searches = active_searches.get(user_id, [])
    if not searches:
        await update.message.reply_text("No hay búsquedas.\n/nueva_busqueda para empezar!")
        return
    text = "📋 Tus búsquedas:\n\n"
    kb = []
    for s in searches:
        status = "🟢 Activa" if s["active"] else "✅ Completada"
        text += f"#{s['id']} {status}\n{s['data']['provincia']} - {s['data']['tramite'][:30]}\n\n"
        if s["active"]:
            kb.append([InlineKeyboardButton(f"❌ Cancelar #{s['id']}", callback_data=f"cancel_{s['id']}")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb) if kb else None)

async def cancel_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    search_id = int(q.data.split("_")[1])
    for s in active_searches.get(user_id, []):
        if s["id"] == search_id:
            s["active"] = False
    await q.edit_message_text(f"✅ Búsqueda #{search_id} cancelada.")

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelado.")
    return ConversationHandler.END

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Ayuda:\n\n"
        "/nueva_busqueda - Iniciar nueva búsqueda de cita\n"
        "/mis_busquedas - Ver estado de búsquedas activas\n"
        "/ayuda - Mostrar esta ayuda\n\n"
        "El bot monitorea ICP Clave cada 3 minutos y te avisa cuando haya cita disponible."
    )

# ── MAIN ────────────────────────────────────────────────────────────────────

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("nueva_busqueda", nueva)],
        states={
            SELECT_PROVINCIA: [CallbackQueryHandler(sel_provincia, pattern=r"^prov_")],
            SELECT_TRAMITE:   [CallbackQueryHandler(sel_tramite,   pattern=r"^tram_")],
            SELECT_OFICINA:   [CallbackQueryHandler(sel_oficina,   pattern=r"^ofic_")],
            ENTER_NIE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_nie)],
            ENTER_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
            ENTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone)],
            CONFIRM:     [CallbackQueryHandler(confirm, pattern=r"^(yes|no)$")],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CommandHandler("mis_busquedas", mis_busquedas))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CallbackQueryHandler(cancel_cb, pattern=r"^cancel_"))

    app.run_polling()

if __name__ == "__main__":
    main()
