"""
Tests para autenticacion de usuarios reales (src/auth.py + rutas /signup, /auth/*).
Reemplaza el viejo AUTH_PASSWORD unico compartido.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

import app as app_mod
import src.auth as auth_mod

flask_app = app_mod.app


@pytest.fixture
def db(tmp_path, monkeypatch):
    """DB de auth temporal, aislada por test."""
    import src.memory as mem_mod
    monkeypatch.setattr(mem_mod, "DB_PATH", str(tmp_path / "test_auth.db"))
    mem_mod._init_schema()
    auth_mod._init_schema()
    return auth_mod


@pytest.fixture
def client(db):
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret-key"
    flask_app.config["RATELIMIT_ENABLED"] = False
    with flask_app.test_client() as c:
        yield c


# ─── src.auth: create_user / verify_user / get_user ───────────────────────────

class TestAuthModule:
    def test_create_user_returns_id(self, db):
        user_id = db.create_user("nueva@example.com", "password123")
        assert isinstance(user_id, int)

    def test_create_user_normalizes_email(self, db):
        user_id = db.create_user("  Nueva@Example.com  ", "password123")
        user = db.get_user(user_id)
        assert user["email"] == "nueva@example.com"

    def test_create_user_rejects_invalid_email(self, db):
        with pytest.raises(db.AuthError):
            db.create_user("no-es-un-correo", "password123")

    def test_create_user_rejects_short_password(self, db):
        with pytest.raises(db.AuthError):
            db.create_user("a@example.com", "corta")

    def test_create_user_rejects_duplicate_email(self, db):
        db.create_user("dup@example.com", "password123")
        with pytest.raises(db.AuthError):
            db.create_user("dup@example.com", "otraPassword1")

    def test_verify_user_correct_credentials(self, db):
        user_id = db.create_user("ok@example.com", "password123")
        assert db.verify_user("ok@example.com", "password123") == user_id

    def test_verify_user_wrong_password(self, db):
        db.create_user("ok2@example.com", "password123")
        assert db.verify_user("ok2@example.com", "incorrecta") is None

    def test_verify_user_unknown_email(self, db):
        assert db.verify_user("no-existe@example.com", "password123") is None

    def test_password_is_hashed_not_stored_plain(self, db):
        db.create_user("hash@example.com", "password123")
        with db._db() as conn:
            row = conn.execute("SELECT password_hash FROM users WHERE email=?", ("hash@example.com",)).fetchone()
        assert row["password_hash"] != "password123"


# ─── /signup, /auth/signup ──────────────────────────────────────────────────

class TestSignupEndpoint:
    def test_signup_creates_account_and_logs_in(self, client):
        r = client.post("/auth/signup", json={"email": "flujo@example.com", "password": "password123"})
        assert r.status_code == 200
        assert r.get_json()["ok"] is True
        # sesion iniciada automaticamente tras signup
        r2 = client.get("/")
        assert r2.status_code == 200

    def test_signup_rejects_short_password(self, client):
        r = client.post("/auth/signup", json={"email": "corta@example.com", "password": "123"})
        assert r.status_code == 400
        assert "error" in r.get_json()

    def test_signup_rejects_duplicate_email(self, client):
        client.post("/auth/signup", json={"email": "repe@example.com", "password": "password123"})
        r = client.post("/auth/signup", json={"email": "repe@example.com", "password": "otraPassword1"})
        assert r.status_code == 400

    def test_signup_page_renders_when_anonymous(self, client):
        r = client.get("/signup")
        assert r.status_code == 200


# ─── /auth/login, /auth/logout ──────────────────────────────────────────────

class TestLoginEndpoint:
    def test_login_with_correct_credentials(self, client):
        client.post("/auth/signup", json={"email": "login@example.com", "password": "password123"})
        client.post("/auth/logout")
        r = client.post("/auth/login", json={"email": "login@example.com", "password": "password123"})
        assert r.status_code == 200
        assert r.get_json()["ok"] is True

    def test_login_with_wrong_password_returns_401(self, client):
        client.post("/auth/signup", json={"email": "login2@example.com", "password": "password123"})
        client.post("/auth/logout")
        r = client.post("/auth/login", json={"email": "login2@example.com", "password": "mala"})
        assert r.status_code == 401
        assert "error" in r.get_json()

    def test_logout_clears_session(self, client):
        client.post("/auth/signup", json={"email": "out@example.com", "password": "password123"})
        client.post("/auth/logout")
        r = client.get("/")
        assert r.status_code == 200
        assert b"Crear cuenta" in r.data  # landing publica, no el chat

    def test_practice_page_still_requires_auth_after_landing_change(self, client):
        """La landing en '/' no debe aflojar require_auth en el resto de las rutas."""
        r = client.get("/practice")
        assert r.status_code == 302
        assert "/login" in r.headers.get("Location", "")


# ─── require_auth: rutas protegidas sin sesion ─────────────────────────────

class TestRequireAuth:
    def test_index_shows_landing_page_when_anonymous(self, client):
        """'/' ya no redirige a /login estando anonimo — muestra la landing publica."""
        r = client.get("/")
        assert r.status_code == 200
        assert b"Differential" in r.data
        assert b"Crear cuenta" in r.data

    def test_index_shows_chat_when_authenticated(self, client):
        client.post("/auth/signup", json={"email": "chat@example.com", "password": "password123"})
        r = client.get("/")
        assert r.status_code == 200
        assert b"chatZone" in r.data

    def test_api_route_returns_401_json_when_anonymous(self, client):
        r = client.get("/api/health")
        assert r.status_code == 401
        assert "error" in r.get_json()

    def test_login_page_redirects_to_index_when_already_authenticated(self, client):
        client.post("/auth/signup", json={"email": "ya@example.com", "password": "password123"})
        r = client.get("/login")
        assert r.status_code == 302
