"""Public catalog connector used to develop the product-listing workflow.

DummyJSON provides mock product records for development. These are NOT live
marketplace listings, verified seller offers, or supplier quotes. Replace this
adapter with an authorized marketplace API when credentials/terms are available.
"""
from __future__ import annotations

from typing import Any

import requests

DUMMYJSON_PRODUCTS_URL = "https://dummyjson.com/products/search"


def search_public_catalog(query: str = "organizer", limit: int = 10) -> dict[str, Any]:
    """Search DummyJSON's public mock catalog and normalize returned product fields."""
    term = query.strip() or "organizer"
    safe_limit = max(1, min(int(limit), 30))
    try:
        response = requests.get(
            DUMMYJSON_PRODUCTS_URL,
            params={"q": term, "limit": safe_limit},
            timeout=12,
            headers={"User-Agent": "AI-Viral-Product-Hunter/0.2 (educational prototype)"},
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        return {
            "source": "DummyJSON mock catalog",
            "mode": "unavailable",
            "query": term,
            "count": 0,
            "products": [],
            "error": f"Public demo catalog request failed: {type(exc).__name__}",
        }

    products = []
    for item in payload.get("products", []):
        price = item.get("price")
        products.append({
            "id": item.get("id"),
            "name": item.get("title", "Untitled product"),
            "description": item.get("description", ""),
            "category": item.get("category", "Uncategorized"),
            "displayed_price_usd": price,
            "brand": item.get("brand"),
            "rating": item.get("rating"),
            "product_url": item.get("images", [None])[0] if item.get("images") else None,
            "source": "DummyJSON mock catalog",
        })

    return {
        "source": "DummyJSON mock catalog",
        "mode": "mock_catalog",
        "query": term,
        "count": len(products),
        "products": products,
        "note": "Mock catalog data for development only; not live marketplace listings, seller availability, or verified supplier prices.",
    }
