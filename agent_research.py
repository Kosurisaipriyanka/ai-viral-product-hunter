"""Optional LLM-assisted product research workflow.

The workflow orchestrates existing research tools, keeps missing evidence explicit,
and falls back to transparent rules when no LLM API key is configured.
"""
import json
import os
from urllib.parse import quote_plus

import requests
from dotenv import load_dotenv

load_dotenv()

from discovery import fetch_google_trends
from youtube_discovery import search_youtube_videos


def _llm_review(query, region_code, trend_item, video_items, financials, supplier_notes):
    """Ask an OpenAI-compatible chat-completions endpoint for a grounded review."""
    api_key = os.getenv("AI_MODEL_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "available": False,
            "provider": None,
            "summary": None,
            "strengths": [],
            "risks": [],
            "next_steps": [],
            "note": "No AI_MODEL_API_KEY or OPENAI_API_KEY is configured; returned the transparent rule-based fallback.",
        }

    base_url = os.getenv("AI_MODEL_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("AI_MODEL_NAME", "gpt-4o-mini")
    evidence = {
        "query": query,
        "region_code": region_code,
        "google_trends": trend_item,
        "youtube_videos": [
            {
                "title": item.get("title"),
                "channel": item.get("channel_title"),
                "views": item.get("views"),
                "likes": item.get("likes"),
                "comments": item.get("comments"),
                "url": item.get("url"),
            }
            for item in video_items[:10]
        ],
        "user_entered_financials": financials,
        "user_entered_supplier_notes": supplier_notes,
    }
    system_prompt = (
        "You are a cautious e-commerce product research assistant. Assess only the evidence supplied. "
        "Do not claim that views equal sales, that indexed trend interest is search volume, or that a product will go viral. "
        "Do not invent supplier prices, shipping, sales, reviews, or competition data. "
        "Return valid JSON with keys summary (string), strengths (array of strings), risks (array of strings), "
        "next_steps (array of strings), and evidence_gaps (array of strings)."
    )
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "temperature": 0.2,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(evidence, ensure_ascii=False)},
                ],
                "response_format": {"type": "json_object"},
            },
            timeout=35,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        result = json.loads(content)
        required = ("summary", "strengths", "risks", "next_steps", "evidence_gaps")
        if not all(key in result for key in required):
            raise ValueError("The model response is missing required JSON fields.")
        for key in required[1:]:
            if not isinstance(result[key], list):
                raise ValueError(f"The model response field {key} must be a list.")
        return {
            "available": True,
            "provider": model,
            "summary": str(result["summary"]),
            "strengths": [str(value) for value in result["strengths"][:8]],
            "risks": [str(value) for value in result["risks"][:8]],
            "next_steps": [str(value) for value in result["next_steps"][:8]],
            "evidence_gaps": [str(value) for value in result["evidence_gaps"][:8]],
            "note": "LLM analysis is advisory. Verify every source and business assumption independently.",
        }
    except (requests.RequestException, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return {
            "available": False,
            "provider": model,
            "summary": None,
            "strengths": [],
            "risks": ["The optional AI review could not be completed."],
            "next_steps": ["Check the AI provider settings and retry, or use the rule-based findings below."],
            "evidence_gaps": ["AI review unavailable; do not interpret this as a positive or negative product verdict."],
            "note": f"AI review unavailable ({type(exc).__name__}); transparent fallback retained.",
        }


def run_product_research_agent(
    query,
    region_code="IN",
    max_results=10,
    selling_price=0,
    supplier_cost=0,
    shipping_cost=0,
    other_costs=0,
    supplier_notes="",
):
    """Run a predictable multi-tool research plan and optionally add an LLM review."""
    cleaned_query = query.strip()
    region = region_code.upper()
    plan = [
        {"step": 1, "tool": "Google Trends", "purpose": "Check indexed search-interest signals."},
        {"step": 2, "tool": "YouTube Data API", "purpose": "Collect public video metadata related to the keyword."},
        {"step": 3, "tool": "Evidence review", "purpose": "Identify gaps and produce cautious next steps."},
        {"step": 4, "tool": "Supplier search links", "purpose": "Open marketplace search pages for manual verification."},
    ]

    trends = fetch_google_trends([cleaned_query], geo=region)
    videos = search_youtube_videos(query=cleaned_query, max_results=max_results, region_code=region)
    trend_item = next(
        (item for item in trends.get("items", []) if item.get("keyword", "").casefold() == cleaned_query.casefold()),
        None,
    )
    video_items = videos.get("items", [])
    views = [item.get("views") for item in video_items if isinstance(item.get("views"), (int, float))]
    latest_interest = trend_item.get("latest_interest") if trend_item else None
    top_views = max(views) if views else None
    total_cost = float(supplier_cost) + float(shipping_cost) + float(other_costs)
    profit = float(selling_price) - total_cost if float(selling_price) > 0 else None
    margin = (profit / float(selling_price) * 100) if profit is not None else None
    financials = {
        "selling_price": float(selling_price),
        "supplier_cost": float(supplier_cost),
        "shipping_cost": float(shipping_cost),
        "other_costs": float(other_costs),
        "total_entered_cost": total_cost,
        "estimated_profit": round(profit, 2) if profit is not None else None,
        "estimated_margin_percent": round(margin, 2) if margin is not None else None,
    }

    if float(selling_price) <= 0:
        decision = "NEEDS MORE RESEARCH"
        decision_reasons = ["Enter a realistic selling price and all relevant costs before estimating profit."]
    elif profit < 0:
        decision = "HIGH RISK"
        decision_reasons = ["Entered costs exceed the entered selling price; estimated profit is negative."]
    elif latest_interest is None or top_views is None:
        decision = "NEEDS MORE RESEARCH"
        decision_reasons = ["At least one key research signal is missing. Retry or verify the sources manually."]
    elif not supplier_notes.strip() or float(supplier_cost) <= 0:
        decision = "NEEDS MORE RESEARCH"
        decision_reasons = ["Add and verify a supplier listing, product match, shipping, and total landed cost."]
    elif margin < 20:
        decision = "NEEDS MORE RESEARCH"
        decision_reasons = ["The entered estimated margin is below the project's 20% review threshold."]
    elif latest_interest >= 50 and top_views >= 100000 and margin >= 30:
        decision = "PROMISING SIGNAL"
        decision_reasons = ["Available trend, video-attention, and entered-margin signals meet the starter thresholds; this is not a sales prediction."]
    else:
        decision = "NEEDS MORE RESEARCH"
        decision_reasons = ["The evidence does not meet every starter threshold for a promising signal."]

    ai_review = _llm_review(cleaned_query, region, trend_item, video_items, financials, supplier_notes)
    evidence_gaps = []
    if trend_item is None:
        evidence_gaps.append("No matching Google Trends result was returned.")
    if not video_items:
        evidence_gaps.append("No YouTube videos were returned.")
    if not supplier_notes.strip():
        evidence_gaps.append("Supplier listing, stock, shipping, product match, and reliability have not been verified.")
    if float(supplier_cost) <= 0:
        evidence_gaps.append("A real supplier cost has not been entered.")
    if float(selling_price) <= 0:
        evidence_gaps.append("A planned selling price has not been entered.")
    evidence_gaps.append("Competitor pricing, actual sales, returns, ad costs, and conversion rates are not verified by this workflow.")

    encoded_query = quote_plus(cleaned_query)
    return {
        "query": cleaned_query,
        "region_code": region,
        "workflow_mode": "multi-tool research workflow with optional LLM review",
        "plan": plan,
        "sources": {
            "trends_source": trends.get("source", "Google Trends"),
            "trends_error": trends.get("error"),
            "youtube_source": videos.get("source", "YouTube Data API"),
            "youtube_error": videos.get("error"),
        },
        "trend": trend_item,
        "youtube": {
            "count": len(video_items),
            "top_video_views": top_views,
            "average_views": round(sum(views) / len(views)) if views else None,
            "items": video_items,
        },
        "financials": financials,
        "decision": decision,
        "decision_reasons": decision_reasons,
        "ai_review": ai_review,
        "evidence_gaps": evidence_gaps,
        "supplier_search_links": [
            {"name": "Alibaba", "url": f"https://www.alibaba.com/trade/search?SearchText={encoded_query}", "status": "Search link only; supplier data is not scraped or verified."},
            {"name": "AliExpress", "url": f"https://www.aliexpress.com/w/wholesale-{encoded_query}.html", "status": "Search link only; supplier data is not scraped or verified."},
        ],
        "warnings": [
            "YouTube views measure attention to videos, not product purchases.",
            "Google Trends is indexed interest, not search counts or sales.",
            "Supplier links open marketplace searches; this endpoint does not scrape or verify supplier listings.",
            "LLM output is advisory and may be wrong. Validate all claims and costs manually.",
            "This is a guided research workflow, not an autonomous agent that purchases products or guarantees virality.",
        ],
    }
