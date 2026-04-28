"""
MEDI-IA - Agente Inteligente Conversacional para Evaluación de Síntomas Médicos
Flask Application - Fase 2
"""

from flask import Flask, render_template, request, jsonify
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rag_pipeline import get_pipeline
from data.corpus_medico import GRAVITY_LEVELS

app = Flask(__name__)

# Pre-cargar pipeline al iniciar
pipeline = None

@app.before_request
def load_pipeline():
    global pipeline
    if pipeline is None:
        pipeline = get_pipeline()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/query', methods=['POST'])
def query_agent():
    """Endpoint principal: recibe síntomas y devuelve evaluación."""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No se proporcionó mensaje'}), 400

    user_message = data['message'].strip()
    if len(user_message) < 5:
        return jsonify({'error': 'Por favor describe tus síntomas con más detalle'}), 400

    result = pipeline.query(user_message)
    
    # Formatear respuesta para el frontend
    gravedad_info = result.get('gravedad_info', GRAVITY_LEVELS.get(result['gravedad'], {}))
    
    response = {
        'success': True,
        'respuesta': result['respuesta'],
        'condicion_principal': result['condicion_principal'],
        'gravedad': result['gravedad'],
        'gravedad_label': gravedad_info.get('label', result['gravedad'].upper()),
        'gravedad_color': gravedad_info.get('color', '#f59e0b'),
        'gravedad_icon': gravedad_info.get('icon', '🟡'),
        'gravedad_descripcion': gravedad_info.get('description', ''),
        'recomendacion': result['recomendacion'],
        'condiciones_relacionadas': result.get('condiciones_relacionadas', []),
        'urgencia': result['urgencia'],
        'confianza': result.get('score_confianza', 0),
        'disclaimer': '⚠️ MEDI-IA no reemplaza la consulta médica profesional. Esta es una evaluación preliminar orientativa.'
    }
    
    return jsonify(response)


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'model': 'TF-IDF + Cosine Similarity', 'corpus_size': 20})


if __name__ == '__main__':
    print("[MEDI-IA] Iniciando servidor...")
    app.run(debug=True, host='0.0.0.0', port=5000)
