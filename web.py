import os
from flask import Flask, request

app = Flask(__name__)

@app.route("/form")
def form():
    nie       = request.args.get("nie", "")
    nombre    = request.args.get("nombre", "")
    ano       = request.args.get("ano", "")
    pais      = request.args.get("pais", "")
    telefono  = request.args.get("telefono", "")
    email     = request.args.get("email", "")
    fecha_min = request.args.get("fecha_min", "")
    fecha_max = request.args.get("fecha_max", "")
    oficina   = request.args.get("oficina", "")
    tramite   = request.args.get("tramite", "")
    provincia = request.args.get("provincia", "")

    def to_iso(d):
        if d and "/" in d:
            p = d.split("/")
            if len(p) == 3:
                return f"{p[2]}-{p[1]}-{p[0]}"
        return d

    fmin = to_iso(fecha_min)
    fmax = to_iso(fecha_max)

    paises_options = ""
    paises = ["AFGANISTAN","ALBANIA","ALEMANIA","ARGELIA","ARGENTINA","BANGLADESH",
              "BOLIVIA","BRASIL","BULGARIA","CHINA","COLOMBIA","ECUADOR","EGIPTO",
              "ESTADOS UNIDOS","FILIPINAS","FRANCIA","GHANA","GUINEA","HONDURAS",
              "INDIA","INDONESIA","IRAQ","IRAN","ITALIA","MALI","MARRUECOS",
              "MAURITANIA","MEXICO","NIGERIA","PAKISTAN","PARAGUAY","PERU",
              "POLONIA","PORTUGAL","REINO UNIDO","REPUBLICA DOMINICANA","RUMANIA",
              "RUSIA","SENEGAL","SIRIA","UCRANIA","URUGUAY","VENEZUELA"]
    for p in paises:
        sel = "selected" if p == pais else ""
        paises_options += f'<option value="{p}" {sel}>{p.title()}</option>'

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Formulario ICP Clave</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#fff;min-height:100vh}}
.topbar{{background:#fff;padding:14px 16px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #e0e0e0;position:sticky;top:0;z-index:100}}
.topbar-title{{font-size:16px;font-weight:600;color:#111}}
.topbar-sub{{font-size:11px;color:#1a73e8;margin-top:2px}}
.field-group{{padding:12px 16px;border-bottom:1px solid #f0f0f0}}
.field-label{{font-size:13px;color:#333;margin-bottom:8px;font-weight:500}}
.field-label span{{color:#d32f2f}}
.radio-group{{display:flex;flex-direction:column;gap:10px}}
.radio-item{{display:flex;align-items:center;gap:10px}}
.radio-item input{{width:18px;height:18px;accent-color:#1a73e8}}
.radio-item label{{font-size:14px;color:#333}}
.form-input{{width:100%;border:1px solid #ccc;border-radius:4px;padding:10px 12px;font-size:14px;color:#333;background:#fff;outline:none}}
.form-input:focus{{border-color:#1a73e8}}
.form-select{{width:100%;border:1px solid #ccc;border-radius:4px;padding:10px 12px;font-size:14px;color:#333;background:#fff;outline:none}}
.date-field{{display:flex;align-items:center;gap:8px;border:1px solid #ccc;border-radius:4px;padding:10px 12px;background:#fff}}
.date-field input[type=date]{{border:none;outline:none;font-size:14px;color:#333;background:transparent;flex:1}}
.section{{padding:16px;border-bottom:1px solid #f0f0f0}}
.oficina-tag{{display:inline-flex;align-items:center;border:1px solid #ccc;border-radius:4px;padding:6px 10px;font-size:13px;color:#333}}
.required-notice{{font-size:13px;color:#555;padding:12px 16px 4px;font-weight:500}}
.required-notice span{{color:#d32f2f}}
.cal-header{{text-align:center;font-size:14px;font-weight:600;color:#333;padding:8px 0}}
.cal-grid{{display:grid;grid-template-columns:repeat(7,1fr);gap:2px;text-align:center}}
.cal-day-name{{font-size:11px;color:#888;padding:4px 0}}
.cal-day{{font-size:13px;color:#333;padding:8px 4px;cursor:pointer;border-radius:50%}}
.cal-day:hover{{background:#e8f0fe}}
.cal-day.empty{{color:#ccc;cursor:default}}
.cal-day.excluded{{background:#1a73e8;color:#fff}}
.form-textarea{{width:100%;border:1px solid #ccc;border-radius:4px;padding:10px 12px;font-size:14px;color:#333;outline:none;resize:vertical;min-height:60px;font-family:inherit}}
.btn-section{{padding:16px;display:flex;flex-direction:column;gap:10px}}
.btn{{width:100%;padding:14px;border:none;border-radius:6px;font-size:15px;font-weight:500;cursor:pointer;background:#1a73e8;color:#fff}}
.btn:hover{{background:#1558b0}}
.success-box{{display:none;background:#e8f5e9;border:1px solid #4caf50;border-radius:8px;padding:16px;margin:16px;text-align:center;color:#2e7d32;font-size:15px;font-weight:500}}
</style>
</head>
<body>

<div class="topbar">
  <div>
    <div class="topbar-title">Formulario ICP Clave</div>
    <div class="topbar-sub">mecita-bot-production.up.railway.app</div>
  </div>
</div>

<div class="section">
  <div style="font-size:13px;color:#555;margin-bottom:10px">Selecciona la(s) oficina(s)</div>
  <div class="oficina-tag">{oficina} &nbsp; ✕</div>
  <div style="font-size:11px;color:#888;margin-top:6px">{provincia} &mdash; {tramite}</div>
</div>

<div class="required-notice">Rellena los campos obligatorios <span>*</span></div>

<div class="field-group">
  <div class="field-label">Tipo de documento <span>*</span></div>
  <div class="radio-group">
    <div class="radio-item">
      <input type="radio" name="tipo_doc" id="r_nie" value="NIE" checked>
      <label for="r_nie">N.I.E.</label>
    </div>
    <div class="radio-item">
      <input type="radio" name="tipo_doc" id="r_pas" value="PASAPORTE">
      <label for="r_pas">PASAPORTE</label>
    </div>
    <div class="radio-item">
      <input type="radio" name="tipo_doc" id="r_dni" value="DNI">
      <label for="r_dni">D.N.I.</label>
    </div>
  </div>
</div>

<div class="field-group">
  <div class="field-label">Número de documento <span>*</span></div>
  <input class="form-input" type="text" id="nie_input" value="{nie}" placeholder="">
  <div id="nie_err" style="font-size:12px;color:#d32f2f;margin-top:4px;display:none">Introduce un documento valido</div>
</div>

<div class="field-group">
  <div class="field-label">Nombre y apellidos <span>*</span></div>
  <input class="form-input" type="text" id="nombre_input" value="{nombre}" placeholder="">
</div>

<div class="field-group">
  <div class="field-label">Año de nacimiento <span>*</span></div>
  <input class="form-input" type="number" id="ano_input" value="{ano}" min="1900" max="2010">
</div>

<div class="field-group">
  <div class="field-label">País de nacionalidad <span>*</span></div>
  <select class="form-select" id="pais_select">
    <option value="">Seleccionar</option>
    {paises_options}
  </select>
</div>

<div class="field-group">
  <div class="field-label">Teléfono <span>*</span></div>
  <input class="form-input" type="tel" id="tel_input" value="{telefono}">
</div>

<div class="field-group">
  <div class="field-label">Correo electrónico</div>
  <div style="font-size:11px;color:#888;margin-bottom:8px">El justificante se enviará al correo especificado, deja el campo vacío para generar una dirección aleatoria</div>
  <input class="form-input" type="email" id="email_input" value="{email}">
</div>

<div class="field-group">
  <div class="field-label">Fecha mínima de la cita</div>
  <div class="date-field">
    <span>📅</span>
    <input type="date" id="fmin_input" value="{fmin}">
  </div>
</div>

<div class="field-group">
  <div class="field-label">Fecha maxima de la cita</div>
  <div class="date-field">
    <span>📅</span>
    <input type="date" id="fmax_input" value="{fmax}">
  </div>
</div>

<div class="field-group">
  <div class="field-label">No quiero que se reserve la cita estos días</div>
  <div class="cal-header" id="cal_header"></div>
  <div class="cal-grid" id="cal_grid"></div>
</div>

<div class="field-group">
  <div class="field-label">Observaciones</div>
  <textarea class="form-textarea" id="obs_input"></textarea>
</div>

<div class="success-box" id="success_box">✅ ¡Solicitud enviada correctamente!</div>

<div class="btn-section">
  <button class="btn" style="background:#1a73e8" onclick="addCert()">Añadir certificados digitales</button>
  <button class="btn" id="submit_btn" onclick="enviar()">Enviar solicitud</button>
</div>

<script>
const excluded = new Set();
function renderCal() {{
  const now = new Date();
  const y = now.getFullYear(), m = now.getMonth();
  const names = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
  document.getElementById('cal_header').textContent = names[m] + ' ' + y;
  const days = new Date(y, m+1, 0).getDate();
  const first = new Date(y, m, 1).getDay();
  const offset = first === 0 ? 6 : first - 1;
  const grid = document.getElementById('cal_grid');
  grid.innerHTML = '';
  ['lu','ma','mi','ju','vi','sá','do'].forEach(d => {{
    const el = document.createElement('div');
    el.className = 'cal-day-name';
    el.textContent = d;
    grid.appendChild(el);
  }});
  for(let i=0;i<offset;i++) {{
    const el = document.createElement('div');
    el.className = 'cal-day empty';
    grid.appendChild(el);
  }}
  for(let d=1;d<=days;d++) {{
    const el = document.createElement('div');
    el.className = 'cal-day' + (excluded.has(d) ? ' excluded' : '');
    el.textContent = d;
    el.onclick = () => {{ excluded.has(d)?excluded.delete(d):excluded.add(d); renderCal(); }};
    grid.appendChild(el);
  }}
}}
renderCal();

function addCert() {{ alert('Función no disponible en esta versión.'); }}

function enviar() {{
  const nie = document.getElementById('nie_input').value.trim();
  const nombre = document.getElementById('nombre_input').value.trim();
  const ano = document.getElementById('ano_input').value.trim();
  const pais = document.getElementById('pais_select').value;
  const tel = document.getElementById('tel_input').value.trim();
  if(!nie||!nombre||!ano||!pais||!tel) {{
    alert('Por favor rellena todos los campos obligatorios (*)');
    return;
  }}
  const btn = document.getElementById('submit_btn');
  btn.textContent = 'Enviando...';
  btn.disabled = true;
  fetch('/submit', {{
    method:'POST',
    headers:{{'Content-Type':'application/json'}},
    body: JSON.stringify({{
      nie, nombre, ano, pais,
      telefono: tel,
      email: document.getElementById('email_input').value,
      fecha_min: document.getElementById('fmin_input').value,
      fecha_max: document.getElementById('fmax_input').value,
      oficina: '{oficina}',
      tramite: '{tramite}',
      provincia: '{provincia}',
      excluded_days: Array.from(excluded),
      observaciones: document.getElementById('obs_input').value
    }})
  }})
  .then(r=>r.json())
  .then(() => {{
    document.getElementById('success_box').style.display='block';
    btn.textContent='✅ Enviado';
    window.scrollTo(0,0);
  }})
  .catch(() => {{
    btn.textContent='Enviar solicitud';
    btn.disabled=false;
    alert('Error al enviar. Inténtalo de nuevo.');
  }});
}}
</script>
</body>
</html>"""

    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route("/submit", methods=["POST"])
def submit():
    from flask import jsonify
    return jsonify({"status": "ok", "message": "Solicitud enviada correctamente"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
