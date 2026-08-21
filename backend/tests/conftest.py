from retentionpulse_api.main import app

from fastapi.testclient import TestClient


def client():
	return TestClient(app)
