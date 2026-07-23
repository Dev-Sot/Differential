"""
MEDI-IA — Flask Application v4 (ReAct Agent)
"""

import sys
import os
import uuid
import json
import hmac
import functools
import logging
import time
import threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, jsonify, session, Response, stream_with_context, redirect, url_for, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from src.agent import run, get_health
from src.schemas import ConsultaRequest, ErrorResponse
from src.memory import clear_session, save_feedback, get_feedback_stats, get_history
from src import metrics as metrics_mod
from src.pdf_export import build_diagnosis_pdf, build_conversation_pdf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("medi-ia")


# ── Cron de limpieza de sesiones inactivas ────────────────────────────────────
def _start_cleanup_cron() -> None:
    days       = int(os.getenv("CLEANUP_DAYS", "30"))
    interval_s = int(os.getenv("CLEANUP_INTERVAL_HOURS", "24")) * 3600

    def _loop():
        while True:
            time.sleep(interval_s)
            try:
                from src.memory import cleanup_old_sessions
                n = cleanup_old_sessions(days=days)
                log.info("cleanup_cron removed=%d sessions older_than=%d_days", n, days)
            except Exception as exc:
                log.error("cleanup_cron error=%s", exc)

    t = threading.Thread(target=_loop, name="cleanup-cron", daemon=True)
    t.start()
    log.info("cleanup_cron started interval_h=%d days_threshold=%d", interval_s // 3600, days)


_SECRET_KEY = os.getenv("SECRET_KEY", "")
if not _SECRET_KEY:
    if os.getenv("FLASK_DEBUG", "False").lower() == "true":
        _SECRET_KEY = os.urandom(24).hex()
        log.warning("SECRET_KEY no definida — usando una aleatoria (solo valido en modo debug local)")
    else:
        raise RuntimeError(
            "SECRET_KEY no esta definida. Es obligatoria fuera de FLASK_DEBUG=True: "
            "sin ella, cada reinicio del proceso invalida todas las sesiones activas. "
            "Genera una con: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

app = Flask(__name__)
app.secret_key = _SECRET_KEY
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.before_request
def _before_request():
    g.rid = str(uuid.uuid4())[:8]
    g.t0 = time.monotonic()


@app.after_request
def _after_request(response):
    elapsed_ms = int((time.monotonic() - g.get("t0", time.monotonic())) * 1000)
    rid = g.get("rid", "-")
    log.info("rid=%s %s %s %d %dms", rid, request.method, request.path, response.status_code, elapsed_ms)
    return response

_REDIS_URL = os.getenv("REDIS_URL", "")
if not _REDIS_URL:
    log.warning(
        "REDIS_URL no definida — el rate limiter usa memoria de proceso. "
        "Con gunicorn.conf.py (workers=2) cada worker lleva su propio contador: "
        "un cliente puede obtener hasta el doble del limite anunciado repartiendo "
        "requests entre workers. Ver docker-compose.yml para el servicio redis."
    )

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=_REDIS_URL or "memory://",
)

AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "")


