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
    payload = service.analyze_video_json("video.mp4")
    assert payload["risk_seconds"] == 7.0
    assert payload["timeline"][0]["motion_score"] == 0.001
    assert "frame" not in payload["timeline"][0]
