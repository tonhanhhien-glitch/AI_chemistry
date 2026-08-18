"""Login/logout/session-status for the single fixed admin account."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_wrong_username_rejected() -> None:
    response = client.post("/api/v1/admin/login", json={"username": "not-admin", "password": "admin@123"})
    assert response.status_code == 401
    assert "molecule_admin_session" not in response.cookies


def test_wrong_password_rejected() -> None:
    response = client.post("/api/v1/admin/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401
    assert "molecule_admin_session" not in response.cookies


def test_correct_credentials_accepted_and_cookie_issued() -> None:
    response = client.post("/api/v1/admin/login", json={"username": "admin", "password": "admin@123"})
    assert response.status_code == 200
    body = response.json()
    assert body == {"authenticated": True, "username": "admin"}
    assert "molecule_admin_session" in response.cookies


def test_session_status_reflects_login_state() -> None:
    anon = TestClient(app)
    assert anon.get("/api/v1/admin/session").json() == {"authenticated": False, "username": None}

    session_client = TestClient(app)
    session_client.post("/api/v1/admin/login", json={"username": "admin", "password": "admin@123"})
    assert session_client.get("/api/v1/admin/session").json() == {"authenticated": True, "username": "admin"}


def test_logout_invalidates_session() -> None:
    session_client = TestClient(app)
    session_client.post("/api/v1/admin/login", json={"username": "admin", "password": "admin@123"})
    assert session_client.get("/api/v1/admin/session").json()["authenticated"] is True

    logout = session_client.post("/api/v1/admin/logout")
    assert logout.status_code == 200
    assert logout.json() == {"authenticated": False, "username": None}
    assert session_client.get("/api/v1/admin/session").json()["authenticated"] is False
    assert session_client.get("/api/v1/admin/molecules").status_code == 401


def test_login_never_returns_or_leaks_the_password() -> None:
    response = client.post("/api/v1/admin/login", json={"username": "admin", "password": "admin@123"})
    assert "admin@123" not in response.text
