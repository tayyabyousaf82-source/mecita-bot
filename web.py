import os
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

FORM_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Formulario ICP Clave</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Arial, sans-serif; background: #f5f5f5; padding: 16px; }
.container { max-width: 500px; margin: 0 auto; background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
h2 { font-size: 18px; color: #333; margin-bottom: 20px; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }
.section { margin-bottom: 16px; }
label { display: block; font-size: 13px; color: #555; margin-bottom: 4px; font-weight: bold; }
label .req { color: red; }
input[type=text], input[type=email], input[type=tel], input[type=number], select, textarea {
  width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px;
}
input:focus, select:focus { outline: none; border-color: #1a73e8; }
.radio-group { display: flex; gap: 20px; margin-top: 6px; }
.radio-group label { font-weight: normal; display: flex; align-items: center; gap: 6px; font-size: 14px; }
.oficina-box { background: #e8f0fe; border: 1px solid #1a73e8; border-radius: 4px; padding: 10px; font-size: 13px; color: #1a73e8; margin-bottom: 16px; }
.date-row { display: flex; gap: 10px; }
.date-row .section { flex: 1; }
.calendar { border: 1px solid #ddd; border-radius: 4px; padding: 10px; margin-top: 8px; }
.calendar h4 { text-align: center; font-size: 14px; margin-bottom: 8px; }
.cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; text-align: center; }
.cal-grid .day-name { font-size: 11px; color: #888; font-weight: bold; padding: 2px; }
.cal-grid .day { font-size: 12px; padding: 6px 2px; border-radius: 4px; cursor: pointer; }
.cal-grid .day:hover { background: #e8f0fe; }
.cal-grid .day.excluded { background: #ffcccc; color: #cc0000; border-radius: 4px; }
.cal-grid .day.empty { cursor: default; }
.btn { display: block; width: 100%; padding: 14px; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 10px; }
.btn-primary { background: #1a73e8; color: white; }
.btn-secondary { background: #f0f0f0; color: #333; margin-top: 8px; }
.btn:hover { opacity: 0.9; }
.success { display: none; text-align: center; padding: 30px 20px; }
.success .icon { font-size: 48px; margin-bottom: 10px; }
.success h3 { color: #2e7d32; font-size: 20px; }
.success p { color: #555; margin-top: 8px; font-size: 14px; }
</style>
</head>
<body>
<div class="container">
  <div id="formSection">
    <h2>📋 Formulario ICP Clave</h2>

    <div class="oficina-box" id="oficinaBox">
      🏢 Cargando oficina...
    </div>

    <div class="section">
      <label>Tipo de documento <span class="req">*</span></label>
      <div class="radio-group">
        <label><input type="radio" name="tipo_doc" value="NIE" checked> N.I.E.</label>
        <label><input type="radio" name="tipo_doc" value="PASAPORTE"> PASAPORTE</label>
        <label><input type="radio" name="tipo_doc" value="DNI"> D.N.I.</label>
      </div>
    </div>

    <div class="section">
      <label>Número de documento <span class="req">*</span></label>
      <input type="text" id="num_doc" placeholder="Ej: X1234567A">
      <small id="doc_error" style="color:red;display:none">Introduce un documento válido</small>
    </div>

    <div class="section">
      <label>Nombre y apellidos <span class="req">*</span></label>
      <input type="text" id="nombre" placeholder="Nombre completo">
    </div>

    <div class="section">
      <label>Año de nacimiento <span class="req">*</span></label>
      <input type="number" id="anio" placeholder="Ej: 1990" min="1920" max="2010">
    </div>

    <div class="section">
      <label>País de nacionalidad <span class="req">*</span></label>
      <select id="pais">
        <option value="">Seleccionar</option>
        <option>Pakistán</option>
        <option>Marruecos</option>
        <option>Colombia</option>
        <option>Ecuador</option>
        <option>Venezuela</option>
        <option>China</option>
        <option>Ucrania</option>
        <option>Rumanía</option>
        <option>Bolivia</option>
        <option>Perú</option>
        <option>India</option>
        <option>Bangladesh</option>
        <option>Argelia</option>
        <option>Senegal</option>
        <option>Nigeria</option>
        <option>Otro</option>
      </select>
    </div>

    <div class="section">
      <label>Teléfono <span class="req">*</span></label>
      <input type="tel" id="telefono" placeholder="+34...">
    </div>

    <div class="section">
      <label>Correo electrónico</label>
      <small style="color:#888;display:block;margin-bottom:4px">El justificante se enviará al correo especificado. Deja vacío para generar dirección aleatoria.</small>
      <input type="email" id="email" placeholder="opcional">
    </div>

    <div class="date-row">
      <div class="section">
        <label>Fecha mínima de la cita</label>
        <input type="date" id="fecha_min" value="2026-05-01">
      </div>
      <div class="section">
        <label>Fecha máxima de la cita</label>
        <input type="date" id="fecha_max" value="2026-10-28">
      </div>
    </div>

    <div class="section">
      <label>No quiero que se reserve la cita estos días</label>
      <div class="calendar">
        <h4 id="cal_title"></h4>
        <div class="cal-grid" id="cal_grid"></div>
      </div>
    </div>

    <div class="section">
      <label>Observaciones</label>
      <textarea id="obs" rows="3" placeholder="Opcional..."></textarea>
    </div>

    <button class="btn btn-secondary" onclick="addCert()">📎 Añadir certificados digitales</button>
    <button class="btn btn-primary" onclick="enviar()">📨 Enviar solicitud</button>
  </div>

  <div class="success" id="successSection">
    <div class="icon">✅</div>
    <h3>¡Solicitud enviada!</h3>
    <p>El bot monitoreará ICP Clave y te avisará por Telegram cuando haya cita disponible.</p>
    <p style="margin-top:12px;font-size:12px;color:#888">Puedes cerrar esta ventana.</p>
  </div>
</div>

<script>
const params = new URLSearchParams(window.location.search);
const oficina = params.get('oficina') || 'Oficina seleccionada';
const provincia = params.get('provincia') || '';
const tramite = params.get('tramite') || '';
const nie_pre = params.get('nie') || '';
const nombre_pre = params.get('nombre') || '';
const tel_pre = params.get('tel') || '';
const user_id = params.get('uid') || '';
const search_id = params.get('sid') || '';

document.getElementById('oficinaBox').textContent = '🏢 ' + oficina;
if (nie_pre) document.getElementById('num_doc').value = nie_pre;
if (nombre_pre) document.getElementById('nombre').value = nombre_pre;
if (tel_pre) document.getElementById('telefono').value = tel_pre;

// Calendar
const excludedDays = new Set();
const now = new Date();
let calYear = now.getFullYear();
let calMonth = now.getMonth();

function renderCal() {
  const months = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
  document.getElementById('cal_title').textContent = months[calMonth] + ' ' + calYear;
  const grid = document.getElementById('cal_grid');
  grid.innerHTML = '';
  ['lu','ma','mi','ju','vi','sá','do'].forEach(d => {
    const el = document.createElement('div');
    el.className = 'day-name'; el.textContent = d; grid.appendChild(el);
  });
  const first = new Date(calYear, calMonth, 1).getDay();
  const offset = (first === 0) ? 6 : first - 1;
  for (let i = 0; i < offset; i++) {
    const el = document.createElement('div'); el.className = 'day empty'; grid.appendChild(el);
  }
  const days = new Date(calYear, calMonth + 1, 0).getDate();
  for (let d = 1; d <= days; d++) {
    const key = calYear + '-' + String(calMonth+1).padStart(2,'0') + '-' + String(d).padStart(2,'0');
    const el = document.createElement('div');
    el.className = 'day' + (excludedDays.has(key) ? ' excluded' : '');
    el.textContent = d;
    el.onclick = () => {
      if (excludedDays.has(key)) excludedDays.delete(key); else excludedDays.add(key);
      renderCal();
    };
    grid.appendChild(el);
  }
}
renderCal();

function addCert() { alert('Función de certificados digitales próximamente.'); }

function enviar() {
  const num = document.getElementById('num_doc').value.trim();
  const nom = document.getElementById('nombre').value.trim();
  const anio = document.getElementById('anio').value.trim();
  const pais = document.getElementById('pais').value;
  const tel = document.getElementById('telefono').value.trim();
  if (!num || !nom || !anio || !pais || !tel) { alert('Por favor rellena todos los campos obligatorios (*)'); return; }

  const data = {
    user_id, search_id, oficina, provincia, tramite,
    tipo_doc: document.querySelector('input[name=tipo_doc]:checked').value,
    num_doc: num, nombre: nom, anio_nacimiento: anio,
    pais_nacionalidad: pais, telefono: tel,
    email: document.getElementById('email').value.trim(),
    fecha_min: document.getElementById('fecha_min').value,
    fecha_max: document.getElementById('fecha_max').value,
    excluded_days: Array.from(excludedDays),
    observaciones: document.getElementById('obs').value.trim()
  };

  fetch('/submit', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data) })
    .then(r => r.json())
    .then(res => {
      document.getElementById('formSection').style.display = 'none';
      document.getElementById('successSection').style.display = 'block';
    })
    .catch(() => alert('Error al enviar. Intenta de nuevo.'));
}
</script>
</body>
</html>"""

@app.route("/form")
def form():
    return render_template_string(FORM_HTML)

@app.route("/submit", methods=["POST"])
def submit():
    data = request.json
    # Store submission (in production use DB)
    print(f"Form submitted: {data}")
    # You can notify via Telegram bot here
    return jsonify({"ok": True})

@app.route("/health")
def health():
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
