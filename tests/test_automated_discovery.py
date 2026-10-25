"""Tests for automated product discovery workflow."""


def test_discovery_sorts_candidates(monkeypatch):
    import automated_discovery

    monkeypatch.setattr(automated_discovery, "fetch_google_trends", lambda keywords, geo: {
        "items": [{"keyword": keywords[0], "latest_interest": 20}, {"keyword": keywords[1], "latest_interest": 90}]
    })
    monkeypatch.setattr(automated_discovery, "search_youtube_videos", lambda query, max_results, region_code: {
        "items": [{"title": query, "views": 100000, "relevance_label": "HIGH"}]
    })
    result = automated_discovery.discover_candidates("pet gadgets", max_candidates=2)
    assert len(result["items"]) == 2
    assert result["items"][0]["product_name"] == "interactive cat toy"
    assert result["items"][0]["rank"] == 1
    assert result["items"][0]["opportunity_score"] > result["items"][1]["opportunity_score"]


def test_discovery_handles_unsupported_niche():
    from automated_discovery import discover_candidates
    result = discover_candidates("unknown niche")
    assert result["items"] == []
    assert "supported niches" in result["error"]
