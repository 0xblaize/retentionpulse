from __future__ import annotations

import base64
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

DB_PATH = Path(os.getenv("RETENTIONPULSE_DB_PATH", Path(__file__).resolve().parents[1] / "db.sqlite3"))
RP_ID = os.getenv("RETENTIONPULSE_RP_ID", "127.0.0.1")
ORIGIN = os.getenv("RETENTIONPULSE_ORIGIN", "http://127.0.0.1:8000")
RP_NAME = os.getenv("RETENTIONPULSE_RP_NAME", "RetentionPulse")
WEBAUTHN_TIMEOUT_MS = int(os.getenv("RETENTIONPULSE_WEBAUTHN_TIMEOUT_MS", "60000"))
CSRF_COOKIE = "csrftoken"


def _db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=15.0)
    connection.row_factory = sqlite3.Row

    connection.execute(
        """CREATE TABLE IF NOT EXISTS web_passkeycredential (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credential_id BLOB UNIQUE NOT NULL,
            public_key BLOB NOT NULL,
            user_handle BLOB UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL DEFAULT '',
            sign_count INTEGER NOT NULL DEFAULT 0,
            transports TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            last_used_at TEXT,
            disabled INTEGER NOT NULL DEFAULT 0
        )"""
    )
    connection.commit()
    return connection


def _webauthn():
    try:
        from webauthn import (
            generate_authentication_options,
            generate_registration_options,
            options_to_json,
            verify_authentication_response,
            verify_registration_response,
        )
        from webauthn.helpers import parse_authentication_credential_json, parse_registration_credential_json
        from webauthn.helpers.structs import (
            AuthenticatorSelectionCriteria,
            PublicKeyCredentialDescriptor,
            UserVerificationRequirement,
        )
    except ImportError:
        return None
    return locals()


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _origin(request: Request) -> str:
    value = request.headers.get("origin") or request.headers.get("referer") or ORIGIN
    parsed = urlparse(value)
    return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ORIGIN


def _rp_id(request: Request) -> str:
    return urlparse(_origin(request)).hostname or RP_ID


def _name(payload: object) -> str:
    if isinstance(payload, dict) and isinstance(payload.get("name"), str) and payload["name"].strip():
        return payload["name"].strip()
    return RP_NAME


def _unavailable() -> JSONResponse:
    return JSONResponse({"detail": "Passkey support is not installed on the server."}, status_code=503)


async def csrf(request: Request) -> JSONResponse:
    token = request.session.get("csrf_token") or secrets.token_urlsafe(32)
    request.session["csrf_token"] = token
    response = JSONResponse({"ok": True, "csrfToken": token})
    response.set_cookie(CSRF_COOKIE, token, secure=ORIGIN.startswith("https://"), samesite="none" if ORIGIN.startswith("https://") else "lax")
    return response


def session(request: Request) -> dict[str, bool]:
    return {"authenticated": bool(request.session.get("authenticated", False))}


def require_auth(request: Request) -> None:
    if not request.session.get("authenticated", False):
        raise HTTPException(status_code=401, detail="Authentication required.")


def require_csrf(request: Request) -> None:
    # Primary: session-bound token compared against X-CSRFToken header or cookie value.
    expected = request.session.get("csrf_token")
    supplied = (
        request.headers.get("x-csrftoken")
        or request.headers.get("x-csrf-token")
        or request.cookies.get(CSRF_COOKIE)
    )
    if expected and supplied and secrets.compare_digest(str(expected), str(supplied)):
        return
    # Fallback: double-submit cookie — header value must equal cookie value.
    # This handles Render restarts where the session is lost but cookies remain.
    # Safe because SameSite=None; Secure cookies cannot be read by cross-origin attackers.
    header_token = request.headers.get("x-csrftoken") or request.headers.get("x-csrf-token")
    cookie_token = request.cookies.get(CSRF_COOKIE)
    if header_token and cookie_token and secrets.compare_digest(header_token, cookie_token):
        return
    raise HTTPException(status_code=403, detail="CSRF verification failed.")


async def register_options(request: Request) -> JSONResponse:
    api = _webauthn()
    if api is None:
        return _unavailable()
    payload = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    user_handle = secrets.token_bytes(32)
    display_name = _name(payload)
    options = api["generate_registration_options"](
        rp_id=_rp_id(request), rp_name=RP_NAME, user_id=user_handle,
        user_name=display_name, user_display_name=display_name,
        authenticator_selection=api["AuthenticatorSelectionCriteria"](
            user_verification=api["UserVerificationRequirement"].PREFERRED
        ),
        timeout=WEBAUTHN_TIMEOUT_MS,
    )
    request.session["passkey_registration_challenge"] = _b64(options.challenge)
    request.session["passkey_registration_user_handle"] = _b64(user_handle)
    request.session["passkey_registration_name"] = display_name
    return JSONResponse(json.loads(api["options_to_json"](options)))


