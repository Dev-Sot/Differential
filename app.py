"""
MEDI-IA — Flask Application v4 (ReAct Agent)
"""

import sys
import os
import uuid
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, jsonify, session, Response, stream_with_context
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from src.agent import run, get_health
from src.schemas import ConsultaRequest, ErrorResponse
from src.memory import clear_session

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24).hex())

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)


def _get_session_id() -> str:
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/query", methods=["POST"])
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
    try:
        result = run(consulta.message, session_id=session_id)
    except FileNotFoundError:
        return jsonify({
            "success": False,
            "error": "Base de conocimiento no disponible. Ejecuta 'make ingest' para construir el indice FAISS.",
        }), 503

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
def reset_session():
    """Reinicia la conversacion (nueva sesion)."""
    session_id = _get_session_id()
    clear_session(session_id)
    session.pop("session_id", None)
    return jsonify({"status": "ok", "message": "Sesion reiniciada."})


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify(get_health())


@app.route("/api/reload", methods=["POST"])
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

    def generate():
        try:
            for event in stream_react(session_id, consulta.message):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/export/pdf", methods=["POST"])
@limiter.limit("5 per minute")
def export_pdf():
    """Genera un PDF del reporte de diagnostico y lo devuelve como descarga."""
    data = request.get_json()
    if not data or not data.get("respuesta"):
        return jsonify({"error": "No hay datos para exportar"}), 400

    try:
        from weasyprint import HTML
        html_content = _build_pdf_html(data)
        pdf_bytes = HTML(string=html_content).write_pdf()
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": "attachment; filename=medi-ia-reporte.pdf"},
        )
    except ImportError:
        return jsonify({"error": "WeasyPrint no esta instalado correctamente."}), 500
    except Exception as e:
        return jsonify({"error": f"Error al generar PDF: {e}"}), 500


def _build_pdf_html(data: dict) -> str:
    import html as _html
    from datetime import datetime

    def esc(val):
        return _html.escape(str(val or ""))

    gravedad = data.get("gravedad", "moderada")
    sev_styles = {
        "leve":       ("#22c55e", "#f0fdf4"),
        "moderada":   ("#f59e0b", "#fffbeb"),
        "grave":      ("#ef4444", "#fef2f2"),
        "emergencia": ("#8b5cf6", "#f5f3ff"),
    }
    fg, bg = sev_styles.get(gravedad, ("#f59e0b", "#fffbeb"))

    respuesta_html = esc(data.get("respuesta", "")).replace("\n\n", "</p><p>").replace("\n", "<br>")

    fuentes_html = ""
    if data.get("fuentes"):
        fuentes_html = f"""
        <div class="section">
          <div class="section-label">Fuentes bibliograficas</div>
          <div class="sources">{esc(", ".join(data["fuentes"]))}</div>
        </div>"""

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: Arial, Helvetica, sans-serif; margin: 48px; color: #1e293b; font-size: 13px; line-height: 1.65; }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2.5px solid #10b981; padding-bottom: 14px; margin-bottom: 28px; }}
  .logo {{ font-size: 22px; font-weight: bold; color: #10b981; }}
  .logo em {{ color: #1e293b; font-style: normal; }}
  .date {{ font-size: 10px; color: #94a3b8; text-align: right; }}
  .query-box {{ background: #eff6ff; border-left: 3px solid #3b82f6; padding: 10px 14px; border-radius: 6px; margin-bottom: 22px; }}
  .query-label {{ font-size: 9px; font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase; color: #3b82f6; margin-bottom: 4px; }}
  .meta {{ display: flex; align-items: center; gap: 12px; margin-bottom: 22px; }}
  .sev-pill {{ display: inline-block; padding: 4px 14px; border-radius: 20px; font-weight: bold; font-size: 11px; background: {bg}; color: {fg}; border: 1px solid {fg}; }}
  .condition {{ font-size: 17px; font-weight: 700; color: #0f172a; }}
  .section {{ margin-bottom: 20px; }}
  .section-label {{ font-size: 9px; font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase; color: #94a3b8; margin-bottom: 6px; }}
  .response-box {{ background: #f8fafc; border-left: 3px solid #10b981; padding: 14px 16px; border-radius: 6px; color: #334155; }}
  .response-box p {{ margin: 0 0 8px; }}
  .response-box p:last-child {{ margin: 0; }}
  .rec-box {{ background: #f0fdf4; border: 1px solid rgba(16,185,129,0.3); padding: 12px 16px; border-radius: 6px; }}
  .sources {{ font-size: 11px; color: #64748b; font-style: italic; }}
  .mode {{ font-size: 10px; color: #94a3b8; font-family: monospace; }}
  .disclaimer {{ font-size: 10px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 14px; margin-top: 28px; font-style: italic; }}
</style>
</head>
<body>

<div class="header">
  <div class="logo">MEDI-<em>IA</em></div>
  <div class="date">Reporte de evaluacion medica<br>{fecha}</div>
</div>

<div class="query-box">
  <div class="query-label">Consulta del paciente</div>
  {esc(data.get("query", ""))}
</div>

<div class="meta">
  <span class="sev-pill">{esc(data.get("gravedad_label", gravedad.upper()))}</span>
  <span class="condition">{esc(data.get("condicion_principal", ""))}</span>
</div>

<div class="section">
  <div class="section-label">Analisis medico</div>
  <div class="response-box"><p>{respuesta_html}</p></div>
</div>

<div class="section">
  <div class="section-label">Recomendacion</div>
  <div class="rec-box">{esc(data.get("recomendacion", ""))}</div>
</div>

{fuentes_html}

<div class="section">
  <div class="section-label">Motor de IA</div>
  <div class="mode">{esc(data.get("modo", ""))}</div>
</div>

<div class="disclaimer">
  MEDI-IA no reemplaza la consulta medica profesional. Este reporte es generado por
  inteligencia artificial y debe ser validado por un profesional de la salud calificado.
  En caso de emergencia llame al 123 o dirijase a urgencias inmediatamente.
</div>

</body>
</html>"""


if __name__ == "__main__":
    print("[MEDI-IA] Iniciando servidor...")
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