def require_auth(f):
    """Decorator: exige sesion autenticada si AUTH_PASSWORD esta definida."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if AUTH_PASSWORD and not session.get("authenticated"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "No autenticado. Inicia sesion en /login"}), 401
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


def _get_session_id() -> str:
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]


@app.route("/login", methods=["GET"])
def login_page():
    if not AUTH_PASSWORD or session.get("authenticated"):
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def auth_login():
    data = request.get_json()
    password = (data or {}).get("password", "")
    if not AUTH_PASSWORD:
        session["authenticated"] = True
        return jsonify({"ok": True})
    if hmac.compare_digest(password, AUTH_PASSWORD):
        session["authenticated"] = True
        log.info("rid=%s auth_ok ip=%s", g.rid, request.remote_addr)
        return jsonify({"ok": True})
    log.warning("rid=%s auth_fail ip=%s", g.rid, request.remote_addr)
    return jsonify({"error": "Contraseña incorrecta"}), 401


@app.route("/auth/logout", methods=["POST"])
def auth_logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/")
@require_auth
def index():
    return render_template("index.html")


@app.route("/api/query", methods=["POST"])
@require_auth
@limiter.limit("10 per minute")
def query_agent():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify(ErrorResponse(error="No se proporciono mensaje").model_dump()), 400

    try:
        consulta = ConsultaRequest(message=data["message"])
    except Exception as e:
        return jsonify(ErrorResponse(error=str(e)).model_dump()), 400

    session_id = _get_session_id()
    t_inf = time.monotonic()
    try:
        result = run(consulta.message, session_id=session_id)
    except FileNotFoundError:
        log.error("rid=%s faiss_index_missing", g.rid)
        metrics_mod.record_error()
        return jsonify({
            "success": False,
            "error": "Base de conocimiento no disponible. Ejecuta 'make ingest' para construir el indice FAISS.",
        }), 503
    inf_ms = int((time.monotonic() - t_inf) * 1000)
    log.info("rid=%s inference_ms=%d session=%s mode=%s", g.rid, inf_ms, session_id[:8], result.get("modo", "?"))
    metrics_mod.record_query(inf_ms)

    nivel = result.get("gravedad_info", {})
    gravedad = result.get("gravedad", "moderada")

    response = {
        "success": True,
        "respuesta": result["respuesta"],
        "condicion_principal": result.get("condicion_principal", "Ver respuesta"),
        "gravedad": gravedad,
        "gravedad_label": nivel.get("label", gravedad.upper()),
        "gravedad_color": nivel.get("color", "#f59e0b"),
        "gravedad_icon": nivel.get("icon", "🟡"),
        "gravedad_descripcion": nivel.get("description", ""),
        "recomendacion": result.get("recomendacion", "Consultar medico."),
        "condiciones_relacionadas": result.get("condiciones_relacionadas", []),
        "urgencia": result.get("urgencia", gravedad),
        "confianza": result.get("score_confianza", 0),
        "fuentes": result.get("fuentes", []),
        "rag_chunks": result.get("rag_chunks", []),
        "modo": result.get("modo", ""),
        "trajectory": result.get("trajectory", []),
        "tools_used": result.get("tools_used", []),
        "disclaimer": "MEDI-IA no reemplaza la consulta medica profesional.",
    }
    return jsonify(response)


@app.route("/api/reset", methods=["POST"])
@require_auth
def reset_session():
    """Reinicia la conversacion (nueva sesion)."""
    session_id = _get_session_id()
    clear_session(session_id)
    session.pop("session_id", None)
    return jsonify({"status": "ok", "message": "Sesion reiniciada."})


@app.route("/api/health", methods=["GET"])
@require_auth
def health_check():
    return jsonify(get_health())


@app.route("/api/reload", methods=["POST"])
@require_auth
def reload_index():
    try:
        from src.rag import retriever
        retriever._index = None
        retriever._metadata = None
        retriever._load()
        try:
            from src.rag import bm25_retriever
            bm25_retriever.reset()
        except Exception:
            pass
        return jsonify({"status": "ok", "message": "Indice recargado."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stream", methods=["POST"])
@require_auth
@limiter.limit("10 per minute")
def stream_query():
    """Endpoint SSE: hace streaming token a token del agente ReAct."""
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify(ErrorResponse(error="No se proporciono mensaje").model_dump()), 400

    try:
        consulta = ConsultaRequest(message=data["message"])
    except Exception as e:
        return jsonify(ErrorResponse(error=str(e)).model_dump()), 400

    from src.guardrails import is_medical_query
    if not is_medical_query(consulta.message):
        return jsonify(ErrorResponse(
            error="Consulta no medica. Solo respondo preguntas sobre sintomas y salud."
        ).model_dump()), 400

    session_id = _get_session_id()

    # Sin HF_TOKEN: RAG fallback — emite un solo evento done
    if not os.getenv("HF_TOKEN"):
        try:
            result = run(consulta.message, session_id=session_id)
        except FileNotFoundError:
            def _no_index():
                yield f"data: {json.dumps({'type': 'error', 'message': 'Base de conocimiento no disponible. Ejecuta make ingest.'})}\n\n"
            return Response(stream_with_context(_no_index()), mimetype="text/event-stream",
                            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
        from src.agent import GRAVITY_LEVELS
        nivel = GRAVITY_LEVELS.get(result.get("gravedad", "moderada"), GRAVITY_LEVELS["moderada"])
        payload = {
            "type": "done",
            "gravedad": result.get("gravedad", "moderada"),
            "gravedad_label": nivel["label"],
            "gravedad_color": nivel["color"],
            "gravedad_icon": nivel["icon"],
            "gravedad_descripcion": nivel["description"],
            "condicion_principal": result.get("condicion_principal", "Ver respuesta"),
            "recomendacion": result.get("recomendacion", "Consultar medico."),
            "respuesta": result.get("respuesta", ""),
            "trajectory": result.get("trajectory", []),
            "fuentes": result.get("fuentes", []),
            "rag_chunks": result.get("rag_chunks", []),
            "confianza": result.get("score_confianza", 0),
            "modo": result.get("modo", "RAG Template"),
            "tools_used": result.get("tools_used", []),
        }
        def _rag():
            yield f"data: {json.dumps(payload)}\n\n"
        return Response(stream_with_context(_rag()), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    # Con HF_TOKEN: streaming completo
    from src.agent_loop import stream_react

    rid = g.rid
    t_stream = time.monotonic()

    def generate():
        try:
            for event in stream_react(session_id, consulta.message):
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("type") == "done":
                    stream_ms = int((time.monotonic() - t_stream) * 1000)
                    log.info("rid=%s stream_ms=%d session=%s iters=%d",
                             rid, stream_ms, session_id[:8], event.get("iteraciones", 0))
                    metrics_mod.record_query(stream_ms)
        except Exception as e:
            log.error("rid=%s stream_error=%s", rid, e)
            metrics_mod.record_error()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/export/pdf", methods=["POST"])
@require_auth
@limiter.limit("5 per minute")
def export_pdf():
    """Genera un PDF del reporte de diagnostico y lo devuelve como descarga."""
    data = request.get_json()
    if not data or not data.get("respuesta"):
        return jsonify({"error": "No hay datos para exportar"}), 400

    try:
        pdf_bytes = build_diagnosis_pdf(data)
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": "attachment; filename=medi-ia-reporte.pdf"},
        )
    except Exception as e:
        log.error("rid=%s pdf_error=%s", g.rid, e)
        return jsonify({"error": f"Error al generar PDF: {e}"}), 500


@app.route("/api/evaluate/full", methods=["GET"])
@require_auth
def get_full_eval():
    """Retorna los resultados de la ultima evaluacion completa del pipeline RAG."""
    results_path = os.path.join(os.path.dirname(__file__), "data", "eval_full_results.json")
    if not os.path.exists(results_path):
        return jsonify({"error": "Sin resultados. Ejecuta: make eval-full"}), 404
    try:
        with open(results_path, encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        log.error("rid=%s eval_full_error=%s", g.rid, e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/export/conversation", methods=["GET"])
@require_auth
@limiter.limit("5 per minute")
def export_conversation():
    """Genera un PDF con todos los turnos de la sesión actual."""
    session_id = _get_session_id()
    history = get_history(session_id)
    turns = [t for t in history if t["role"] != "system"]
    if not turns:
        return jsonify({"error": "La sesión está vacía"}), 400
    try:
        pdf_bytes = build_conversation_pdf(turns)
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": "attachment; filename=medi-ia-sesion.pdf"},
        )
    except Exception as e:
        log.error("rid=%s conversation_pdf_error=%s", g.rid, e)
        return jsonify({"error": f"Error al generar PDF: {e}"}), 500


@app.route("/metrics", methods=["GET"])
@require_auth
def metrics_page():
    return render_template("metrics.html")


@app.route("/live", methods=["GET"])
@require_auth
def live_page():
    return render_template("live.html")


@app.route("/manifest.json", methods=["GET"])
def pwa_manifest():
    return jsonify({
        "name": "MEDI-IA",
        "short_name": "MEDI-IA",
        "description": "Asistente médico con diagnóstico diferencial — 14 libros médicos, RAG + ReAct",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#090e1a",
        "theme_color": "#10b981",
        "orientation": "portrait-primary",
        "icons": [
            {"src": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='%23090e1a'/><text y='72' x='50' text-anchor='middle' font-size='60'>🩺</text></svg>", "sizes": "any", "type": "image/svg+xml"}
        ]
    })


@app.route("/api/feedback", methods=["POST"])
@require_auth
@limiter.limit("30 per minute")
def feedback():
    data = request.get_json()
    if not data or "rating" not in data:
        return jsonify({"error": "rating requerido (1 o -1)"}), 400
    rating = data["rating"]
    if rating not in (1, -1):
        return jsonify({"error": "rating debe ser 1 o -1"}), 400
    session_id = _get_session_id()
    try:
        save_feedback(session_id, data.get("condicion", ""), rating)
    except Exception as e:
        log.error("rid=%s feedback_error=%s", g.rid, e)
        return jsonify({"error": "No se pudo guardar el feedback"}), 500
    return jsonify({"ok": True})


@app.route("/api/metrics", methods=["GET"])
@require_auth
def get_metrics():
    """Métricas básicas en memoria: queries/hora, latencia, errores, uptime, feedback."""
    try:
        fb = get_feedback_stats()
    except Exception:
        fb = {"total": 0, "positive": 0, "negative": 0}

    return jsonify(metrics_mod.snapshot(fb))


@app.route("/evaluate", methods=["GET"])
@require_auth
def evaluate_page():
    from src.evaluation import load_snapshot
    has_snapshot = load_snapshot() is not None
    return render_template("evaluate.html", has_snapshot=has_snapshot)


@app.route("/api/evaluate/snapshot", methods=["GET"])
@require_auth
def get_eval_snapshot():
    from src.evaluation import load_snapshot
    data = load_snapshot()
    if data is None:
        return jsonify({"error": "No hay snapshot. Ejecuta el benchmark primero."}), 404
    return jsonify(data)


@app.route("/api/evaluate/run", methods=["POST"])
@require_auth
@limiter.limit("2 per minute")
def run_evaluation():
    from src.evaluation import run_benchmark, save_snapshot
    try:
        data = run_benchmark()
        save_snapshot(data)
        log.info("rid=%s benchmark_done duration_s=%.1f", g.rid, data["duration_s"])
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Indice FAISS no encontrado. Ejecuta make ingest primero."}), 503
    except Exception as e:
        log.error("rid=%s benchmark_error=%s", g.rid, e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/tts", methods=["POST"])
@require_auth
@limiter.limit("30 per minute")
def tts_endpoint():
    import edge_tts
    from threading import Thread
    from queue import Queue

    data = request.json or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text requerido"}), 400
    if len(text) > 3000:
        text = text[:3000]

    voice = data.get("voice", "es-ES-AlvaroNeural")
    q: Queue = Queue()

    async def _gen():
        import asyncio
        try:
            communicate = edge_tts.Communicate(text, voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    q.put(chunk["data"])
        except Exception as exc:
            log.error("rid=%s tts_error=%s", g.rid, exc)
        finally:
            q.put(None)

    Thread(target=lambda: __import__("asyncio").run(_gen()), daemon=True).start()

    def _stream():
        while True:
            chunk = q.get()
            if chunk is None:
                break
            yield chunk

    return Response(
        stream_with_context(_stream()),
        mimetype="audio/mpeg",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    print("[MEDI-IA] Iniciando servidor...")
    _start_cleanup_cron()
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
