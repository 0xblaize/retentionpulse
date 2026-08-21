from fastapi.testclient import TestClient

from retentionpulse_api.main import app


def csrf_client() -> tuple[TestClient, str]:
    client = TestClient(app)
    token = client.get("/api/auth/csrf/").json()["csrfToken"]
    return client, token


def test_session_api_starts_unauthenticated():
    response = TestClient(app).get("/api/auth/session/")
    assert response.status_code == 200
    assert response.json() == {"authenticated": False}


def test_logout_api_clears_session():
    client, token = csrf_client()
    response = client.post("/api/auth/logout/", headers={"X-CSRFToken": token})
    assert response.status_code == 200
    assert response.json() == {"authenticated": False}
    assert client.get("/api/auth/session/").json()["authenticated"] is False


def test_analyze_api_requires_authentication():
    response = TestClient(app).post("/api/analyze/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."
