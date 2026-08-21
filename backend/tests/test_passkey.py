import pytest
from fastapi.testclient import TestClient

from retentionpulse_api.main import app


pytest.importorskip("webauthn")


def test_passkey_registration_options_returns_public_key_payload():
    client = TestClient(app)
    token = client.get("/api/auth/csrf/").json()["csrfToken"]
    response = client.post(
        "/api/auth/passkey/register/options/",
        headers={"X-CSRFToken": token},
        json={"name": "My work laptop"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["rp"]["id"]
    assert payload["user"]["name"] == "My work laptop"
    assert payload["challenge"]
