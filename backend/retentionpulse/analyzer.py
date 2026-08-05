from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np


@dataclass(frozen=True)
class FrameSample:
    timestamp: float
    frame: np.ndarray


@dataclass(frozen=True)
class StaticSegment:
    start: float
    end: float
    duration: float
    confidence: float


@dataclass(frozen=True)
class AnalysisResult:
    duration: float
    samples: tuple[FrameSample, ...]
    motion_scores: tuple[float, ...]
    static_segments: tuple[StaticSegment, ...]


def normalize_frame(frame: np.ndarray, size: tuple[int, int] = (160, 90)) -> np.ndarray:
    grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.resize(grayscale, size, interpolation=cv2.INTER_AREA)


def frame_difference(previous: np.ndarray, current: np.ndarray) -> float:
    if previous.shape != current.shape:
        raise ValueError("Frames must have the same shape")
    return float(np.mean(cv2.absdiff(previous, current)) / 255.0)


def detect_static_segments(
    timestamps: Sequence[float],
    motion_scores: Sequence[float],
    *,
    static_threshold: float = 0.015,
    min_duration: float = 6.0,
    sample_interval: float = 0.5,
) -> tuple[StaticSegment, ...]:
    if len(timestamps) != len(motion_scores):
        raise ValueError("Timestamps and motion scores must have the same length")
    if not timestamps:
        return ()

    segments: list[StaticSegment] = []
    run_start: int | None = None

    for index, score in enumerate(motion_scores):
        is_static = index > 0 and score <= static_threshold
        if is_static and run_start is None:
            run_start = index - 1
        if run_start is not None and (not is_static or index == len(motion_scores) - 1):
            end_index = index if is_static and index == len(motion_scores) - 1 else index - 1
            start = float(timestamps[run_start])
            end = float(timestamps[end_index] + sample_interval)
            duration = end - start
            if duration > min_duration:
                run_scores = motion_scores[run_start + 1 : end_index + 1]
                confidence = float(1.0 - min(np.mean(run_scores) / max(static_threshold, 1e-9), 1.0))
                segments.append(StaticSegment(start, end, duration, confidence))
            run_start = None

    return tuple(segments)


def sample_video(video_path: str | Path, interval_seconds: float = 0.5) -> tuple[float, tuple[FrameSample, ...]]:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError("Unable to open video")

    fps = float(capture.get(cv2.CAP_PROP_FPS))
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 and frame_count > 0 else 0.0
    if duration <= 0:
        capture.release()
        raise ValueError("Video has no readable duration")

    samples: list[FrameSample] = []
    timestamp = 0.0
    while timestamp < duration:
        capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000.0)
        success, frame = capture.read()
        if success:
            samples.append(FrameSample(timestamp, normalize_frame(frame)))
        timestamp += interval_seconds
    capture.release()

    if len(samples) < 2:
        raise ValueError("Video does not contain enough readable frames")
    return duration, tuple(samples)


def analyze_video(
    video_path: str | Path,
    *,
    interval_seconds: float = 0.5,
    static_threshold: float = 0.015,
    min_duration: float = 6.0,
) -> AnalysisResult:
    duration, samples = sample_video(video_path, interval_seconds)
    timestamps = tuple(sample.timestamp for sample in samples)
    scores = [0.0]
    scores.extend(frame_difference(previous.frame, current.frame) for previous, current in zip(samples, samples[1:]))
    segments = detect_static_segments(
        timestamps,
        scores,
        static_threshold=static_threshold,
        min_duration=min_duration,
        sample_interval=interval_seconds,
    )
    return AnalysisResult(duration, samples, tuple(scores), segments)
