from __future__ import annotations

from dataclasses import dataclass

from .analyzer import StaticSegment


@dataclass(frozen=True)
class RepairSuggestion:
    timestamp: float
    action: str
    detail: str
    priority: str


def format_timestamp(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    minutes, remaining = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{remaining:02d}" if hours else f"{minutes}:{remaining:02d}"


def generate_repair_suggestions(segments: tuple[StaticSegment, ...]) -> tuple[RepairSuggestion, ...]:
    suggestions: list[RepairSuggestion] = []
    for segment in segments:
        timestamp = format_timestamp(segment.start)
        if segment.duration >= 12:
            action = "Cut or replace the shot"
            detail = f"{timestamp}: this static shot lasts {segment.duration:.1f}s. Add a cut, B-roll, or a tighter edit."
            priority = "High"
        elif segment.confidence >= 0.75:
            action = "Add B-roll or camera movement"
            detail = f"{timestamp}: visual change is very low for {segment.duration:.1f}s. Add motion, a zoom, or an overlay."
            priority = "High"
        else:
            action = "Review this transition"
            detail = f"{timestamp}: visual change is low for {segment.duration:.1f}s. Consider a cut or visual accent."
            priority = "Medium"
        suggestions.append(RepairSuggestion(segment.start, action, detail, priority))
    return tuple(suggestions)
