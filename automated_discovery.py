"""Automated candidate discovery using existing public research connectors."""
from discovery import fetch_google_trends
from youtube_discovery import search_youtube_videos
from product_decisions import calculate_opportunity_score

NICHE_CANDIDATES = {
    "pet gadgets": ["pet hair remover", "interactive cat toy", "portable pet water bottle", "slow feeder bowl", "pet grooming glove"],
    "kitchen gadgets": ["portable blender", "vegetable chopper", "oil spray bottle", "digital kitchen scale", "silicone air fryer liner"],
    "fitness": ["resistance bands", "adjustable jump rope", "posture corrector", "massage ball", "shaker bottle"],
    "travel accessories": ["packing cubes", "travel organizer", "compression toiletry bag", "portable luggage scale", "travel shoe bags"],
    "desk accessories": ["ergonomic laptop stand", "cable organizer", "desk mat", "monitor light bar", "under desk footrest"],
    "beauty accessories": ["heatless curling rod", "makeup brush cleaner", "facial ice roller", "travel makeup organizer", "hair scalp massager"],
}


def discover_candidates(niche, region_code="IN", max_candidates=5):
    """Research curated candidates; trends and video metrics are evidence signals only."""
    cleaned_niche = (niche or "").strip().casefold()
    region = (region_code or "IN").upper()
    if cleaned_niche not in NICHE_CANDIDATES:
        return {"niche": niche, "region_code": region, "items": [],
                "error": "Choose one of the supported niches: " + ", ".join(NICHE_CANDIDATES),
                "note": "Candidate ideas are curated starting points, not live marketplace discoveries."}
    candidates = NICHE_CANDIDATES[cleaned_niche][:max(1, min(int(max_candidates), 5))]
    trends = fetch_google_trends(candidates, geo=region)
    trend_by_keyword = {str(item.get("keyword", "")).casefold(): item for item in trends.get("items", [])}
    results = []
    for keyword in candidates:
        trend = trend_by_keyword.get(keyword.casefold())
        video_result = search_youtube_videos(query=keyword, max_results=5, region_code=region)
        videos = video_result.get("items", [])
        relevant = [v for v in videos if v.get("relevance_label") in ("HIGH", "MEDIUM")]
        views = [v.get("views") for v in relevant if isinstance(v.get("views"), (int, float))]
        score = calculate_opportunity_score(
            trends_interest=trend.get("latest_interest") if trend else None,
            relevant_video_count=len(relevant), total_video_count=len(videos),
            top_relevant_views=max(views) if views else None,
            margin_percent=None, supplier_verified=False,
        )
        results.append({
            "product_name": keyword,
            "trends_interest": trend.get("latest_interest") if trend else None,
            "relevant_videos": len(relevant), "videos_checked": len(videos),
            "top_relevant_views": max(views) if views else None,
            "opportunity_score": score["score"], "signal": score["label"],
            "evidence_gaps": " ".join(score["evidence_gaps"]),
            "youtube_error": video_result.get("error"),
        })
    results.sort(key=lambda item: item["opportunity_score"], reverse=True)
    for rank, item in enumerate(results, 1):
        item["rank"] = rank
    return {"niche": cleaned_niche, "region_code": region, "items": results,
            "note": "Curated ideas; Trends is indexed interest, views are attention not sales, and costs/supplier reliability are not verified."}
