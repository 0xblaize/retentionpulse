import json
from types import SimpleNamespace

import pytest
from django.conf import settings
from django.test import Client, override_settings

from web.models import PasskeyCredential

pytestmark = pytest.mark.django_db

@override_settings(RETENTIONPULSE_RP_ID="127.0.0.1", RETENTIONPULSE_ORIGIN="http://testserver")
def test_passkey_registration_options_returns_public_key_payload():
    response = Client().post("/api/auth/passkey/register/options/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["rp"]["id"] == "testserver"
    assert payload["user"]["id"]
    assert payload["challenge"]


@override_settings(RETENTIONPULSE_RP_ID="127.0.0.1", RETENTIONPULSE_ORIGIN="http://testserver")
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


@override_settings(RETENTIONPULSE_RP_ID="127.0.0.1", RETENTIONPULSE_ORIGIN="http://testserver")
def test_passkey_registration_verify_stores_the_selected_name(monkeypatch):
    client = Client()
    session = client.session
    session["passkey_registration_challenge"] = "YWJj"
    session["passkey_registration_user_handle"] = "ZGVm"
    session["passkey_registration_name"] = "My work laptop"
    session.save()
    client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

    class DummyCredential:
        response = SimpleNamespace(transports=["usb"])

    def fake_webauthn():
        return {
            "parse_registration_credential_json": lambda body: DummyCredential(),
            "verify_registration_response": lambda **kwargs: SimpleNamespace(
                credential_id=b"credential-id",
                credential_public_key=b"public-key",
                sign_count=1,
            ),
        }

    monkeypatch.setattr("web.views._webauthn", fake_webauthn)

    response = client.post(
        "/api/auth/passkey/register/verify/",
        data=json.dumps({"id": "abc", "rawId": "abc", "type": "public-key", "response": {}}),
        content_type="application/json",
    )

    assert response.status_code == 200
    credential = PasskeyCredential.objects.get(credential_id=b"credential-id")
    assert credential.name == "My work laptop"


@override_settings(RETENTIONPULSE_RP_ID="127.0.0.1", RETENTIONPULSE_ORIGIN="http://testserver")
def test_passkey_authentication_options_returns_public_key_payload():
    response = Client().post("/api/auth/passkey/authenticate/options/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["rpId"] == "testserver"
    assert payload["challenge"]
