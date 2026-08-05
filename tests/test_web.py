from django.test import Client


def test_session_api_starts_unauthenticated():
    response = Client().get("/api/auth/session/")
    assert response.status_code == 200
    assert response.json() == {"authenticated": False}


def test_logout_api_clears_session():
    client = Client()
    session = client.session
    session["authenticated"] = True
    session.save()
    response = client.post("/api/auth/logout/")
    assert response.status_code == 200
    assert response.json() == {"authenticated": False}
    assert client.get("/api/auth/session/").json()["authenticated"] is False


def test_analyze_api_requires_authentication():
    response = Client().post("/api/analyze/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."
