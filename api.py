"""FastAPI backend for sample products and discovery signals."""
from fastapi import FastAPI, Query

from catalog import search_public_catalog
from discovery import fetch_google_trends
from scoring import score_trend_items
from youtube_discovery import search_youtube_videos
from product_filter import screen_video_candidates

app = FastAPI(title="AI Viral Product Hunter API", version="0.4.0")

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

@app.get("/opportunities")
def get_opportunities(
    keywords: str = Query(default="pet gadgets,home organization,travel accessories"),
    geo: str = Query(default="IN", min_length=2, max_length=2),
):
    """Return an experimental score derived only from Google Trends signals."""
    keyword_list = [keyword.strip() for keyword in keywords.split(",")]
    trends = fetch_google_trends(keyword_list, geo=geo.upper())
    response = dict(trends)
    response["items"] = score_trend_items(trends.get("items", []))
    response["score_method"] = {
        "formula": "70% latest interest + 30% normalized recent momentum",
        "limits": "Momentum capped at +/-100%; score unavailable when change cannot be calculated.",
        "warning": "Experimental trend-only heuristic, not a prediction of sales, profit, or virality.",
    }
    return response

@app.get("/catalog")
def get_catalog(
    query: str = Query(default="organizer", min_length=1, max_length=100),
    limit: int = Query(default=10, ge=1, le=30),
):
    """Search a public mock catalog to develop listing workflows without API keys."""
    return search_public_catalog(query=query, limit=limit)

@app.get("/youtube/search")
def youtube_search(
    query: str = Query(default="viral products", min_length=1, max_length=100),
    max_results: int = Query(default=10, ge=1, le=25),
    region_code: str = Query(default="US", min_length=2, max_length=2),
):
    """Search YouTube video metadata through the official Data API."""
    return search_youtube_videos(query=query, max_results=max_results, region_code=region_code.upper())

@app.get("/youtube/shortlist")
def youtube_shortlist(
    query: str = Query(default="useful home gadgets", min_length=1, max_length=100),
    max_results: int = Query(default=10, ge=1, le=25),
    region_code: str = Query(default="US", min_length=2, max_length=2),
):
    """Search YouTube and rank videos with a transparent keyword-based screening heuristic."""
    response = search_youtube_videos(query=query, max_results=max_results, region_code=region_code.upper())
    response["items"] = screen_video_candidates(response.get("items", []))
    response["screening_method"] = {
        "formula": "20 points for each of five keyword signals: demonstration, problem-solving, emotional hook, bundle potential, and evergreen category",
        "warning": "This is a first-pass keyword screen, not an AI judgment or a prediction of sales or virality. Video metadata may not describe the product accurately.",
    }
    return response
