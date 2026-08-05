from fastapi.testclient import TestClient

from retentionpulse_api.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_rejects_unsupported_extension():
    response = client.post("/analyze", files={"video": ("clip.txt", b"not video", "text/plain")})
    assert response.status_code == 400
