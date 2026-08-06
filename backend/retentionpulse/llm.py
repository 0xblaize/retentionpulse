from __future__ import annotations

import json
import os
from typing import Any

import httpx


def generate_ai_repair_plan(
    *,
    duration: float,
    risk_seconds: float,
    health_score: int,
    segments: list[dict[str, Any]],
    suggestions: list[dict[str, Any]],
) -> str | None:
    endpoint = os.getenv("RETENTIONPULSE_LLM_API_URL", "").strip()
    api_key = os.getenv("RETENTIONPULSE_LLM_API_KEY", "").strip()
    model = os.getenv("RETENTIONPULSE_LLM_MODEL", "gpt-4o-mini").strip()
    if not endpoint or not api_key:
        return None

    facts = {
        "duration_seconds": round(duration, 2),
        "health_score": health_score,
        "risk_seconds": round(risk_seconds, 2),
        "risk_segments": segments,
        "deterministic_suggestions": suggestions,
    }
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": "You are a concise video editor. Turn visual retention findings into a practical repair plan. Do not invent timestamps or facts. Return 3 to 5 short numbered actions.",
            },
            {
                "role": "user",
                "content": json.dumps(facts, separators=(",", ":")),
            },
        ],
    }
    try:
        response = httpx.post(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=httpx.Timeout(30.0, connect=5.0),
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return content.strip() if isinstance(content, str) and content.strip() else None
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        return None
