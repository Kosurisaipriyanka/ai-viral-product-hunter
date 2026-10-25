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

@app.get("/research/report")
def research_report(
    query: str = Query(default="portable blender", min_length=1, max_length=100),
    region_code: str = Query(default="IN", min_length=2, max_length=2),
    max_results: int = Query(default=10, ge=1, le=25),
):
    """Combine YouTube attention and Google Trends interest for one product keyword."""
    cleaned_query = query.strip()
    trends = fetch_google_trends([cleaned_query], geo=region_code.upper())
    videos = search_youtube_videos(query=cleaned_query, max_results=max_results, region_code=region_code.upper())
    trend_item = next((item for item in trends.get("items", []) if item.get("keyword", "").casefold() == cleaned_query.casefold()), None)
    video_items = videos.get("items", [])
    views = [item.get("views") for item in video_items if isinstance(item.get("views"), (int, float))]
    likes = [item.get("likes") for item in video_items if isinstance(item.get("likes"), (int, float))]
    comments = [item.get("comments") for item in video_items if isinstance(item.get("comments"), (int, float))]
    max_views = max(views) if views else None
    # Log scale keeps one extremely popular video from overwhelming the report.
    import math
    view_signal = round(min(100, (math.log10(max_views + 1) / 9) * 100), 1) if max_views is not None else None
    trend_signal = trend_item.get("latest_interest") if trend_item else None
    trend_change = trend_item.get("change_percent") if trend_item else None
    combined_score = None
    if trend_signal is not None and view_signal is not None:
        combined_score = round(0.6 * float(trend_signal) + 0.4 * view_signal, 1)
    return {
        "query": cleaned_query,
        "region_code": region_code.upper(),
        "source": "YouTube Data API v3 + Google Trends",
        "trend": trend_item,
        "youtube": {
            "video_count": len(video_items),
            "videos_with_view_counts": len(views),
            "top_video_views": max_views,
            "average_views": round(sum(views) / len(views)) if views else None,
            "total_available_likes": sum(likes) if likes else None,
            "total_available_comments": sum(comments) if comments else None,
            "view_attention_signal": view_signal,
            "items": video_items,
            "error": videos.get("error"),
        },
        "combined_research_score": combined_score,
        "score_method": "60% latest Google Trends indexed interest + 40% log-scaled highest view count signal, only when both sources return usable data.",
        "warnings": [
            "Experimental research score only; it is not a prediction of sales, profit, or virality.",
            "YouTube view counts measure video attention, not product purchases. Google Trends values are indexed interest, not search counts.",
            "Google Trends uses an unofficial pytrends interface and may be rate-limited.",
            "Missing data is left unavailable rather than fabricated."
        ],
    }


@app.get("/agent/research")
def agent_research(
    query: str = Query(default="portable blender", min_length=1, max_length=100),
    region_code: str = Query(default="IN", min_length=2, max_length=2),
    max_results: int = Query(default=10, ge=1, le=25),
    selling_price: float = Query(default=0, ge=0, le=10000000),
    supplier_cost: float = Query(default=0, ge=0, le=10000000),
    shipping_cost: float = Query(default=0, ge=0, le=10000000),
    other_costs: float = Query(default=0, ge=0, le=10000000),
    supplier_notes: str = Query(default="", max_length=1000),
):
    """Run the guided multi-tool product research workflow with optional LLM review."""
    from agent_research import run_product_research_agent

    return run_product_research_agent(
        query=query,
        region_code=region_code,
        max_results=max_results,
        selling_price=selling_price,
        supplier_cost=supplier_cost,
        shipping_cost=shipping_cost,
        other_costs=other_costs,
        supplier_notes=supplier_notes,
    )
