from types import SimpleNamespace

from retentionpulse.multimodal import analyze_multimodal


def test_multimodal_falls_back_with_capability_warnings(monkeypatch):
    monkeypatch.setattr("retentionpulse.multimodal.shutil.which", lambda _: None)
    result = SimpleNamespace(
        duration=8.0,
        samples=(SimpleNamespace(timestamp=0.0), SimpleNamespace(timestamp=0.5)),
        motion_scores=(0.0, 0.02),
        static_segments=(),
    )

    payload = analyze_multimodal("video.mp4", result)

    assert payload["capabilities"]["visual"] is True
    assert payload["capabilities"]["audio"] is False
    assert payload["capabilities"]["transcription"] is False
    assert payload["capabilities"]["embeddings"] is False
    assert payload["warnings"]
    assert len(payload["timeline_zones"]) == 2


def test_multimodal_compiles_visual_remediation():
    result = SimpleNamespace(
        duration=20.0,
        samples=(SimpleNamespace(timestamp=0.0),),
        motion_scores=(0.001,),
        static_segments=(SimpleNamespace(start=0.0, end=7.0, duration=7.0, confidence=0.9),),
    )

    payload = analyze_multimodal("video.mp4", result)

    assert payload["remediation_actions"][0]["edit_type"] == "cut_or_b_roll"
    assert payload["remediation_actions"][0]["severity"] == "red"
