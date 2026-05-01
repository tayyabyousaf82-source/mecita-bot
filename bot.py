import os, logging, asyncio, aiohttp, urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                          MessageHandler, filters, ContextTypes, ConversationHandler)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── STATES ──────────────────────────────────────────────────────────────────
(SELECT_TYPE, SELECT_PROVINCIA, SELECT_TRAMITE,
 SELECT_OFICINA, ENTER_NIE, ENTER_NAME, ENTER_PHONE, CONFIRM) = range(8)

WEB_URL = os.environ.get("WEB_URL", "https://your-app.railway.app")

# ── DATA ────────────────────────────────────────────────────────────────────

TIPOS = [
    ("Extranjería 🇪🇸", "extranjeria"),
    ("Registro Civil ⚖️", "registro"),
    ("DGT 🚗", "dgt"),
    ("Homologaciones 🎓", "homologaciones"),
    ("SEPE 💼", "sepe"),
]

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

TRAMITES = {
    "default": [
        "SOLICITUD DE AUTORIZACIONES",
        "- RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO",
        "TARJETA CONFLICTO UCRANIA–ПОЛІЦІЯ",
        "-TOMA DE HUELLAS (EXPEDICIÓN DE TARJETA)",
        "-ASIGNACIÓN DE NIE",
        "-CARTA DE INVITACIÓN",
        "-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA UE",
        "-CERTIFICADOS (DE RESIDENCIA, DE NO RESIDENCIA)",
        "- CÉDULA DE INSCRIPCIÓN",
        "- UCRANIA : SOLICITUD PROTECCIÓN TEMPORAL",
        "-PRORROGA DE ESTANCIA",
        "-SOLICITUD TARJETA ROJA",
        "-DECLARACIÓN DE ENTRADA",
        "- RESGUARDO PRÓRROGA DE DERECHOS POR RESOLUCIÓN",
        "-CERTIFICADOS CONCORDANCIA",
        "- TÍTULOS DE VIAJE",
        "- EXPEDICIÓN/RENOVACIÓN DE DOCUMENTOS",
        "-CERTIFICADOS Y ASIGNACION NIE (NO COMUNITARIOS)",
        "- SOLICITUD DE APATRIDA",
        "- PRORROGA DE ESTANCIA CON VISADO",
        "- PRORROGA DE ESTANCIA SIN VISADO",
        "RENOVACIONES, PRÓRROGAS Y MODIFICACIONES",
    ],
    "Madrid": [
        "SOLICITUD DE AUTORIZACIONES",
        "- RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO",
        "TARJETA CONFLICTO UCRANIA–ПОЛІЦІЯ",
        "POLICÍA-TOMA DE HUELLAS (EXPEDICIÓN DE TARJETA) INICIAL, RENOVACIÓN, DUPLICADO Y LEY 14/2013",
        "-ASIGNACIÓN DE NIE",
        "-CARTA DE INVITACIÓN",
        "-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA UE",
        "-CERTIFICADOS (DE RESIDENCIA, DE NO RESIDENCIA)",
        "- CÉDULA DE INSCRIPCIÓN",
        "- UCRANIA : SOLICITUD PROTECCIÓN TEMPORAL",
        "-PRORROGA DE ESTANCIA",
        "-SOLICITUD TARJETA ROJA",
        "- RESGUARDO PRÓRROGA DE DERECHOS POR RESOLUCIÓN",
        "- PRORROGA DE ESTANCIA CON VISADO",
        "- PRORROGA DE ESTANCIA SIN VISADO",
        "RENOVACIONES, PRÓRROGAS Y MODIFICACIONES",
        "- SOLICITUD DE APATRIDA",
    ],
    "Barcelona": [
        "SOLICITUD DE AUTORIZACIONES",
        "- RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO",
        "TARJETA CONFLICTO UCRANIA–ПОЛІЦІЯ",
        "-TOMA DE HUELLAS (EXPEDICIÓN DE TARJETA)",
        "-ASIGNACIÓN DE NIE",
        "-CARTA DE INVITACIÓN",
        "-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA UE",
        "-CERTIFICADOS (DE RESIDENCIA, DE NO RESIDENCIA)",
        "- CÉDULA DE INSCRIPCIÓN",
        "- UCRANIA : SOLICITUD PROTECCIÓN TEMPORAL",
        "-PRORROGA DE ESTANCIA",
        "RENOVACIONES, PRÓRROGAS Y MODIFICACIONES",
        "- EXPEDICIÓN/RENOVACIÓN DE DOCUMENTOS",
        "-CERTIFICADOS Y ASIGNACION NIE (NO COMUNITARIOS)",
    ],
}

def get_tramites(provincia):
    return TRAMITES.get(provincia, TRAMITES["default"])

