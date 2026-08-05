import numpy as np
import pytest

from retentionpulse.analyzer import detect_static_segments, frame_difference
from retentionpulse.suggestions import format_timestamp, generate_repair_suggestions


def test_identical_frames_have_zero_difference():
    frame = np.zeros((20, 20), dtype=np.uint8)
    assert frame_difference(frame, frame) == 0


def test_static_run_over_six_seconds_is_flagged():
    timestamps = [index * 0.5 for index in range(16)]
    scores = [0.0] + [0.001] * 15
    segments = detect_static_segments(timestamps, scores)
    assert len(segments) == 1
    assert segments[0].duration > 6
    assert segments[0].start == 0


def test_exactly_six_seconds_is_not_flagged():
    timestamps = [index * 0.5 for index in range(12)]
    scores = [0.0] + [0.001] * 11
    assert detect_static_segments(timestamps, scores) == ()


def test_motion_breaks_static_runs():
    timestamps = [index * 0.5 for index in range(30)]
    scores = [0.0] + [0.001] * 14 + [0.2] + [0.001] * 14
    segments = detect_static_segments(timestamps, scores)
    assert len(segments) == 2


def test_empty_inputs_are_safe():
    assert detect_static_segments([], []) == ()


def test_mismatched_inputs_fail():
    with pytest.raises(ValueError):
        detect_static_segments([0.0], [0.0, 0.1])


def test_suggestions_keep_segment_timestamp():
    timestamps = [0.0, 6.5]
    scores = [0.0, 0.001]
    segments = detect_static_segments(timestamps, scores, min_duration=0.5)
    suggestions = generate_repair_suggestions(segments)
    assert suggestions[0].timestamp == 0.0
    assert format_timestamp(102) == "1:42"
