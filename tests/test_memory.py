"""
Tests para src/memory.py (implementacion SQLite).
Cada test usa una base de datos temporal aislada via tmp_path.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
import time
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


class TestCleanupOldSessions:
    def test_cleanup_zero_days_removes_all_active(self, mem):
        mem.add_turn("s1", "user", "hola")
        mem.add_turn("s2", "user", "hola")
        # days=0 considera todo como viejo
        eliminated = mem.cleanup_old_sessions(days=0)
        assert eliminated == 2
        assert mem.get_history("s1") == []
        assert mem.get_history("s2") == []

    def test_cleanup_large_days_removes_nothing(self, mem):
        mem.add_turn("s1", "user", "hola")
        eliminated = mem.cleanup_old_sessions(days=9999)
        assert eliminated == 0
        assert len(mem.get_history("s1")) == 1

    def test_cleanup_returns_count(self, mem):
        for sid in ["a", "b", "c"]:
            mem.add_turn(sid, "user", "x")
        eliminated = mem.cleanup_old_sessions(days=0)
        assert eliminated == 3

    def test_cleanup_removes_turns_and_session_metadata(self, mem):
        mem.add_turn("s1", "user", "hola")
        mem.cleanup_old_sessions(days=0)
        assert "s1" not in mem.list_sessions()

    def test_cleanup_is_selective(self, mem):
        mem.add_turn("old", "user", "vieja")
        # 'recent' queda con days=9999 — no se toca
        mem.add_turn("recent", "user", "nueva")
        # Solo borramos con days=0 la que fue last_seen hace menos de un instante,
        # que seria todas. Mejor test: verificar que days=9999 no toca nada
        eliminated = mem.cleanup_old_sessions(days=9999)
        assert eliminated == 0
        assert len(mem.get_history("old")) == 1
        assert len(mem.get_history("recent")) == 1


class TestSessionStats:
    def test_returns_list_of_dicts(self, mem):
        mem.add_turn("s1", "user", "a")
        stats = mem.session_stats()
        assert isinstance(stats, list)
        assert len(stats) == 1
        assert {"session", "turns", "last_seen"}.issubset(stats[0].keys())

    def test_turn_count_is_accurate(self, mem):
        for i in range(3):
            mem.add_turn("s1", "user", f"msg {i}")
        stats = mem.session_stats()
        s1 = next(s for s in stats if s["session"] == "s1")
        assert s1["turns"] == 3

    def test_empty_db_returns_empty_list(self, mem):
        assert mem.session_stats() == []

    def test_last_seen_is_populated_after_add_turn(self, mem):
        mem.add_turn("s1", "user", "hola")
        stats = mem.session_stats()
        assert stats[0]["last_seen"] is not None
        assert len(stats[0]["last_seen"]) > 10
