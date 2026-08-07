from __future__ import annotations

from pydantic import BaseModel, Field


class Segment(BaseModel):
    start: float
    end: float
    duration: float
    confidence: float = Field(ge=0, le=1)


class Suggestion(BaseModel):
    timestamp: float
    action: str
    detail: str
    priority: str


class TimelinePoint(BaseModel):
    timestamp: float
    position: float = Field(ge=0, le=100)
    motion_score: float
    risk: bool


class SpeechMetrics(BaseModel):
    speech_ratio: float
    pause_count: int
    long_pause_count: int
    pause_density: float
    average_energy: float
    energy_variance: float
    words_per_minute: float


class ZonePoint(BaseModel):
    timestamp: float
    position: float
    visual_motion: float
    audio_energy: float
    semantic_drift: float | None = None
    attention_risk: float
    zone: str
    reasons: list[str]


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str
    words: list[dict[str, float | str]] = []


class RemediationAction(BaseModel):
    id: str
    start: float
    end: float
    severity: str
    category: str
    edit_type: str
    title: str
    rationale: str
    instruction: str
    priority: str


class AnalysisResponse(BaseModel):
    duration: float
    risk_seconds: float
    risk_ratio: float
    health_score: int
    segments: list[Segment]
    suggestions: list[Suggestion]
    ai_repair_plan: str | None = None
    timeline: list[TimelinePoint]
    analyzer_version: str | None = None
    mode: str | None = None
    capabilities: dict[str, bool] | None = None
    warnings: list[str] = []
    transcript: list[TranscriptSegment] = []
    speech_metrics: SpeechMetrics | None = None
    timeline_zones: list[ZonePoint] = []
    remediation_actions: list[RemediationAction] = []
