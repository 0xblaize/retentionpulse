import json
import os
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/retentionpulse-test.sqlite3")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.test import Client
from web.models import PasskeyCredential
import web.views as views


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


views._webauthn = fake_webauthn

client = Client()
session = client.session
session["passkey_registration_challenge"] = "YWJj"
session["passkey_registration_user_handle"] = "ZGVm"
session["passkey_registration_name"] = "My work laptop"
session.save()

try:
    response = client.post(
        "/api/auth/passkey/register/verify/",
        data=json.dumps({"id": "abc", "rawId": "abc", "type": "public-key", "response": {}}),
        content_type="application/json",
        HTTP_ORIGIN="http://127.0.0.1:8000",
    )
    print("status", response.status_code)
    print(response.json())
    print("count", PasskeyCredential.objects.count())
    print("name", PasskeyCredential.objects.get().name)
except Exception as exc:
    import traceback

    traceback.print_exc()
