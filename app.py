"""
MEDI-IA — Flask Application v4 (ReAct Agent)
"""

import sys
import os
import uuid
import json
import functools
import logging
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, jsonify, session, Response, stream_with_context, redirect, url_for, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from src.agent import run, get_health
from src.schemas import ConsultaRequest, ErrorResponse
from src.memory import clear_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("medi-ia")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24).hex())


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

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
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
    if password == AUTH_PASSWORD:
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
        return jsonify({
            "success": False,
            "error": "Base de conocimiento no disponible. Ejecuta 'make ingest' para construir el indice FAISS.",
        }), 503
    inf_ms = int((time.monotonic() - t_inf) * 1000)
    log.info("rid=%s inference_ms=%d session=%s mode=%s", g.rid, inf_ms, session_id[:8], result.get("modo", "?"))

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
        except Exception as e:
            log.error("rid=%s stream_error=%s", rid, e)
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
        pdf_bytes = _build_pdf_bytes(data)
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": "attachment; filename=medi-ia-reporte.pdf"},
        )
    except Exception as e:
        log.error("rid=%s pdf_error=%s", g.rid, e)
        return jsonify({"error": f"Error al generar PDF: {e}"}), 500


def _build_pdf_bytes(data: dict) -> bytes:
    from fpdf import FPDF
    from datetime import datetime
    import re

    gravedad = data.get("gravedad", "moderada")
    sev_fg = {
        "leve":       (22, 163, 74),
        "moderada":   (180, 110, 0),
        "grave":      (185, 28, 28),
        "emergencia": (91, 33, 182),
    }.get(gravedad, (180, 110, 0))
    sev_bg = {
        "leve":       (240, 253, 244),
        "moderada":   (255, 251, 235),
        "grave":      (254, 242, 242),
        "emergencia": (245, 243, 255),
    }.get(gravedad, (255, 251, 235))

    EMERALD = (16, 185, 129)
    BLUE    = (59, 130, 246)
    SLATE   = (71, 85, 105)
    MUTED   = (148, 163, 184)
    DARK    = (15, 23, 42)

    def safe(text):
        """Normalize Unicode to Latin-1 safe string (core PDF fonts)."""
        replacements = {
            "—": "-", "–": "-",
            "“": '"', "”": '"',
            "‘": "'", "’": "'",
            "…": "...",
        }
        s = str(text or "")
        for k, v in replacements.items():
            s = s.replace(k, v)
        return s.encode("latin-1", errors="replace").decode("latin-1")

    def clean(text):
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text or "")
        skip = [
            "condicion principal", "condicion principal sugerida",
            "nivel de urgencia", "recomendacion",
            "esto no reemplaza", "este reporte",
            "sintomas clave",
        ]
        lines = [
            l for l in text.split("\n")
            if l.strip() and not any(l.strip().lower().startswith(s) for s in skip)
        ]
        return safe("\n".join(lines).strip())

    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    W = pdf.w - 40

    def label(text):
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 5, text.upper(), ln=True)
        pdf.ln(1)

    def vbar(color, x, y, h):
        pdf.set_fill_color(*color)
        pdf.rect(x, y, 2, h, style="F")

    def hline():
        pdf.set_draw_color(226, 232, 240)
        pdf.set_line_width(0.3)
        pdf.line(20, pdf.get_y(), pdf.w - 20, pdf.get_y())
        pdf.ln(4)

    # Header
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*EMERALD)
    pdf.cell(0, 12, "MEDI-IA", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MUTED)
    pdf.set_y(pdf.get_y() - 9)
    pdf.cell(0, 9, f"Reporte de evaluacion medica  |  {fecha}", align="R", ln=True)
    pdf.set_draw_color(*EMERALD)
    pdf.set_line_width(1.0)
    pdf.line(20, pdf.get_y(), pdf.w - 20, pdf.get_y())
    pdf.ln(8)

    # Query box
    query = safe(data.get("query", ""))
    if query:
        y0 = pdf.get_y()
        pdf.set_xy(25, y0 + 1)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*BLUE)
        pdf.cell(0, 4, "CONSULTA DEL PACIENTE", ln=True)
        pdf.set_x(25)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*DARK)
        pdf.multi_cell(W - 5, 5.5, query)
        vbar(BLUE, 20, y0, pdf.get_y() - y0)
        pdf.ln(7)

    # Severity pill + condition
    lbl  = safe(data.get("gravedad_label", gravedad.upper()))
    cond = safe(data.get("condicion_principal", ""))
    pill_w = min(len(lbl) * 2.6 + 10, 45)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*sev_bg)
    pdf.set_text_color(*sev_fg)
    pdf.set_draw_color(*sev_fg)
    pdf.set_line_width(0.4)
    pdf.cell(pill_w, 7, lbl, border=1, fill=True, align="C", ln=False)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*DARK)
    pdf.cell(5, 7, "", ln=False)
    pdf.multi_cell(W - pill_w - 5, 7, cond)
    pdf.ln(7)

    # Analysis
    label("Analisis medico")
    y0 = pdf.get_y()
    pdf.set_xy(25, y0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*SLATE)
    pdf.multi_cell(W - 5, 5.5, clean(data.get("respuesta", "")))
    vbar(EMERALD, 20, y0, pdf.get_y() - y0)
    pdf.ln(7)

    # Recommendation
    label("Recomendacion")
    rec_y = pdf.get_y()
    pdf.set_x(20)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*DARK)
    pdf.set_fill_color(240, 253, 244)
    pdf.multi_cell(W, 5.5, safe(data.get("recomendacion", "")), fill=True)
    rec_h = pdf.get_y() - rec_y
    pdf.set_draw_color(*EMERALD)
    pdf.set_line_width(0.4)
    pdf.rect(20, rec_y, W, rec_h)
    pdf.ln(7)

    # Sources
    fuentes = data.get("fuentes", [])
    if fuentes:
        label("Fuentes bibliograficas")
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(W, 5, safe(", ".join(fuentes)))
        pdf.ln(5)

    # Engine
    label("Motor de IA")
    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 5, safe(data.get("modo", "")), ln=True)
    pdf.ln(7)

    # Disclaimer
    hline()
    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(W, 5,
        "MEDI-IA no reemplaza la consulta medica profesional. "
        "Este reporte es generado por inteligencia artificial y debe ser validado "
        "por un profesional de la salud calificado. "
        "En caso de emergencia llame al 123 o dirigase a urgencias inmediatamente."
    )

    return bytes(pdf.output())


if __name__ == "__main__":
    print("[MEDI-IA] Iniciando servidor...")
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
