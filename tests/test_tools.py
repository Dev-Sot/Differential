"""
Tests para src/tools.py.

assess_urgency: logica pura, sin mocks.
search_symptoms / get_drug_info / get_section: mockean retrieve() y rerank()
  para no necesitar el indice FAISS.
execute_tool: testea el dispatcher con mocks y con assess_urgency real.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import patch, MagicMock
from src.tools import (
    assess_urgency,
    execute_tool,
    tools_description,
    TOOLS,
)


# ── Chunks de ejemplo reutilizables en tests con mock ────────────────────────

def _make_chunk(book="Harrison Principios De Medicina Interna 19 1", page=42,
                text="Texto de ejemplo medico.", seccion="Cardiologia"):
    return {"book": book, "page": page, "text": text, "seccion": seccion,
            "score": 0.9, "rerank_score": 1.2}


# ── assess_urgency ────────────────────────────────────────────────────────────

class TestAssessUrgency:
    def test_infarto_is_emergency(self):
        result = assess_urgency("posible infarto", "")
        assert "emergencia" in result.lower()

    def test_paro_cardiaco_is_emergency(self):
        result = assess_urgency("paro cardiaco", "")
        assert "emergencia" in result.lower()

    def test_convulsiones_is_emergency(self):
        result = assess_urgency("convulsiones continuas", "")
        assert "emergencia" in result.lower()

    def test_anafilaxia_is_emergency(self):
        result = assess_urgency("reaccion alergica severa anafilaxia", "")
        assert "emergencia" in result.lower()

    def test_emergency_detected_in_context(self):
        # La keyword esta en el contexto, no en symptoms
        result = assess_urgency("no se siente bien", "historial de sepsis reciente")
        assert "emergencia" in result.lower()

    def test_dolor_pecho_is_grave(self):
        result = assess_urgency("dolor pecho intenso", "")
        assert "grave" in result.lower()

    def test_difficulty_breathing_is_grave(self):
        result = assess_urgency("difficulty breathing", "")
        assert "grave" in result.lower()

    def test_chest_pain_is_grave(self):
        result = assess_urgency("chest pain", "")
        assert "grave" in result.lower()

    def test_default_is_moderada(self):
        result = assess_urgency("me duele un poco la cabeza", "sin antecedentes")
        assert "moderada" in result.lower()

    def test_case_insensitive_emergency(self):
        result = assess_urgency("INFARTO AGUDO", "")
        assert "emergencia" in result.lower()

    def test_emergency_beats_grave(self):
        # Cuando hay keywords de emergencia Y grave a la vez, debe salir emergencia
        result = assess_urgency("dolor pecho e infarto", "")
        assert "emergencia" in result.lower()


# ── execute_tool — dispatcher ─────────────────────────────────────────────────

class TestExecuteTool:
    def test_unknown_tool_returns_error_message(self):
        result = execute_tool("herramienta_inexistente", "input")
        assert "no existe" in result.lower() or "Herramienta" in result

    def test_unknown_tool_lists_available_tools(self):
        result = execute_tool("xyz", "algo")
        for name in TOOLS:
            assert name in result

    def test_assess_urgency_with_pipe_separator(self):
        result = execute_tool("assess_urgency", "infarto|||diabetico 60 anos")
        assert "emergencia" in result.lower()

    def test_assess_urgency_without_separator_uses_full_input(self):
        # Sin ||| el input completo se usa como symptoms
        result = execute_tool("assess_urgency", "convulsiones")
        assert "emergencia" in result.lower()

    def test_assess_urgency_empty_context(self):
        result = execute_tool("assess_urgency", "fiebre|||")
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("src.tools.retrieve")
    @patch("src.tools.rerank")
    def test_search_symptoms_calls_retrieve_and_rerank(self, mock_rerank, mock_retrieve):
        chunk = _make_chunk()
        mock_retrieve.return_value = [chunk]
        mock_rerank.return_value = [chunk]

        result = execute_tool("search_symptoms", "fiebre y tos")

        mock_retrieve.assert_called_once()
        mock_rerank.assert_called_once()
        assert "Fragmento 1" in result

    @patch("src.tools.retrieve")
    @patch("src.tools.rerank")
    def test_search_symptoms_no_results_returns_message(self, mock_rerank, mock_retrieve):
        mock_retrieve.return_value = []
        mock_rerank.return_value = []

        result = execute_tool("search_symptoms", "sintoma inexistente xyz")
        assert "No se encontraron" in result

    @patch("src.tools.retrieve")
    @patch("src.tools.rerank")
    def test_get_section_with_separator(self, mock_rerank, mock_retrieve):
        chunk = _make_chunk()
        mock_retrieve.return_value = [chunk]
        mock_rerank.return_value = [chunk]

        result = execute_tool("get_section", "harrison|||infarto miocardio")
        assert isinstance(result, str)
        assert len(result) > 0
        mock_retrieve.assert_called_once_with("infarto miocardio", top_k=15)

    @patch("src.tools.retrieve")
    @patch("src.tools.rerank")
    def test_get_section_without_separator_uses_full_as_topic(self, mock_rerank, mock_retrieve):
        chunk = _make_chunk()
        mock_retrieve.return_value = [chunk]
        mock_rerank.return_value = [chunk]

        execute_tool("get_section", "harrison infarto")
        # Sin ||| el input completo va como topic
        mock_retrieve.assert_called_once_with("harrison infarto", top_k=15)

    @patch("src.tools.retrieve")
    @patch("src.tools.rerank")
    def test_get_drug_info_filters_drugs_book(self, mock_rerank, mock_retrieve):
        drug_chunk = _make_chunk(book="The Top 100 Drugs Clinical", text="Aspirina 100mg")
        other_chunk = _make_chunk(book="Harrison Principios De Medicina Interna 19 1")
        mock_retrieve.return_value = [drug_chunk, other_chunk]
        mock_rerank.return_value = [drug_chunk]

        result = execute_tool("get_drug_info", "hipertension")
        assert "Top 100 Drugs" in result

    @patch("src.tools.retrieve")
    @patch("src.tools.rerank")
    def test_execute_tool_catches_exception(self, mock_rerank, mock_retrieve):
        mock_retrieve.side_effect = RuntimeError("FAISS index not found")

        result = execute_tool("search_symptoms", "dolor")
        assert "Error" in result
        assert "search_symptoms" in result


# ── TOOLS registry ────────────────────────────────────────────────────────────

class TestToolsRegistry:
    def test_all_four_tools_registered(self):
        expected = {"search_symptoms", "assess_urgency", "get_drug_info", "get_section"}
        assert expected == set(TOOLS.keys())

    def test_each_tool_has_func_key(self):
        for name, meta in TOOLS.items():
            assert "func" in meta, f"Tool '{name}' no tiene 'func'"

    def test_each_tool_has_description_key(self):
        for name, meta in TOOLS.items():
            assert "description" in meta, f"Tool '{name}' no tiene 'description'"

    def test_each_func_is_callable(self):
        for name, meta in TOOLS.items():
            assert callable(meta["func"]), f"Tool '{name}' func no es callable"

    def test_descriptions_are_non_empty(self):
        for name, meta in TOOLS.items():
            assert len(meta["description"]) > 10, f"Description de '{name}' muy corta"


# ── tools_description() ───────────────────────────────────────────────────────

class TestToolsDescription:
    def setup_method(self):
        self.desc = tools_description()

    def test_all_tool_names_present(self):
        for name in TOOLS:
            assert name in self.desc

    def test_each_line_starts_with_dash(self):
        for line in self.desc.strip().splitlines():
            assert line.startswith("- "), f"Linea sin formato '- ': {line!r}"

    def test_returns_string(self):
        assert isinstance(self.desc, str)

    def test_has_four_lines(self):
        lines = [l for l in self.desc.strip().splitlines() if l.strip()]
        assert len(lines) == 4