OFICINAS = {
    "Madrid": [
        "OFICINA DE EXTRANJERÍA MADRID, C/ ADUANA, 27, MADRID",
        "BRIGADA PROVINCIAL DOCUMENTACIÓN, C/ JULIAN GONZALEZ SEGADOR",
        "CNP MORATALAZ, C/ ARROYO DE LAS PILILLAS, 58, MADRID",
        "CNP CARABANCHEL, C/ GENERAL FANJUL, 8, MADRID",
        "CNP FUENCARRAL, C/ PINOS ALTA, 8, MADRID",
    ],
    "Barcelona": [
        "OFICINA DE EXTRANJERÍA BARCELONA, AV. MARQUÈS DE L'ARGENTERA, 4",
        "OFICINA RAMBLA GUIPÚSCOA, 74, BARCELONA",
        "CNP TARJETAS BARCELONA",
    ],
    "Albacete": [
        "CNP TARJETAS Expedición, CALDERON DE LA BARCA, 2, ALBACETE",
        "CNP HELLIN, FORTUNATO ARIAS, 2, HELLIN",
    ],
    "Cáceres": [
        "OFICINA DE EXTRANJERIA EN CACERES, C/Catedrático Emilio Díez, 4",
    ],
    "Ciudad Real": [
        "OFICINA DE EXTRANJERÍA, Carretera Porzuna, 1, Ciudad Real",
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
    "Alicante": [
        "OFICINA EXTRANJERÍA ALICANTE, C/ MÚSICO BRETÓN, 4",
        "CNP TORREVIEJA, C/ PADRE DAMIÁN, S/N",
    ],
    "Granada": [
        "OFICINA EXTRANJERÍA GRANADA, C/ GRAN VÍA DE COLÓN, 48",
    ],
}
OFICINA_DEFAULT = ["OFICINA CENTRAL DE EXTRANJERÍA", "COMISARÍA PROVINCIAL"]

def get_oficinas(provincia):
    return OFICINAS.get(provincia, OFICINA_DEFAULT)

active_searches: dict = {}

# ── KEYBOARDS ────────────────────────────────────────────────────────────────

def tipos_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data=f"tipo_{val}")]
        for label, val in TIPOS
    ])

def province_keyboard():
    kb, row = [], []
    for i, p in enumerate(PROVINCIAS):
        row.append(InlineKeyboardButton(p, callback_data=f"prov_{i}"))
        if len(row) == 3:
            kb.append(row); row = []
    if row: kb.append(row)
    return InlineKeyboardMarkup(kb)

def list_keyboard(items, prefix):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t, callback_data=f"{prefix}_{i}")]
        for i, t in enumerate(items)
    ])

# ── HANDLERS ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bienvenido a MiCitaBot!\n\n"
        "/nueva_busqueda - Nueva cita\n"
        "/mis_busquedas - Ver búsquedas\n"
        "/ayuda - Ayuda"
    )

async def nueva_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🔍 Select the type of appointment you need",
        reply_markup=tipos_keyboard()
    )
    return SELECT_TYPE

async def sel_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    tipo_val = q.data[5:]  # remove "tipo_"
    tipo_label = next((l for l, v in TIPOS if v == tipo_val), tipo_val)
    context.user_data["tipo"] = tipo_label
    await q.edit_message_text(
        f"🔍 {tipo_label}\n\nSelect the province",
        reply_markup=province_keyboard()
    )
    return SELECT_PROVINCIA

async def sel_provincia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    provincia = PROVINCIAS[int(q.data.split("_")[1])]
    context.user_data["provincia"] = provincia
    tramites = get_tramites(provincia)
    context.user_data["tramites_list"] = tramites
    tipo = context.user_data.get("tipo", "Extranjería")
    await q.edit_message_text(
        f"🔍 {tipo}\n\nSelect the procedure",
        reply_markup=list_keyboard(tramites, "tram")
    )
    return SELECT_TRAMITE

async def sel_tramite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    tramite = context.user_data["tramites_list"][int(q.data.split("_")[1])]
    context.user_data["tramite"] = tramite
    provincia = context.user_data["provincia"]
    oficinas = get_oficinas(provincia)
    context.user_data["oficinas_list"] = oficinas
    await q.edit_message_text(
        f"Province: {provincia}\nProcedure: {tramite[:50]}\n\nSelect the office",
        reply_markup=list_keyboard(oficinas, "ofic")
    )
    return SELECT_OFICINA

