import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from blend.app import app


def test_api_search_returns_json_for_valid_query():
    client = app.test_client()
    response = client.get("/api/search?q=test&format=json")

    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, dict)
    assert "results" in payload
    assert "number_of_results" in payload
