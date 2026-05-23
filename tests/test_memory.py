"""
Tests para src/memory.py (implementacion SQLite).
Cada test usa una base de datos temporal aislada via tmp_path.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
import src.memory as mem_mod


@pytest.fixture
def mem(tmp_path, monkeypatch):
    """Base de datos SQLite temporal — aislada por test."""
    monkeypatch.setattr(mem_mod, "DB_PATH", str(tmp_path / "test.db"))
    mem_mod._init_schema()
    yield mem_mod


class TestAddAndGetHistory:
    def test_empty_session_returns_empty_list(self, mem):
        assert mem.get_history("nueva-sesion") == []

    def test_add_single_turn(self, mem):
        mem.add_turn("s1", "user", "tengo fiebre")
        history = mem.get_history("s1")
        assert history == [{"role": "user", "content": "tengo fiebre"}]

    def test_add_multiple_turns_preserves_order(self, mem):
        mem.add_turn("s1", "user", "mensaje 1")
        mem.add_turn("s1", "assistant", "respuesta 1")
        mem.add_turn("s1", "user", "mensaje 2")
        history = mem.get_history("s1")
        assert len(history) == 3
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        assert history[2]["content"] == "mensaje 2"

    def test_sessions_are_isolated(self, mem):
        mem.add_turn("sesion-a", "user", "mensaje A")
        mem.add_turn("sesion-b", "user", "mensaje B")
        assert mem.get_history("sesion-a") == [{"role": "user", "content": "mensaje A"}]
        assert mem.get_history("sesion-b") == [{"role": "user", "content": "mensaje B"}]

    def test_content_with_special_characters(self, mem):
        content = "fiebre 39°C, dolor de cabeza y náuseas — ¿es grave?"
        mem.add_turn("s1", "user", content)
        assert mem.get_history("s1")[0]["content"] == content


class TestSystemPrompt:
    def test_system_appears_before_user_turns(self, mem):
        mem.set_system("s1", "Eres un medico experto.")
        mem.add_turn("s1", "user", "hola")
        history = mem.get_history("s1")
        assert history[0]["role"] == "system"
        assert history[1]["role"] == "user"

    def test_set_system_only_stores_once(self, mem):
        mem.set_system("s1", "Prompt original")
        mem.set_system("s1", "Prompt nuevo")  # debe ignorarse
        system_msgs = [m for m in mem.get_history("s1") if m["role"] == "system"]
        assert len(system_msgs) == 1
        assert system_msgs[0]["content"] == "Prompt original"

    def test_set_system_idempotent_on_repeated_calls(self, mem):
        for _ in range(5):
            mem.set_system("s1", "Prompt fijo")
        system_msgs = [m for m in mem.get_history("s1") if m["role"] == "system"]
        assert len(system_msgs) == 1

    def test_system_is_first_after_turns_added(self, mem):
        mem.set_system("s1", "sys")
        for i in range(5):
            mem.add_turn("s1", "user", f"msg {i}")
            mem.add_turn("s1", "assistant", f"resp {i}")
        assert mem.get_history("s1")[0]["role"] == "system"


class TestClearAndList:
    def test_clear_removes_all_turns(self, mem):
        mem.add_turn("s1", "user", "hola")
        mem.clear_session("s1")
        assert mem.get_history("s1") == []

    def test_clear_nonexistent_session_does_not_raise(self, mem):
        mem.clear_session("no-existe")  # no debe lanzar excepcion

    def test_clear_only_removes_target_session(self, mem):
        mem.add_turn("a", "user", "mensaje A")
        mem.add_turn("b", "user", "mensaje B")
        mem.clear_session("a")
        assert mem.get_history("a") == []
        assert len(mem.get_history("b")) == 1

    def test_list_sessions_returns_known_ids(self, mem):
        mem.add_turn("alpha", "user", "x")
        mem.add_turn("beta", "user", "y")
        sessions = mem.list_sessions()
        assert "alpha" in sessions
        assert "beta" in sessions

    def test_cleared_session_removed_from_list(self, mem):
        mem.add_turn("s1", "user", "x")
        mem.clear_session("s1")
        assert "s1" not in mem.list_sessions()


class TestMaxTurnsTrimming:
    def test_trims_oldest_non_system_turns(self, mem):
        MAX = mem_mod.MAX_TURNS
        mem.set_system("s1", "sys")
        for i in range(MAX * 2 + 4):
            mem.add_turn("s1", "user", f"msg {i}")
            mem.add_turn("s1", "assistant", f"resp {i}")
        history = mem.get_history("s1")
        non_system = [m for m in history if m["role"] != "system"]
        assert len(non_system) <= MAX * 2

    def test_system_never_trimmed(self, mem):
        MAX = mem_mod.MAX_TURNS
        mem.set_system("s1", "system prompt intacto")
        for i in range(MAX * 2 + 4):
            mem.add_turn("s1", "user", f"msg {i}")
            mem.add_turn("s1", "assistant", f"resp {i}")
        history = mem.get_history("s1")
        assert history[0]["role"] == "system"
        assert history[0]["content"] == "system prompt intacto"

    def test_most_recent_turns_kept(self, mem):
        MAX = mem_mod.MAX_TURNS
        for i in range(MAX * 2 + 4):
            mem.add_turn("s1", "user", f"msg {i}")
        history = mem.get_history("s1")
        contents = [m["content"] for m in history]
        # Los ultimos mensajes deben estar presentes
        assert f"msg {MAX * 2 + 3}" in contents
        assert f"msg {MAX * 2 + 2}" in contents
        # Los primeros mensajes deben haber sido eliminados
        assert "msg 0" not in contents
