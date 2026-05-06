"""
Guardrails de MEDI-IA — filtra consultas no medicas antes de llegar al LLM.
Solo pasan preguntas relacionadas con salud, sintomas, enfermedades o medicamentos.
"""
import re

_MEDICAL = re.compile(
    r"\b("
    r"sintoma|dolor|fiebre|tos|nausea|vomito|diarrea|mareo|fatiga|cansancio|"
    r"enfermedad|diagnostico|medicamento|tratamiento|farmaco|dosis|pastilla|"
    r"cabeza|pecho|abdomen|estomago|corazon|pulmon|rinon|higado|hueso|musculo|"
    r"sangre|presion|glucosa|colesterol|infeccion|virus|bacteria|inflamacion|"
    r"medico|doctor|hospital|clinica|urgencias|consulta|especialista|"
    r"alergia|asma|diabetes|hipertension|cancer|tumor|fractura|herida|"
    r"embarazo|prenatal|pediatria|geriatria|cirugia|operacion|anestesia|"
    r"biopsia|radiografia|ecografia|resonancia|tomografia|analisis|examen|"
    r"antibiotico|analgesico|antiinflamatorio|vacuna|inyeccion|suero|"
    r"salud|enfermo|paciente|clinico|medica|hemorragia|convulsion|desmayo|"
    r"picadura|quemadura|intoxicacion|asfixia|palpitacion|taquicardia|"
    r"hipotension|hipertension|falla|insuficiencia|infarto|derrame|"
    r"articulacion|columna|nervio|tendone|vena|arteria|linfa|hormona|"
    r"piel|erupcion|sarpullido|urticaria|psoriasis|eczema|acne|"
    r"vision|oido|ojos|nariz|garganta|boca|dientes|encias"
    r")\b",
    re.IGNORECASE,
)

_NON_MEDICAL = re.compile(
    r"\b("
    r"programacion|codigo|python|javascript|html|css|sql|algoritmo|software|"
    r"matematica|algebra|calculo|geometria|estadistica|fisica|quimica|"
    r"historia|politica|economia|filosofia|religion|arte|musica|pelicula|deporte|"
    r"cocina|receta|cocinar|viaje|turismo|moda|videojuego|juego|"
    r"chiste|broma|cuento|poema|cancion|letra|"
    r"dinero|inversion|cripto|bitcoin|finanzas|impuesto|"
    r"noticia|clima|tiempo|meteorologia|tecnologia"
    r")\b",
    re.IGNORECASE,
)

_REFUSAL_GRAVEDAD_INFO = {
    "label": "INFO",
    "color": "#6b7280",
    "icon": "ℹ️",
    "description": "Solo respondo preguntas medicas.",
}

_REFUSAL_TEXT = (
    "Soy MEDI-IA, un asistente médico especializado en diagnóstico diferencial.\n\n"
    "Solo puedo ayudarte con preguntas relacionadas con:\n"
    "- **Síntomas y enfermedades**\n"
    "- **Diagnóstico diferencial**\n"
    "- **Medicamentos y tratamientos**\n"
    "- **Urgencias y emergencias médicas**\n\n"
    "Por favor, descríbeme tus síntomas o tu consulta médica y con gusto te ayudo.\n\n"
    "_Esto no reemplaza la consulta médica profesional._"
)


def is_medical_query(text: str) -> bool:
    """
    True si la consulta parece medica o ambigua (beneficio de la duda).
    False solo si hay señales claras de tema no medico y ninguna señal medica.
    """
    has_medical = bool(_MEDICAL.search(text))
    has_non_medical = bool(_NON_MEDICAL.search(text))

    if has_medical:
        return True
    if has_non_medical:
        return False
    # Sin senales claras: dejar pasar, el system prompt del LLM decidira
    return True


def refusal_result() -> dict:
    """Resultado estructurado para rechazar consultas no medicas."""
    return {
        "respuesta": _REFUSAL_TEXT,
        "condicion_principal": "Consulta fuera del alcance médico",
        "gravedad": "leve",
        "gravedad_info": _REFUSAL_GRAVEDAD_INFO,
        "urgencia": "leve",
        "recomendacion": "Describe tus síntomas o consulta médica para que pueda ayudarte.",
        "condiciones_relacionadas": [],
        "score_confianza": 0,
        "fuentes": [],
        "modo": "Guardrail — consulta no médica",
        "trajectory": [],
        "tools_used": [],
        "iteraciones": 0,
    }
