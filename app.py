"""Interfaz web del scraper.

Uso:
    .venv/bin/python app.py        → http://localhost:5050
"""

import glob
import json
import os
import threading
import time
import uuid

from flask import Flask, abort, jsonify, request, send_file, send_from_directory

from src.exporter import OUTPUT_DIR
from src.pipeline import business_key, run_job


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "web"), static_url_path="/static")

JOBS = {}
LOCK = threading.Lock()


def new_job(params):
    return {
        "id": uuid.uuid4().hex[:10],
        "params": params,
        "status": "running",          # running | done | error | cancelled
        "phase": "inicio",
        "message": "Preparando navegador…",
        "query_index": 0,
        "query_total": 0,
        "loaded": 0,
        "detail_done": 0,
        "detail_total": 0,
        "web_done": 0,
        "web_total": 0,
        "log": [],
        "rows": {},
        "version": 0,
        "result": None,
        "error": "",
        "cancel": False,
        "started": time.time(),
        "finished": None,
    }


def run_in_background(job):

    def emit(kind, **data):
        with LOCK:
            job["version"] += 1
            if kind == "phase":
                job["phase"] = data["phase"]
                job["message"] = data["message"]
                job["query_index"] = data.get("query_index", job["query_index"])
                job["query_total"] = data.get("query_total", job["query_total"])
                job["log"].append({"t": time.time(), "level": "phase", "message": data["message"]})
            elif kind == "log":
                job["log"].append({"t": time.time(), "level": data.get("level", "info"),
                                   "message": data["message"]})
            elif kind == "scroll":
                job["loaded"] = data["loaded"]
            elif kind == "cards":
                job["detail_total"] = data["total"]
            elif kind == "business":
                job["rows"][data["key"]] = data["business"]
                job["detail_done"] = data["done"]
                job["detail_total"] = data["total"]
            elif kind == "web":
                job["rows"][data["key"]] = data["business"]
                job["web_done"] = data["done"]
                job["web_total"] = data["total"]

    def target():
        try:
            result = run_job(job["params"], emit=emit, is_cancelled=lambda: job["cancel"])
            with LOCK:
                job["result"] = {
                    "excel": os.path.basename(result["excel"]),
                    "summary": result["summary"],
                    "stats": result["stats"],
                }
                job["rows"] = {business_key(b): b for b in result["businesses"]}
                job["status"] = "cancelled" if result["stats"]["interrumpido"] else "done"
                job["phase"] = "fin"
                job["message"] = "Listo" if job["status"] == "done" else result["stats"]["interrumpido"]
        except Exception as error:
            with LOCK:
                job["status"] = "error"
                job["error"] = str(error)
                job["message"] = f"Error: {error}"
                job["log"].append({"t": time.time(), "level": "error", "message": str(error)})
        finally:
            with LOCK:
                job["finished"] = time.time()
                job["version"] += 1

    threading.Thread(target=target, daemon=True).start()


def public_job(job, since_log=0, include_rows=True):
    data = {k: v for k, v in job.items() if k not in ("rows", "cancel", "log")}
    data["log"] = job["log"][since_log:]
    data["log_total"] = len(job["log"])
    data["elapsed"] = int((job["finished"] or time.time()) - job["started"])
    if include_rows:
        rows = list(job["rows"].values())
        if job["result"]:
            rows.sort(key=lambda b: b.get("n", 0))
        data["rows"] = rows
    return data


# --------------------------------------------------------------------- rutas

@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.post("/api/jobs")
def create_job():
    body = request.get_json(force=True) or {}
    if not str(body.get("tipo", "")).strip() or not str(body.get("ubicacion", "")).strip():
        return jsonify({"error": "Indica el tipo de negocio y la ubicación."}), 400

    with LOCK:
        if any(j["status"] == "running" for j in JOBS.values()):
            return jsonify({"error": "Ya hay una búsqueda en curso. Espera o detenla."}), 409

    params = {
        "tipo": str(body.get("tipo", "")).strip(),
        "ubicacion": str(body.get("ubicacion", "")).strip(),
        "zonas": body.get("zonas", ""),
        "max_resultados": int(body.get("max_resultados") or 0),
        "concurrencia": int(body.get("concurrencia") or 3),
        "headless": not bool(body.get("ver_navegador")),
        "analizar_webs": bool(body.get("analizar_webs", True)),
        "rating_min": float(body.get("rating_min") or 0),
        "resenas_min": int(body.get("resenas_min") or 0),
        "solo_con_telefono": bool(body.get("solo_con_telefono")),
        "solo_sin_web": bool(body.get("solo_sin_web")),
        "excluir_cerrados": bool(body.get("excluir_cerrados", True)),
        "pais": str(body.get("pais") or "51"),
        "radio_km": float(body.get("radio_km") or 0),
    }
    job = new_job(params)
    with LOCK:
        JOBS[job["id"]] = job
    run_in_background(job)
    return jsonify({"id": job["id"]})


@app.get("/api/jobs/<job_id>")
def get_job(job_id):
    job = JOBS.get(job_id)
    if not job:
        abort(404)
    since = int(request.args.get("since_log", 0))
    known = int(request.args.get("version", -1))
    with LOCK:
        include_rows = known != job["version"]
        return jsonify(public_job(job, since, include_rows))


@app.post("/api/jobs/<job_id>/cancel")
def cancel_job(job_id):
    job = JOBS.get(job_id)
    if not job:
        abort(404)
    job["cancel"] = True
    return jsonify({"ok": True})


@app.get("/api/history")
def history():
    items = []
    for path in sorted(glob.glob(os.path.join(OUTPUT_DIR, "*.json")), key=os.path.getmtime, reverse=True):
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            items.append({
                "id": os.path.basename(path)[:-5],
                "tipo": data["params"].get("tipo", ""),
                "ubicacion": data["params"].get("ubicacion", ""),
                "fecha": data["stats"].get("fecha", ""),
                "total": data["summary"].get("total", 0),
                "sin_web": data["summary"].get("sin_web", 0),
                "excel": data.get("excel", ""),
                "parcial": bool(data["stats"].get("interrumpido")),
            })
        except Exception:
            continue
    # Excels antiguos (versión 1) que no tienen .json asociado.
    known = {i["excel"] for i in items}
    for path in sorted(glob.glob(os.path.join(OUTPUT_DIR, "*.xlsx")), key=os.path.getmtime, reverse=True):
        name = os.path.basename(path)
        if name not in known:
            items.append({"id": "", "tipo": name[:-5].replace("_", " "), "ubicacion": "",
                          "fecha": time.strftime("%d/%m/%Y %H:%M", time.localtime(os.path.getmtime(path))),
                          "total": None, "sin_web": None, "excel": name, "parcial": False})
    return jsonify(items)


@app.get("/api/history/<run_id>")
def history_item(run_id):
    path = os.path.join(OUTPUT_DIR, f"{os.path.basename(run_id)}.json")
    if not os.path.exists(path):
        abort(404)
    with open(path, encoding="utf-8") as fh:
        return jsonify(json.load(fh))


@app.get("/download/<path:name>")
def download(name):
    path = os.path.join(OUTPUT_DIR, os.path.basename(name))
    if not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True)


@app.post("/api/open-folder")
def open_folder():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.system(f'open "{OUTPUT_DIR}"')
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print(f"\n  Scraper de negocios → http://localhost:{port}\n")
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
