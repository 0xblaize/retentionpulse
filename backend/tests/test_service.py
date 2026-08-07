from retentionpulse import service


def test_analysis_json_excludes_frame_arrays(monkeypatch):
    class Sample:
        timestamp = 0.0
        frame = object()

    class Segment:
        start = 0.0
        end = 7.0
        duration = 7.0
        confidence = 0.9

    class Result:
        duration = 10.0
        samples = (Sample(),)
        motion_scores = (0.001,)
        static_segments = (Segment(),)

    monkeypatch.setattr(service, "analyze_video", lambda _: Result())
    monkeypatch.setattr(service, "generate_repair_suggestions", lambda _: ())
    monkeypatch.setattr(service, "generate_ai_repair_plan", lambda **_: None)
    payload = service.analyze_video_json("video.mp4")
    assert payload["risk_seconds"] == 7.0
    assert payload["timeline"][0]["motion_score"] == 0.001
    assert "frame" not in payload["timeline"][0]


def test_analysis_passes_multimodal_evidence_to_advisor(monkeypatch):
    class Sample:
        timestamp = 0.0
        frame = object()

    class Result:
        duration = 10.0
        samples = (Sample(),)
        motion_scores = (0.001,)
        static_segments = ()

    captured = {}
    monkeypatch.setattr(service, "analyze_video", lambda _: Result())
    monkeypatch.setattr(service, "generate_repair_suggestions", lambda _: ())
    monkeypatch.setattr(service, "analyze_multimodal", lambda *_: {
        "transcript": [{"start": 1.0, "end": 2.0, "text": "Quantum physics"}],
        "speech_metrics": {"pause_count": 1},
        "timeline_zones": [{"timestamp": 1.0, "zone": "red"}],
        "remediation_actions": [{"id": "drift-1", "start": 1.0, "end": 4.0}],
    })

    def advisor(**kwargs):
        captured.update(kwargs)
        return "1. Add B-roll."

    monkeypatch.setattr(service, "generate_ai_repair_plan", advisor)
    payload = service.analyze_video_json("video.mp4", mode="multimodal")

    assert payload["ai_repair_plan"] == "1. Add B-roll."
    assert captured["transcript"][0]["text"] == "Quantum physics"
    assert captured["speech_metrics"]["pause_count"] == 1
    assert captured["timeline_zones"][0]["zone"] == "red"
    assert captured["remediation_actions"][0]["id"] == "drift-1"


def test_analysis_preserves_deterministic_payload_when_advisor_fails(monkeypatch):
    class Result:
        duration = 10.0
        samples = ()
        motion_scores = ()
        static_segments = ()

    monkeypatch.setattr(service, "analyze_video", lambda _: Result())
    monkeypatch.setattr(service, "generate_repair_suggestions", lambda _: ())
    monkeypatch.setattr(service, "generate_ai_repair_plan", lambda **_: None)
    payload = service.analyze_video_json("video.mp4", mode="visual")

    assert payload["ai_repair_plan"] is None
    assert payload["duration"] == 10.0
    assert payload["risk_seconds"] == 0
    assert payload["health_score"] == 100
