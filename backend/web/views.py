from __future__ import annotations

import base64
import json
import secrets
from functools import wraps
from typing import Any, Callable

import httpx
from django.conf import settings
from django.middleware.csrf import get_token
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from urllib.parse import urlparse

from .models import PasskeyCredential


def protected(view: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    @wraps(view)
    def wrapped(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.session.get("authenticated", False):
            if request.path.startswith("/api/"):
                return JsonResponse({"detail": "Authentication required."}, status=401)
            return redirect("login")
        return view(request, *args, **kwargs)

    return wrapped


def landing(request: HttpRequest) -> HttpResponse:
    frontend_entry = settings.FRONTEND_DIR / "dist" / "index.html"
    if frontend_entry.exists():
        return render(request, "index.html")
    return render(request, "web/landing.html")


@ensure_csrf_cookie
def csrf_bootstrap(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"ok": True, "csrfToken": get_token(request)})


def auth_session(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"authenticated": bool(request.session.get("authenticated", False))})


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
            PublicKeyCredentialRpEntity,
            PublicKeyCredentialUserEntity,
            UserVerificationRequirement,
        )
    except ImportError:
        return None
    return locals()


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _webauthn_error() -> JsonResponse:
    return JsonResponse({"detail": "Passkey support is not installed on the server."}, status=503)


def _get_webauthn_origin(request: HttpRequest) -> str:
    origin = request.META.get("HTTP_ORIGIN") or request.META.get("HTTP_REFERER") or ""
    if origin:
        parsed = urlparse(origin)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    return settings.RETENTIONPULSE_ORIGIN


def _get_webauthn_rp_id(request: HttpRequest) -> str:
    origin = _get_webauthn_origin(request)
    parsed = urlparse(origin)
    if parsed.hostname:
        return parsed.hostname
    return settings.RETENTIONPULSE_RP_ID


def _get_passkey_name(request: HttpRequest) -> str:
    payload: Any = {}
    if request.content_type == "application/json":
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = {}
    elif request.POST:
        payload = request.POST
    if isinstance(payload, dict):
        name = payload.get("name")
        if isinstance(name, str):
            name = name.strip()
            if name:
                return name
    return settings.RETENTIONPULSE_RP_NAME or "RetentionPulse"


@require_POST
def passkey_register_options(request: HttpRequest) -> JsonResponse:
    api = _webauthn()
    if api is None:
        return _webauthn_error()
    if PasskeyCredential.objects.exists() and not request.session.get("authenticated", False):
        return JsonResponse({"detail": "A passkey is already registered for this workspace."}, status=403)
    user_handle = secrets.token_bytes(32)
    display_name = _get_passkey_name(request)
    options = api["generate_registration_options"](
        rp_id=_get_webauthn_rp_id(request),
        rp_name=settings.RETENTIONPULSE_RP_NAME,
        user_id=user_handle,
        user_name=display_name,
        user_display_name=display_name,
        authenticator_selection=api["AuthenticatorSelectionCriteria"](user_verification=api["UserVerificationRequirement"].REQUIRED),
        timeout=settings.RETENTIONPULSE_WEBAUTHN_TIMEOUT_MS,
    )
    request.session["passkey_registration_challenge"] = _b64(options.challenge)
    request.session["passkey_registration_user_handle"] = _b64(user_handle)
    request.session["passkey_registration_name"] = display_name
    return JsonResponse(json.loads(api["options_to_json"](options)))


@require_POST
def passkey_register_verify(request: HttpRequest) -> JsonResponse:
    api = _webauthn()
    if api is None:
        return _webauthn_error()
    challenge = request.session.pop("passkey_registration_challenge", None)
    user_handle = request.session.pop("passkey_registration_user_handle", None)
    name = request.session.pop("passkey_registration_name", None)
    if not challenge or not user_handle:
        return JsonResponse({"detail": "Passkey registration expired. Start again."}, status=400)
    try:
        credential = api["parse_registration_credential_json"](request.body.decode("utf-8"))
        verification = api["verify_registration_response"](
            credential=credential,
            expected_challenge=_unb64(challenge),
            expected_rp_id=_get_webauthn_rp_id(request),
            expected_origin=_get_webauthn_origin(request),
            require_user_verification=True,
        )
        PasskeyCredential.objects.create(
            credential_id=verification.credential_id,
            public_key=verification.credential_public_key,
            user_handle=_unb64(user_handle),
            name=name or settings.RETENTIONPULSE_RP_NAME or "RetentionPulse",
            sign_count=verification.sign_count,
            transports=list(getattr(credential.response, "transports", None) or []),
        )
    except Exception as exc:
        return JsonResponse({"detail": f"The passkey registration could not be verified: {exc}"}, status=400)
    request.session.cycle_key()
    request.session["authenticated"] = True
    return JsonResponse({"authenticated": True})


