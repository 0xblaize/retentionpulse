import json

import pytest
from django.test import Client


pytestmark = pytest.mark.django_db

def test_passkey_registration_options_returns_public_key_payload():
    response = Client().post("/api/auth/passkey/register/options/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["rp"]["id"] == "127.0.0.1"
    assert payload["user"]["id"]
    assert payload["challenge"]


def test_passkey_registration_options_uses_provided_name():
    response = Client().post(
        "/api/auth/passkey/register/options/",
        data=json.dumps({"name": "My work laptop"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["name"] == "My work laptop"
    assert payload["user"]["displayName"] == "My work laptop"


def test_passkey_authentication_options_returns_public_key_payload():
    response = Client().post("/api/auth/passkey/authenticate/options/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["rpId"] == "127.0.0.1"
    assert payload["challenge"]
