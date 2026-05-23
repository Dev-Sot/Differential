"""
Tests para src/guardrails.py.
Logica pura — no requiere FAISS ni modelos ML.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.guardrails import is_medical_query, refusal_result


class TestIsMedicalQuery:
    # ── Consultas claramente medicas ─────────────────────────────────────────

    def test_symptom_dolor_passes(self):
        assert is_medical_query("tengo dolor de cabeza desde ayer") is True

    def test_symptom_fiebre_passes(self):
        assert is_medical_query("fiebre de 38.5 en mi hijo") is True

    def test_symptom_nausea_passes(self):
        assert is_medical_query("nausea y vomito despues de comer") is True

    def test_medication_keyword_passes(self):
        assert is_medical_query("que medicamento tomar para la infeccion") is True

    def test_emergency_keywords_pass(self):
        assert is_medical_query("posible infarto, palpitaciones fuertes") is True

    def test_body_part_keyword_passes(self):
        assert is_medical_query("me duele el pecho al respirar") is True

    def test_condition_diabetes_passes(self):
        assert is_medical_query("soy diabetico y tengo herida que no cicatriza") is True

    def test_medical_wins_over_non_medical(self):
        # Si hay keyword medica Y no-medica, la medica tiene prioridad
        assert is_medical_query("tengo fiebre y quiero aprender python") is True

    def test_case_insensitive_medical(self):
        assert is_medical_query("FIEBRE ALTA Y ESCALOFRIOS") is True

    # ── Consultas claramente no medicas ──────────────────────────────────────

    def test_programming_blocked(self):
        assert is_medical_query("como hago un algoritmo en python") is False

    def test_cooking_blocked(self):
        assert is_medical_query("dame una receta para cocinar arroz") is False

    def test_economics_blocked(self):
        assert is_medical_query("invertir en cripto o en acciones") is False

    def test_entertainment_blocked(self):
        assert is_medical_query("recomiendame una pelicula de accion") is False

    def test_history_blocked(self):
        assert is_medical_query("cuando fue la revolucion francesa historia") is False

    def test_case_insensitive_non_medical(self):
        assert is_medical_query("PROGRAMACION en JAVASCRIPT") is False

    # ── Consultas ambiguas — beneficio de la duda ────────────────────────────

    def test_empty_string_passes(self):
        # Sin senales de ningun tipo → dejar pasar
        assert is_medical_query("") is True

    def test_vague_query_passes(self):
        # "me siento mal" no tiene keyword de ningun tipo
        assert is_medical_query("me siento muy mal ultimamente") is True

    def test_greeting_passes(self):
        assert is_medical_query("hola buenos dias") is True


class TestRefusalResult:
    def setup_method(self):
        self.result = refusal_result()

    def test_required_keys_present(self):
        required = {
            "respuesta", "condicion_principal", "gravedad", "gravedad_info",
            "urgencia", "recomendacion", "condiciones_relacionadas",
            "score_confianza", "fuentes", "modo", "trajectory",
            "tools_used", "iteraciones",
        }
        assert required.issubset(self.result.keys())

    def test_gravedad_info_has_required_keys(self):
        gi = self.result["gravedad_info"]
        assert {"label", "color", "icon", "description"}.issubset(gi.keys())

    def test_score_confianza_is_zero(self):
        assert self.result["score_confianza"] == 0

    def test_iteraciones_is_zero(self):
        assert self.result["iteraciones"] == 0

    def test_lists_are_empty(self):
        assert self.result["condiciones_relacionadas"] == []
        assert self.result["fuentes"] == []
        assert self.result["trajectory"] == []
        assert self.result["tools_used"] == []

    def test_modo_identifies_guardrail(self):
        assert "guardrail" in self.result["modo"].lower() or "Guardrail" in self.result["modo"]

    def test_respuesta_is_non_empty_string(self):
        assert isinstance(self.result["respuesta"], str)
        assert len(self.result["respuesta"]) > 20

    def test_condicion_principal_describes_scope(self):
        assert "alcance" in self.result["condicion_principal"].lower() or \
               "scope" in self.result["condicion_principal"].lower() or \
               len(self.result["condicion_principal"]) > 5