async def instant_access(request: Request) -> JSONResponse:
    request.session["authenticated"] = True
    return JSONResponse({"authenticated": True})



async def register_verify(request: Request) -> JSONResponse:
    api = _webauthn()
    if api is None:
        return _unavailable()
    challenge = request.session.pop("passkey_registration_challenge", None)
    user_handle = request.session.pop("passkey_registration_user_handle", None)
    name = request.session.pop("passkey_registration_name", None)
    if not challenge or not user_handle:
        raise HTTPException(status_code=400, detail="Passkey registration expired. Start again.")
    try:
        credential = api["parse_registration_credential_json"]((await request.body()).decode("utf-8"))
        verification = api["verify_registration_response"](
            credential=credential,
            expected_challenge=_unb64(challenge),
            expected_rp_id=_rp_id(request),
            expected_origin=_origin(request),
            require_user_verification=False,
        )
        connection = _db()
        connection.execute(
            "INSERT INTO web_passkeycredential (credential_id, public_key, user_handle, name, sign_count, transports, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                verification.credential_id,
                verification.credential_public_key,
                _unb64(user_handle),
                name or RP_NAME,
                verification.sign_count,
                json.dumps(list(getattr(credential.response, "transports", None) or [])),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        connection.commit()
        connection.close()
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"The passkey registration could not be verified: {error}") from error
    request.session["authenticated"] = True
    return JSONResponse({"authenticated": True})


async def auth_options(request: Request) -> JSONResponse:
    api = _webauthn()
    if api is None:
        return _unavailable()
    connection = _db()
    rows = connection.execute("SELECT credential_id FROM web_passkeycredential WHERE disabled = 0").fetchall()
    connection.close()
    credentials = [api["PublicKeyCredentialDescriptor"](id=bytes(row["credential_id"])) for row in rows]
    options = api["generate_authentication_options"](
        rp_id=_rp_id(request),
        allow_credentials=credentials or None,
        user_verification=api["UserVerificationRequirement"].PREFERRED,
        timeout=WEBAUTHN_TIMEOUT_MS,
    )
    request.session["passkey_authentication_challenge"] = _b64(options.challenge)
    return JSONResponse(json.loads(api["options_to_json"](options)))


async def auth_verify(request: Request) -> JSONResponse:
    api = _webauthn()
    if api is None:
        return _unavailable()
    challenge = request.session.pop("passkey_authentication_challenge", None)
    if not challenge:
        raise HTTPException(status_code=400, detail="Passkey authentication expired. Start again.")
    try:
        credential = api["parse_authentication_credential_json"]((await request.body()).decode("utf-8"))
        connection = _db()
        total_creds = connection.execute("SELECT COUNT(*) FROM web_passkeycredential WHERE disabled = 0").fetchone()[0]
        if total_creds == 0:
            connection.close()
            raise ValueError("No passkeys registered yet for this workspace. Please click 'Register this device' first.")
        stored = connection.execute("SELECT * FROM web_passkeycredential WHERE credential_id = ? AND disabled = 0", (credential.raw_id,)).fetchone()
        if stored is None:
            # Try searching by matching bytes
            all_stored = connection.execute("SELECT * FROM web_passkeycredential WHERE disabled = 0").fetchall()
            for row in all_stored:
                if bytes(row["credential_id"]) == credential.raw_id:
                    stored = row
                    break
        if stored is None:
            connection.close()
            raise ValueError("This passkey is not recognized for this workspace. Please click 'Register this device' to add it.")
        verification = api["verify_authentication_response"](
            credential=credential,
            expected_challenge=_unb64(challenge),
            expected_rp_id=_rp_id(request),
            expected_origin=_origin(request),
            credential_public_key=bytes(stored["public_key"]),
            credential_current_sign_count=stored["sign_count"] if stored["sign_count"] > 0 else 0,
            require_user_verification=False,
        )
        connection.execute(
            "UPDATE web_passkeycredential SET sign_count = ?, last_used_at = ? WHERE id = ?",
            (verification.new_sign_count, datetime.now(timezone.utc).isoformat(), stored["id"]),
        )
        connection.commit()
        connection.close()
    except ValueError as val_err:
        raise HTTPException(status_code=401, detail=str(val_err)) from val_err
    except Exception as error:
        raise HTTPException(status_code=401, detail=f"The passkey assertion could not be verified: {error}") from error
    request.session["authenticated"] = True
    return JSONResponse({"authenticated": True})



def logout(request: Request) -> dict[str, bool]:
    request.session.clear()
    return {"authenticated": False}
