from __future__ import annotations

from pathlib import Path
from typing import Any

from .analyzer import analyze_video
from .llm import generate_ai_repair_plan
from .multimodal import analyze_multimodal
from .suggestions import generate_repair_suggestions


def analyze_video_json(video_path: str | Path, *, mode: str = "auto") -> dict[str, Any]:
    if mode not in {"fast_preview", "visual", "multimodal", "auto"}:
        raise ValueError("Analysis mode must be fast_preview, visual, multimodal, or auto.")
    result = analyze_video(video_path)
    suggestions = generate_repair_suggestions(result.static_segments)
    visual_risk_seconds = sum(segment.duration for segment in result.static_segments)

    segments = [
        {
            "start": segment.start,
            "end": segment.end,
            "duration": segment.duration,
            "confidence": segment.confidence,
        }
        for segment in result.static_segments
    ]
    suggestion_payload = [
        {
            "timestamp": suggestion.timestamp,
            "action": suggestion.action,
            "detail": suggestion.detail,
            "priority": suggestion.priority,
        }
        for suggestion in suggestions
    ]
    timeline = [
        {
            "timestamp": sample.timestamp,
            "position": (sample.timestamp / result.duration * 100) if result.duration else 0.0,
            "motion_score": score,
            "risk": any(segment.start <= sample.timestamp < segment.end for segment in result.static_segments),
        }
        for sample, score in zip(result.samples, result.motion_scores)
    ]

    multimodal_payload: dict[str, Any] = {}
    if mode not in {"fast_preview", "visual"}:
        multimodal_payload = analyze_multimodal(video_path, result)

    # Incorporate audio pause risk into health score so a visually-moving video with
    # long dead-air silences does not score 100/100.
    audio_risk_seconds = 0.0
    remediation_actions = multimodal_payload.get("remediation_actions", [])
    for action in remediation_actions:
        if action.get("category") == "long_pause_or_silence":
            audio_risk_seconds += max(0.0, float(action.get("end", 0)) - float(action.get("start", 0)))

    risk_seconds = max(visual_risk_seconds, visual_risk_seconds + audio_risk_seconds * 0.5)
    risk_ratio = risk_seconds / result.duration if result.duration else 0.0
    health_score = max(0, round((1.0 - risk_ratio) * 100))

    # Always preserve the requested mode — do not let multimodal_payload overwrite it.
    multimodal_payload.pop("mode", None)

    payload: dict[str, Any] = {
        "duration": result.duration,
        "risk_seconds": risk_seconds,
        "risk_ratio": risk_ratio,
        "health_score": health_score,
        "segments": segments,
        "suggestions": suggestion_payload,
        "ai_repair_plan": None,
        "timeline": timeline,
        "mode": mode,
        "capabilities": {
            "visual": True,
            "audio": bool(multimodal_payload.get("speech_metrics")),
            "embeddings": bool(multimodal_payload.get("timeline_zones")),
        },
        **multimodal_payload,
    }
    if mode not in {"fast_preview", "visual"}:
        try:
            payload["ai_repair_plan"] = generate_ai_repair_plan(
                duration=result.duration,
                risk_seconds=risk_seconds,
                health_score=health_score,
                segments=segments,
                suggestions=suggestion_payload,
                transcript=multimodal_payload.get("transcript", []),
                speech_metrics=multimodal_payload.get("speech_metrics"),
                timeline_zones=multimodal_payload.get("timeline_zones", []),
                remediation_actions=multimodal_payload.get("remediation_actions", []),
            )
        except Exception:
            payload["ai_repair_plan"] = None
    return payload

