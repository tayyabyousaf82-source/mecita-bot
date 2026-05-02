import os
import logging
import threading
from urllib.parse import urlencode
from flask import Flask, request as freq, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler
)
from data import PROVINCIA_DATA

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "8719883446:AAHBcWG_VNvxd25NTGWPrVC_TDPiP47UIzc"
BASE_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "mecita-bot-production.up.railway.app")

WAITING_PROVINCIA, WAITING_TRAMITE, WAITING_OFICINA = range(3)
SORTED_PROVINCIAS = sorted(PROVINCIA_DATA.items(), key=lambda x: x[1]["name"])

# ══ FLASK ══════════════════════════════════════════════════
flask_app = Flask(__name__)

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #fff; }
.topbar { background: #fff; padding: 14px 16px; border-bottom: 1px solid #e0e0e0; position: sticky; top: 0; z-index: 100; }
.topbar-title { font-size: 16px; font-weight: 600; color: #111; }
.topbar-sub { font-size: 11px; color: #1a73e8; margin-top: 2px; }
.section { padding: 16px; border-bottom: 1px solid #f0f0f0; }
.field-group { padding: 12px 16px; border-bottom: 1px solid #f0f0f0; }
.field-label { font-size: 13px; color: #333; margin-bottom: 8px; font-weight: 500; }
.req { color: #d32f2f; }
.radio-group { display: flex; flex-direction: column; gap: 10px; }
.radio-item { display: flex; align-items: center; gap: 10px; }
.radio-item input { width: 18px; height: 18px; accent-color: #1a73e8; }
.radio-item label { font-size: 14px; color: #333; }
.form-input { width: 100%; border: 1px solid #ccc; border-radius: 4px; padding: 10px 12px; font-size: 14px; color: #333; outline: none; }
.form-input:focus { border-color: #1a73e8; }
.form-select { width: 100%; border: 1px solid #ccc; border-radius: 4px; padding: 10px 12px; font-size: 14px; color: #333; outline: none; background: #fff; }
.date-field { display: flex; align-items: center; gap: 8px; border: 1px solid #ccc; border-radius: 4px; padding: 10px 12px; }
.date-field input { border: none; outline: none; font-size: 14px; color: #333; flex: 1; background: transparent; }
.oficina-tag { display: inline-flex; align-items: center; border: 1px solid #ccc; border-radius: 4px; padding: 6px 10px; font-size: 13px; color: #333; }
.cal-header { text-align: center; font-size: 14px; font-weight: 600; color: #333; padding: 8px 0; }
.cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; text-align: center; }
.cal-day-name { font-size: 11px; color: #888; padding: 4px 0; }
.cal-day { font-size: 13px; color: #333; padding: 8px 2px; cursor: pointer; border-radius: 50%; }
.cal-day:hover { background: #e8f0fe; }
.cal-day.empty { color: #ccc; cursor: default; }
.cal-day.excluded { background: #1a73e8; color: #fff; }
.form-textarea { width: 100%; border: 1px solid #ccc; border-radius: 4px; padding: 10px 12px; font-size: 14px; color: #333; outline: none; resize: vertical; min-height: 60px; font-family: inherit; }
.btn-section { padding: 16px; display: flex; flex-direction: column; gap: 10px; }
.btn { width: 100%; padding: 14px; border: none; border-radius: 6px; font-size: 15px; font-weight: 500; cursor: pointer; background: #1a73e8; color: #fff; }
.success-box { display: none; background: #e8f5e9; border: 1px solid #4caf50; border-radius: 8px; padding: 16px; margin: 16px; text-align: center; color: #2e7d32; font-size: 15px; }
"""

JS = """
const excl = new Set();
function renderCal() {
  const now = new Date(), y = now.getFullYear(), m = now.getMonth();
  const mn = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
  document.getElementById('cal_h').textContent = mn[m] + ' ' + y;
  const days = new Date(y, m+1, 0).getDate();
  const first = new Date(y, m, 1).getDay();
  const off = first === 0 ? 6 : first - 1;
  const g = document.getElementById('cal_g');
  g.innerHTML = '';
  ['lu','ma','mi','ju','vi','sá','do'].forEach(d => {
    const e = document.createElement('div'); e.className = 'cal-day-name'; e.textContent = d; g.appendChild(e);
  });
  for (let i = 0; i < off; i++) { const e = document.createElement('div'); e.className = 'cal-day empty'; g.appendChild(e); }
  for (let d = 1; d <= days; d++) {
    const e = document.createElement('div');
    e.className = 'cal-day' + (excl.has(d) ? ' excluded' : '');
    e.textContent = d;
    e.onclick = () => { excl.has(d) ? excl.delete(d) : excl.add(d); renderCal(); };
    g.appendChild(e);
  }
}
renderCal();
function enviar() {
  const nie = document.getElementById('nie_i').value.trim();
  const nom = document.getElementById('nom_i').value.trim();
  const ano = document.getElementById('ano_i').value.trim();
  const pais = document.getElementById('pais_i').value;
  const tel = document.getElementById('tel_i').value.trim();
  if (!nie || !nom || !ano || !pais || !tel) { alert('Por favor rellena todos los campos obligatorios (*)'); return; }
  const btn = document.getElementById('sbtn');
  btn.textContent = 'Enviando...'; btn.disabled = true;
  fetch('/submit', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      nie, nombre: nom, ano, pais, telefono: tel,
      email: document.getElementById('email_i').value,
      fecha_min: document.getElementById('fmin_i').value,
      fecha_max: document.getElementById('fmax_i').value,
      excluded_days: Array.from(excl),
      observaciones: document.getElementById('obs_i').value
    })
  })
  .then(r => r.json())
  .then(() => { document.getElementById('sbox').style.display='block'; btn.textContent='Enviado'; window.scrollTo(0,0); })
  .catch(() => { btn.textContent='Enviar solicitud'; btn.disabled=false; alert('Error al enviar.'); });
}
"""

PAISES = [
    "AFGANISTAN","ALBANIA","ALEMANIA","ARGELIA","ARGENTINA","BANGLADESH",
    "BOLIVIA","BRASIL","BULGARIA","CHINA","COLOMBIA","ECUADOR","EGIPTO",
    "ESTADOS UNIDOS","FILIPINAS","FRANCIA","GHANA","GUINEA","HONDURAS",
    "INDIA","INDONESIA","IRAQ","IRAN","ITALIA","MALI","MARRUECOS",
    "MAURITANIA","MEXICO","NIGERIA","PAKISTAN","PARAGUAY","PERU",
    "POLONIA","PORTUGAL","REINO UNIDO","REPUBLICA DOMINICANA","RUMANIA",
    "RUSIA","SENEGAL","SIRIA","UCRANIA","URUGUAY","VENEZUELA"
]

@flask_app.route("/form")
def form():
    get = freq.args.get
    nie      = get("nie", "")
    nombre   = get("nombre", "")
    ano      = get("ano", "")
    pais     = get("pais", "")
    telefono = get("telefono", "")
    email    = get("email", "")
    fmin_raw = get("fecha_min", "")
    fmax_raw = get("fecha_max", "")
    oficina  = get("oficina", "")
    tramite  = get("tramite", "")
    provincia= get("provincia", "")

    def to_iso(d):
        if d and "/" in d:
            p = d.split("/")
            if len(p) == 3:
                return "%s-%s-%s" % (p[2], p[1], p[0])
        return d

    fmin = to_iso(fmin_raw)
    fmax = to_iso(fmax_raw)

    opts = "\n".join(
        '<option value="%s" %s>%s</option>' % (p, "selected" if p == pais else "", p.title())
        for p in PAISES
    )

    html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Formulario ICP Clave</title>
<style>""" + CSS + """</style>
</head>
<body>
<div class="topbar">
  <div class="topbar-title">Formulario ICP Clave</div>
  <div class="topbar-sub">mecita-bot-production.up.railway.app</div>
</div>

<div class="section">
  <div style="font-size:13px;color:#555;margin-bottom:10px">Selecciona la(s) oficina(s)</div>
  <div class="oficina-tag">""" + oficina + """ &nbsp;&#x2715;</div>
  <div style="font-size:11px;color:#888;margin-top:6px">""" + provincia + """ &mdash; """ + tramite + """</div>
</div>

<div style="font-size:13px;color:#555;padding:12px 16px 4px;font-weight:500">
  Rellena los campos obligatorios <span class="req">*</span>
</div>

<div class="field-group">
  <div class="field-label">Tipo de documento <span class="req">*</span></div>
  <div class="radio-group">
    <div class="radio-item"><input type="radio" name="tipo" id="rnie" value="NIE" checked><label for="rnie">N.I.E.</label></div>
    <div class="radio-item"><input type="radio" name="tipo" id="rpas" value="PASAPORTE"><label for="rpas">PASAPORTE</label></div>
    <div class="radio-item"><input type="radio" name="tipo" id="rdni" value="DNI"><label for="rdni">D.N.I.</label></div>
  </div>
</div>

<div class="field-group">
  <div class="field-label">Número de documento <span class="req">*</span></div>
  <input class="form-input" type="text" id="nie_i" value=\"""" + nie + """\">
</div>

<div class="field-group">
  <div class="field-label">Nombre y apellidos <span class="req">*</span></div>
  <input class="form-input" type="text" id="nom_i" value=\"""" + nombre + """\">
</div>

<div class="field-group">
  <div class="field-label">Año de nacimiento <span class="req">*</span></div>
  <input class="form-input" type="number" id="ano_i" value=\"""" + ano + """\" min="1900" max="2010">
</div>

<div class="field-group">
  <div class="field-label">País de nacionalidad <span class="req">*</span></div>
  <select class="form-select" id="pais_i">
    <option value="">Seleccionar</option>
    """ + opts + """
  </select>
</div>

<div class="field-group">
  <div class="field-label">Teléfono <span class="req">*</span></div>
  <input class="form-input" type="tel" id="tel_i" value=\"""" + telefono + """\">
</div>

<div class="field-group">
  <div class="field-label">Correo electrónico</div>
  <div style="font-size:11px;color:#888;margin-bottom:8px">El justificante se enviará al correo especificado, deja el campo vacío para generar una dirección aleatoria</div>
  <input class="form-input" type="email" id="email_i" value=\"""" + email + """\">
</div>

<div class="field-group">
  <div class="field-label">Fecha mínima de la cita</div>
  <div class="date-field"><span>&#128197;</span><input type="date" id="fmin_i" value=\"""" + fmin + """\"></div>
</div>

<div class="field-group">
  <div class="field-label">Fecha maxima de la cita</div>
  <div class="date-field"><span>&#128197;</span><input type="date" id="fmax_i" value=\"""" + fmax + """\"></div>
</div>

<div class="field-group">
  <div class="field-label">No quiero que se reserve la cita estos días</div>
  <div class="cal-header" id="cal_h"></div>
  <div class="cal-grid" id="cal_g"></div>
</div>

<div class="field-group">
  <div class="field-label">Observaciones</div>
  <textarea class="form-textarea" id="obs_i"></textarea>
</div>

<div class="success-box" id="sbox">&#x2705; ¡Solicitud enviada correctamente!</div>

<div class="btn-section">
  <button class="btn" style="background:#1565c0" onclick="alert('No disponible en esta versión.')">Añadir certificados digitales</button>
  <button class="btn" id="sbtn" onclick="enviar()">Enviar solicitud</button>
</div>

<script>""" + JS + """</script>
</body>
</html>"""

    return html, 200, {"Content-Type": "text/html; charset=utf-8"}

@flask_app.route("/submit", methods=["POST"])
def submit():
    return jsonify({"status": "ok"})

@flask_app.route("/")
def home():
    return "MiCitaBot running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)

# ══ TELEGRAM BOT ═══════════════════════════════════════════
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
        row.append(InlineKeyboardButton(pdata0["name"], callback_data="prov_" + pid0))
        if i + 1 < len(SORTED_PROVINCIAS):
            pid1, pdata1 = SORTED_PROVINCIAS[i + 1]
            row.append(InlineKeyboardButton(pdata1["name"], callback_data="prov_" + pid1))
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
        [InlineKeyboardButton(nombre, callback_data="tram_" + code)]
        for code, nombre in pdata["tramites"].items()
    ]
    await query.edit_message_text(
        "📍 Provincia: *" + pdata["name"] + "*\n\n📋 *Paso 2/3* — Selecciona el *Trámite*:",
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
        [InlineKeyboardButton(oficinas[i], callback_data="ofic_" + str(i))]
        for i in range(len(oficinas))
    ]
    await query.edit_message_text(
        "📍 *" + context.user_data["provincia_name"] + "*\n📋 *" + tname + "*\n\n🏢 *Paso 3/3* — Selecciona la *Oficina*:",
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
    provincia = context.user_data["provincia_name"]
    tramite = context.user_data["tramite_name"]

    params = {"oficina": oficina, "tramite": tramite, "provincia": provincia}
    form_url = "https://" + BASE_URL + "/form?" + urlencode(params)

    keyboard = [[InlineKeyboardButton("📋 Abrir Formulario ICP Clave", url=form_url)]]
    await query.edit_message_text(
        "✅ *Selección completada:*\n\n"
        "📍 " + provincia + "\n"
        "📋 " + tramite + "\n"
        "🏢 " + oficina + "\n\n"
        "👇 *Abre el formulario y rellena tus datos:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    context.user_data.clear()
    return ConversationHandler.END

def main():
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    logger.info("Flask started")

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
    logger.info("Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
