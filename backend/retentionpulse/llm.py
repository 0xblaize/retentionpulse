from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlparse

import httpx


DEFAULT_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"


def _chat_completions_url(value: str) -> str:
    value = value.rstrip("/")
    if value.endswith("/chat/completions"):
        return value
    return f"{value}/chat/completions"


def _is_local_url(value: str) -> bool:
    hostname = urlparse(value).hostname
    return hostname in {"localhost", "127.0.0.1", "::1"}


def _resolve_llm_provider() -> tuple[str, str, str] | None:
    configured_url = os.getenv("RETENTIONPULSE_LLM_API_URL", "").strip()
    offline = os.getenv("RETENTIONPULSE_OFFLINE_MODE", "1") == "1"
    if configured_url:
        url = _chat_completions_url(configured_url)
    elif offline:
        url = DEFAULT_GROQ_URL
    else:
        return None

    api_key = os.getenv("RETENTIONPULSE_LLM_API_KEY", "").strip()
    model = os.getenv("RETENTIONPULSE_LLM_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL
    if api_key or _is_local_url(url):
        return url, api_key, model
    return None


def _transcript_evidence(transcript: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "start": round(float(segment.get("start", 0.0)), 2),
            "end": round(float(segment.get("end", 0.0)), 2),
            "text": str(segment.get("text", ""))[:500],
        }
        for segment in transcript[:100]
    ]


def _zone_evidence(timeline_zones: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "timestamp": zone.get("timestamp"),
            "zone": zone.get("zone"),
            "attention_risk": zone.get("attention_risk"),
            "semantic_drift": zone.get("semantic_drift"),
            "reasons": zone.get("reasons", []),
        }
        for zone in timeline_zones
        if zone.get("zone") in {"yellow", "red"}
    ][:200]


def _action_evidence(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": action.get("id"),
            "start": action.get("start"),
            "end": action.get("end"),
            "severity": action.get("severity"),
            "category": action.get("category"),
            "edit_type": action.get("edit_type"),
            "instruction": action.get("instruction"),
        }
        for action in actions[:100]
    ]


def generate_ai_repair_plan(
    *,
    duration: float,
    risk_seconds: float,
    health_score: int,
    segments: list[dict[str, Any]],
    suggestions: list[dict[str, Any]],
    transcript: list[dict[str, Any]] | None = None,
    speech_metrics: dict[str, Any] | None = None,
    timeline_zones: list[dict[str, Any]] | None = None,
    remediation_actions: list[dict[str, Any]] | None = None,
) -> str | None:
    provider = _resolve_llm_provider()
    if provider is None:
        return None
    endpoint, api_key, model = provider
    facts = {
        "duration_seconds": round(duration, 2),
        "health_score": health_score,
        "risk_seconds": round(risk_seconds, 2),
        "risk_segments": segments[:100],
        "deterministic_suggestions": suggestions[:100],
        "transcript": _transcript_evidence(transcript or []),
        "speech_metrics": speech_metrics or {},
        "failing_timeline_zones": _zone_evidence(timeline_zones or []),
        "deterministic_remediation_actions": _action_evidence(remediation_actions or []),
    }
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": "You are a concise video editor. Use only the supplied diagnostic facts. Return 3 to 5 short numbered edit actions. Preserve supplied timestamps; never invent timestamps, faults, or facts.",
            },
            {"role": "user", "content": json.dumps(facts, separators=(",", ":"))},
        ],
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        response = httpx.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=httpx.Timeout(30.0, connect=5.0),
        )
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        return content.strip() if isinstance(content, str) and content.strip() else None
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        return None
