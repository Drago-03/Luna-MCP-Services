from fastapi.testclient import TestClient
from mcp_bearer_token import app


def test_health_endpoint():
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    for name in ["code_gen", "git_clone", "img_bw"]:
        assert name in data["tools"]
