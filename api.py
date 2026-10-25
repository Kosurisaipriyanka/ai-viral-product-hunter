"""FastAPI backend for sample products and optional live discovery signals."""
from fastapi import FastAPI, Query

from discovery import fetch_google_trends

app = FastAPI(title="AI Viral Product Hunter API", version="0.2.0")

SAMPLE_PRODUCTS = [
    {"name": "Reusable Pet Hair Remover", "category": "Pet Gadgets", "viral_score": 82, "estimated_retail_price_inr": 599, "estimated_supplier_cost_inr": 180, "source": "Sample data", "notes": "Easy-to-demonstrate household pet accessory"},
    {"name": "Portable Pet Water Bottle", "category": "Pet Gadgets", "viral_score": 76, "estimated_retail_price_inr": 499, "estimated_supplier_cost_inr": 160, "source": "Sample data", "notes": "Travel-friendly hydration accessory"},
    {"name": "Adjustable Drawer Organizer", "category": "Home & Kitchen", "viral_score": 78, "estimated_retail_price_inr": 699, "estimated_supplier_cost_inr": 240, "source": "Sample data", "notes": "Simple home-organization demonstration"},
    {"name": "Rechargeable Motion Sensor Light", "category": "Home & Kitchen", "viral_score": 80, "estimated_retail_price_inr": 799, "estimated_supplier_cost_inr": 290, "source": "Sample data", "notes": "Useful lighting accessory"},
    {"name": "Resistance Band Set", "category": "Fitness", "viral_score": 71, "estimated_retail_price_inr": 499, "estimated_supplier_cost_inr": 150, "source": "Sample data", "notes": "Compact fitness accessory"},
    {"name": "Travel Cable Organizer", "category": "Travel Accessories", "viral_score": 69, "estimated_retail_price_inr": 399, "estimated_supplier_cost_inr": 100, "source": "Sample data", "notes": "Small accessory for organizing cables"},
    {"name": "Makeup Brush Cleaning Mat", "category": "Beauty Accessories", "viral_score": 67, "estimated_retail_price_inr": 299, "estimated_supplier_cost_inr": 70, "source": "Sample data", "notes": "Demonstrable cleaning accessory"},
]

@app.get("/health")
def health():
    """Simple health check for local development and automated tests."""
    return {"status": "ok", "service": "AI Viral Product Hunter API"}

@app.get("/products")
def get_products(category: str | None = None):
    """Return clearly labelled sample product candidates, optionally filtered by category."""
    products = SAMPLE_PRODUCTS if category is None else [
        product for product in SAMPLE_PRODUCTS if product["category"].casefold() == category.casefold()
    ]
    return {"mode": "sample_data", "count": len(products), "products": products}

@app.get("/trends")
def get_trends(
    keywords: str = Query(default="pet gadgets,home organization,travel accessories"),
    geo: str = Query(default="IN", min_length=2, max_length=2),
):
    """Return Google Trends interest signals for comma-separated keywords."""
    keyword_list = [keyword.strip() for keyword in keywords.split(",")]
    return fetch_google_trends(keyword_list, geo=geo.upper())
