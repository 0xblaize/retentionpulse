from __future__ import annotations

from pathlib import Path
from typing import Any

from .analyzer import analyze_video
from .llm import generate_ai_repair_plan
from .suggestions import generate_repair_suggestions


def analyze_video_json(video_path: str | Path) -> dict[str, Any]:
    result = analyze_video(video_path)
    suggestions = generate_repair_suggestions(result.static_segments)
    risk_seconds = sum(segment.duration for segment in result.static_segments)
    risk_ratio = risk_seconds / result.duration if result.duration else 0.0

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
    health_score = max(0, round((1.0 - risk_ratio) * 100))
    ai_repair_plan = generate_ai_repair_plan(
        duration=result.duration,
        risk_seconds=risk_seconds,
        health_score=health_score,
        segments=segments,
        suggestions=suggestion_payload,
    )
    timeline = [
        {
            "timestamp": sample.timestamp,
            "position": (sample.timestamp / result.duration * 100) if result.duration else 0.0,
            "motion_score": score,
            "risk": any(segment.start <= sample.timestamp < segment.end for segment in result.static_segments),
        }
        for sample, score in zip(result.samples, result.motion_scores)
    ]
    return {
        "duration": result.duration,
        "risk_seconds": risk_seconds,
        "risk_ratio": risk_ratio,
        "health_score": health_score,
        "segments": segments,
        "suggestions": suggestion_payload,
        "ai_repair_plan": ai_repair_plan,
        "timeline": timeline,
    }
