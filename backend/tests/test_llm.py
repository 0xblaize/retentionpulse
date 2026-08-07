import httpx

from retentionpulse import llm


class Response:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        return None

    def json(self):
        return self.body


def test_offline_defaults_to_groq(monkeypatch):
    captured = {}
    monkeypatch.setenv("RETENTIONPULSE_OFFLINE_MODE", "1")
    monkeypatch.delenv("RETENTIONPULSE_LLM_API_URL", raising=False)
    monkeypatch.setenv("RETENTIONPULSE_LLM_API_KEY", "groq-key")
    monkeypatch.setenv("RETENTIONPULSE_LLM_MODEL", "llama-3.3-70b-versatile")

    def post(url, **kwargs):
        captured.update(url=url, kwargs=kwargs)
        return Response({"choices": [{"message": {"content": "1. Cut the pause."}}]})

    monkeypatch.setattr(llm.httpx, "post", post)
    assert llm.generate_ai_repair_plan(duration=10, risk_seconds=2, health_score=80, segments=[], suggestions=[]) == "1. Cut the pause."
    assert captured["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer groq-key"


def test_cloud_override_requires_key_and_normalizes_url(monkeypatch):
    monkeypatch.setenv("RETENTIONPULSE_OFFLINE_MODE", "1")
    monkeypatch.setenv("RETENTIONPULSE_LLM_API_URL", "https://llm.example/v1")
    monkeypatch.setenv("RETENTIONPULSE_LLM_API_KEY", "secret")
    captured = {}
    monkeypatch.setattr(llm.httpx, "post", lambda url, **kwargs: (captured.update(url=url, kwargs=kwargs) or Response({"choices": [{"message": {"content": "plan"}}]})))

    assert llm.generate_ai_repair_plan(duration=1, risk_seconds=0, health_score=100, segments=[], suggestions=[]) == "plan"
    assert captured["url"] == "https://llm.example/v1/chat/completions"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer secret"


def test_remote_without_key_is_disabled(monkeypatch):
    monkeypatch.setenv("RETENTIONPULSE_OFFLINE_MODE", "1")
    monkeypatch.setenv("RETENTIONPULSE_LLM_API_URL", "https://llm.example/v1")
    monkeypatch.delenv("RETENTIONPULSE_LLM_API_KEY", raising=False)
    monkeypatch.setattr(llm.httpx, "post", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("request should not happen")))
    assert llm.generate_ai_repair_plan(duration=1, risk_seconds=0, health_score=100, segments=[], suggestions=[]) is None


def test_prompt_contains_multimodal_evidence(monkeypatch):
    captured = {}
    monkeypatch.setenv("RETENTIONPULSE_OFFLINE_MODE", "1")
    monkeypatch.delenv("RETENTIONPULSE_LLM_API_URL", raising=False)
    monkeypatch.setenv("RETENTIONPULSE_LLM_API_KEY", "groq-key")

    def post(_url, **kwargs):
        captured.update(kwargs)
        return Response({"choices": [{"message": {"content": "plan"}}]})

    monkeypatch.setattr(llm.httpx, "post", post)
    llm.generate_ai_repair_plan(
        duration=20,
        risk_seconds=4,
        health_score=70,
        segments=[],
        suggestions=[],
        transcript=[{"start": 12.5, "end": 14, "text": "Quantum physics"}],
        speech_metrics={"pause_count": 2},
        timeline_zones=[{"timestamp": 12.5, "zone": "red", "semantic_drift": 0.8, "reasons": ["semantic_drift"]}],
        remediation_actions=[{"id": "drift-1", "start": 12.5, "end": 16, "severity": "red", "category": "semantic_drift", "edit_type": "b_roll", "instruction": "Add server footage."}],
    )
    content = captured["json"]["messages"][1]["content"]
    assert "Quantum physics" in content
    assert "12.5" in content
    assert "semantic_drift" in content


def test_provider_failures_return_none(monkeypatch):
    monkeypatch.setenv("RETENTIONPULSE_OFFLINE_MODE", "1")
    monkeypatch.setenv("RETENTIONPULSE_LLM_API_KEY", "groq-key")
    monkeypatch.setattr(llm.httpx, "post", lambda *_args, **_kwargs: (_ for _ in ()).throw(httpx.ConnectError("offline")))
    assert llm.generate_ai_repair_plan(duration=1, risk_seconds=0, health_score=100, segments=[], suggestions=[]) is None

    monkeypatch.setattr(llm.httpx, "post", lambda *_args, **_kwargs: Response({"choices": []}))
    assert llm.generate_ai_repair_plan(duration=1, risk_seconds=0, health_score=100, segments=[], suggestions=[]) is None
