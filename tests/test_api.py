from fastapi.testclient import TestClient

from api import app

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
