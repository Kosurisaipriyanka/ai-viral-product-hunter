from fastapi.testclient import TestClient

import api
from api import app
from scoring import score_trend_items

client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_products_endpoint_returns_sample_data():
    response = client.get("/products")
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "sample_data"
    assert body["count"] > 0
    assert all(item["source"] == "Sample data" for item in body["products"])


def test_products_can_be_filtered_by_category():
    response = client.get("/products", params={"category": "Pet Gadgets"})
    assert response.status_code == 200
    body = response.json()
    assert body["count"] > 0
    assert all(item["category"] == "Pet Gadgets" for item in body["products"])


def test_unknown_category_returns_empty_list():
    response = client.get("/products", params={"category": "Not a category"})
    assert response.status_code == 200
    assert response.json()["products"] == []


def test_trends_endpoint_handles_empty_keywords_without_network_call():
    response = client.get("/trends", params={"keywords": ""})
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "Google Trends"
    assert body["items"] == []


def test_catalog_endpoint_rejects_empty_query():
    response = client.get("/catalog", params={"query": ""})
    assert response.status_code == 422


def test_score_trend_items_calculates_bounded_score():
    result = score_trend_items([{
        "keyword": "travel accessories",
        "latest_interest": 50,
        "previous_interest": 40,
        "change_percent": 25.0,
    }])[0]
    # Momentum=(25+100)/2=62.5; score=70%*50 + 30%*62.5 = 53.75.
    assert result["opportunity_score"] == 53.8
    assert result["score_status"] == "experimental trend-only heuristic"


def test_score_is_unavailable_when_momentum_cannot_be_calculated():
    result = score_trend_items([{
        "keyword": "pet gadgets",
        "latest_interest": 0,
        "previous_interest": 0,
        "change_percent": None,
    }])[0]
    assert result["opportunity_score"] is None
    assert result["score_status"] == "insufficient trend history"


def test_opportunities_endpoint_scores_returned_trend_items(monkeypatch):
    monkeypatch.setattr(api, "fetch_google_trends", lambda keywords, geo="IN": {
        "source": "Google Trends",
        "geo": geo,
        "items": [{
            "keyword": "home organization",
            "latest_interest": 60,
            "previous_interest": 50,
            "change_percent": 20.0,
            "points": 93,
        }],
        "note": "test data",
    })
    response = client.get("/opportunities", params={"keywords": "home organization"})
    assert response.status_code == 200
    body = response.json()
    # Momentum=(20+100)/2=60; both latest and momentum components equal 60.
    assert body["items"][0]["opportunity_score"] == 60.0
    assert "not a prediction" in body["score_method"]["warning"]



def test_youtube_search_requires_local_api_key(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "")
    response = client.get("/youtube/search", params={"query": "portable blender"})
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "YouTube Data API v3"
    assert body["items"] == []
    assert "YOUTUBE_API_KEY" in body["error"]


def test_youtube_search_rejects_empty_query():
    response = client.get("/youtube/search", params={"query": ""})
    assert response.status_code == 422
