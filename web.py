import os
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

@app.route("/form")
def form():
    fecha_min = request.args.get("fecha_min", "")
    fecha_max = request.args.get("fecha_max", "")

    # Convert DD/MM/YYYY to YYYY-MM-DD for HTML date input
    def to_iso(d):
        if d and "/" in d:
            parts = d.split("/")
            if len(parts) == 3:
                return f"{parts[2]}-{parts[1]}-{parts[0]}"
        return d

    data = {
        "nie":          request.args.get("nie", ""),
        "nombre":       request.args.get("nombre", ""),
        "ano":          request.args.get("ano", ""),
        "pais":         request.args.get("pais", ""),
        "telefono":     request.args.get("telefono", ""),
        "email":        request.args.get("email", ""),
        "fecha_min":    fecha_min,
        "fecha_max":    fecha_max,
        "fecha_min_iso": to_iso(fecha_min),
        "fecha_max_iso": to_iso(fecha_max),
        "oficina":      request.args.get("oficina", ""),
        "tramite":      request.args.get("tramite", ""),
        "provincia":    request.args.get("provincia", ""),
    }
    return render_template("form.html", **data)

@app.route("/submit", methods=["POST"])
def submit():
    return jsonify({"status": "ok", "message": "Solicitud enviada correctamente"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
