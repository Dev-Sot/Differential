"""
MEDI-IA — Flask Application v4 (ReAct Agent)
"""

import sys
import os
import uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, jsonify, session
from src.agent import run, get_health
from src.schemas import ConsultaRequest, ErrorResponse
from src.memory import clear_session

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24).hex())


def _get_session_id() -> str:
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/query", methods=["POST"])
def query_agent():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify(ErrorResponse(error="No se proporciono mensaje").model_dump()), 400

    try:
        consulta = ConsultaRequest(message=data["message"])
    except Exception as e:
        return jsonify(ErrorResponse(error=str(e)).model_dump()), 400

    session_id = _get_session_id()
    result = run(consulta.message, session_id=session_id)

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


if __name__ == "__main__":
    print("[MEDI-IA] Iniciando servidor...")
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