@require_POST
def passkey_auth_options(request: HttpRequest) -> JsonResponse:
    api = _webauthn()
    if api is None:
        return _webauthn_error()
    credentials = [
        api["PublicKeyCredentialDescriptor"](id=credential.credential_id)
        for credential in PasskeyCredential.objects.filter(disabled=False)
    ]
    options = api["generate_authentication_options"](
        rp_id=_get_webauthn_rp_id(request),
        allow_credentials=credentials or None,
        user_verification=api["UserVerificationRequirement"].REQUIRED,
        timeout=settings.RETENTIONPULSE_WEBAUTHN_TIMEOUT_MS,
    )
    request.session["passkey_authentication_challenge"] = _b64(options.challenge)
    return JsonResponse(json.loads(api["options_to_json"](options)))


@require_POST
def passkey_auth_verify(request: HttpRequest) -> JsonResponse:
    api = _webauthn()
    if api is None:
        return _webauthn_error()
    challenge = request.session.pop("passkey_authentication_challenge", None)
    if not challenge:
        return JsonResponse({"detail": "Passkey authentication expired. Start again."}, status=400)
    try:
        credential = api["parse_authentication_credential_json"](request.body.decode("utf-8"))
        stored = PasskeyCredential.objects.get(credential_id=credential.raw_id, disabled=False)
        verification = api["verify_authentication_response"](
            credential=credential,
            expected_challenge=_unb64(challenge),
            expected_rp_id=_get_webauthn_rp_id(request),
            expected_origin=_get_webauthn_origin(request),
            credential_public_key=bytes(stored.public_key),
            credential_current_sign_count=stored.sign_count,
            require_user_verification=True,
        )
        stored.sign_count = verification.new_sign_count
        stored.last_used_at = timezone.now()
        stored.save(update_fields=["sign_count", "last_used_at"])
    except Exception:
        return JsonResponse({"detail": "The passkey assertion could not be verified."}, status=401)
    request.session.cycle_key()
    request.session["authenticated"] = True
    return JsonResponse({"authenticated": True})


@require_POST
def auth_logout(request: HttpRequest) -> JsonResponse:
    request.session.flush()
    return JsonResponse({"authenticated": False})


def login_view(request: HttpRequest) -> HttpResponse:
    return render(request, "web/login.html", {"frontend_url": settings.RETENTIONPULSE_FRONTEND_URL})


def logout_view(request: HttpRequest) -> HttpResponse:
    request.session.flush()
    return redirect("landing")


@protected
def dashboard(request: HttpRequest) -> HttpResponse:
    frontend_entry = settings.FRONTEND_DIR / "dist" / "index.html"
    if frontend_entry.exists():
        return render(request, "index.html")
    return render(request, "web/dashboard.html", {"analysis": request.session.get("analysis")})


def _forward_analysis(video: Any, mode: str = "auto") -> tuple[int, dict[str, Any]]:
    timeout = 60.0 if mode in {"fast_preview", "visual"} else 180.0
    response = httpx.post(
        f"{settings.RETENTIONPULSE_API_URL}/analyze",
        files={"video": (video.name, video.file, video.content_type or "application/octet-stream")},
        data={"mode": mode},
        timeout=httpx.Timeout(timeout, connect=10.0),
    )
    try:
        payload = response.json()
    except ValueError:
        payload = {"detail": "The analysis service returned an invalid response."}
    return response.status_code, payload


@require_POST
@protected
def analyze_api(request: HttpRequest) -> JsonResponse:
    video = request.FILES.get("video")
    if video is None:
        return JsonResponse({"detail": "Choose a video before scanning."}, status=400)
    try:
        status_code, payload = _forward_analysis(video, request.POST.get("mode", "auto"))
    except httpx.HTTPError:
        return JsonResponse({"detail": "The analysis service is unavailable. Start FastAPI and try again."}, status=502)
    if status_code >= 400:
        return JsonResponse(payload, status=status_code)
    request.session["analysis"] = payload
    return JsonResponse(payload)


@require_POST
@protected
def analyze(request: HttpRequest) -> HttpResponse:
    video = request.FILES.get("video")
    if video is None:
        return render(request, "web/dashboard.html", {"error": "Choose a video before scanning."}, status=400)
    try:
        status_code, payload = _forward_analysis(video, request.POST.get("mode", "auto"))
    except httpx.HTTPError:
        return render(request, "web/dashboard.html", {"error": "The analysis service is unavailable. Start FastAPI and try again."}, status=502)
    if status_code >= 400:
        return render(request, "web/dashboard.html", {"error": payload.get("detail", "The analysis service rejected this upload.")}, status=status_code)
    request.session["analysis"] = payload
    return redirect("dashboard")
