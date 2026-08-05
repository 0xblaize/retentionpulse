from django.test import Client


def test_passkey_registration_options_returns_public_key_payload():
    response = Client().post("/api/auth/passkey/register/options/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["rp"]["id"] == "127.0.0.1"
    assert payload["user"]["id"]
    assert payload["challenge"]


def test_passkey_authentication_options_returns_public_key_payload():
    response = Client().post("/api/auth/passkey/authenticate/options/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["rpId"] == "127.0.0.1"
    assert payload["challenge"]
