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


class AnalysisResponse(BaseModel):
    duration: float
    risk_seconds: float
    risk_ratio: float
    health_score: int
    segments: list[Segment]
    suggestions: list[Suggestion]
    ai_repair_plan: str | None = None
    timeline: list[TimelinePoint]