async def sel_oficina(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    oficinas = context.user_data["oficinas_list"]
    context.user_data["oficina"] = oficinas[int(q.data.split("_")[1])]
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
        [InlineKeyboardButton("✅ Confirmar", callback_data="confirm_yes")],
        [InlineKeyboardButton("❌ Cancelar",  callback_data="confirm_no")]
    ])
    await update.message.reply_text(
        f"Province: {d['provincia']}\n"
        f"Procedure: {d['tramite'][:60]}\n"
        f"Office: {d['oficina'][:60]}\n\n"
        f"NIE: {d['nie']}\n"
        f"Nombre: {d['nombre']}\n"
        f"Tel: {d['telefono']}",
        reply_markup=kb
    )
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "confirm_no":
        await q.edit_message_text("❌ Cancelado.")
        return ConversationHandler.END

    user_id = update.effective_user.id
    data = context.user_data.copy()

    if user_id not in active_searches:
        active_searches[user_id] = []
    search_id = len(active_searches[user_id]) + 1
    active_searches[user_id].append({"id": search_id, "data": data, "active": True})

    params = urllib.parse.urlencode({
        "uid": user_id, "sid": search_id,
        "oficina": data["oficina"],
        "provincia": data["provincia"],
        "tramite": data["tramite"],
        "nie": data["nie"],
        "nombre": data["nombre"],
        "tel": data["telefono"],
    })
    form_url = f"{WEB_URL}/form?{params}"

    await q.edit_message_text(
        f"Province: {data['provincia']}\n"
        f"Procedure: {data['tramite'][:60]}\n"
        f"Office: {data['oficina'][:60]}\n\n"
        f"🔍 Fill this form to complete the process of request "
        f"(valid link for 24h)\n\n"
        f"{form_url}"
    )
    asyncio.create_task(monitor_icp(user_id, search_id, data, context.application.bot))
    return ConversationHandler.END

# ── MONITOR ──────────────────────────────────────────────────────────────────

async def monitor_icp(user_id, search_id, data, bot):
    attempt = 0
    while True:
        attempt += 1
        try:
            search = next((s for s in active_searches.get(user_id, [])
                           if s["id"] == search_id), None)
            if not search or not search["active"]:
                break
            logger.info(f"ICP check user={user_id} #{search_id} attempt={attempt}")
            if await check_icp():
                await bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"🎉 ¡CITA DISPONIBLE!\n\n"
                        f"📍 {data['provincia']}\n"
                        f"🔍 {data['tramite'][:50]}\n"
                        f"🏢 {data['oficina'][:50]}\n\n"
                        f"🔗 Ve AHORA:\n"
                        f"https://icp.administracionelectronica.gob.es/icpplus/index.html\n\n"
                        f"⚡ ¡Las citas se agotan rápido!"
                    )
                )
                search["active"] = False
                break
        except Exception as e:
            logger.error(f"Monitor error: {e}")
        await asyncio.sleep(180)

async def check_icp() -> bool:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        async with aiohttp.ClientSession(headers=headers) as s:
            async with s.get(
                "https://icp.administracionelectronica.gob.es/icpplus/index.html",
                timeout=aiohttp.ClientTimeout(total=15)
            ) as r:
                if r.status == 200:
                    t = await r.text()
                    for m in ["no hay citas", "no existen", "no quedan"]:
                        if m in t.lower(): return False
                    return True
    except Exception as e:
        logger.error(f"ICP error: {e}")
    return False

# ── OTHER COMMANDS ────────────────────────────────────────────────────────────

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
    sid = int(q.data.split("_")[1])
    for s in active_searches.get(user_id, []):
        if s["id"] == sid: s["active"] = False
    await q.edit_message_text(f"✅ Búsqueda #{sid} cancelada.")

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelado.")
    return ConversationHandler.END

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Comandos:\n\n"
        "/nueva_busqueda - Nueva búsqueda\n"
        "/mis_busquedas - Ver búsquedas activas\n"
        "/ayuda - Ayuda\n\n"
        "Bot monitorea cada 3 minutos y avisa cuando hay cita."
    )

# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("nueva_busqueda", nueva_cmd)],
        states={
            SELECT_TYPE:      [CallbackQueryHandler(sel_type,     pattern=r"^tipo_")],
            SELECT_PROVINCIA: [CallbackQueryHandler(sel_provincia, pattern=r"^prov_")],
            SELECT_TRAMITE:   [CallbackQueryHandler(sel_tramite,  pattern=r"^tram_")],
            SELECT_OFICINA:   [CallbackQueryHandler(sel_oficina,  pattern=r"^ofic_")],
            ENTER_NIE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_nie)],
            ENTER_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
            ENTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone)],
            CONFIRM:     [CallbackQueryHandler(confirm, pattern=r"^confirm_")],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CommandHandler("mis_busquedas", mis_busquedas))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CallbackQueryHandler(cancel_cb, pattern=r"^cancel_"))

    logger.info("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
