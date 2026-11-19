from fastapi.testclient import TestClient
from adaptive_router.main import app
from adaptive_router.learn import Learn, LearnUnavailable


def test_index_search():
    with TestClient(app) as client:
        assert client.get("/health").json()["indexed_entries"] > 100
        payload = client.post("/v1/search", json={"query":"upload_blob", "user_id":"public"}).json()
        assert payload["decision"]["route"] == "RAG"
        assert 0 < len(payload["results"]) <= 10
        assert all(hit["url"].startswith("https://learn.microsoft.com/") for hit in payload["results"])


def test_hybrid_preserves_local_results_on_outage(monkeypatch):
    async def unavailable(self, query, sources, user_id):
        assert sources == ["microsoft-learn"]
        raise LearnUnavailable
    monkeypatch.setattr(Learn, "search", unavailable)
    with TestClient(app) as client:
        payload = client.post("/v1/search", json={"query":"Python BlobClient and latest service limits", "user_id":"public"}).json()
        assert payload["decision"]["route"] == "HYBRID"
        assert payload["results"] and payload["warnings"]
