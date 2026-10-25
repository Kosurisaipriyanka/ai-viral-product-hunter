from agent_research import run_product_research_agent


def test_research_agent_uses_existing_sources_and_returns_supplier_search_links(monkeypatch):
    import agent_research

    monkeypatch.setattr(agent_research, "fetch_google_trends", lambda keywords, geo="IN": {
        "source": "Google Trends",
        "items": [{"keyword": "portable blender", "latest_interest": 60, "change_percent": 10}],
    })
    monkeypatch.setattr(agent_research, "search_youtube_videos", lambda query, max_results, region_code: {
        "source": "YouTube Data API v3",
        "items": [{"title": "Portable blender review", "views": 150000, "url": "https://youtube.com/watch?v=example"}],
    })
    monkeypatch.setattr(agent_research, "_llm_review", lambda *args: {
        "available": False, "provider": None, "summary": None, "strengths": [], "risks": [],
        "next_steps": [], "evidence_gaps": [], "note": "fallback",
    })

    result = run_product_research_agent(
        "portable blender", selling_price=1000, supplier_cost=400, shipping_cost=50,
        other_costs=50, supplier_notes="Supplier listing manually checked",
    )

    assert result["decision"] == "PROMISING SIGNAL"
    assert result["financials"]["estimated_profit"] == 500
    assert len(result["plan"]) == 4
    assert "alibaba.com" in result["supplier_search_links"][0]["url"]
    assert "not scraped or verified" in result["supplier_search_links"][0]["status"]


def test_research_agent_does_not_call_missing_data_promising(monkeypatch):
    import agent_research

    monkeypatch.setattr(agent_research, "fetch_google_trends", lambda keywords, geo="IN": {
        "source": "Google Trends", "items": [],
    })
    monkeypatch.setattr(agent_research, "search_youtube_videos", lambda query, max_results, region_code: {
        "source": "YouTube Data API v3", "items": [],
    })
    monkeypatch.setattr(agent_research, "_llm_review", lambda *args: {
        "available": False, "provider": None, "summary": None, "strengths": [], "risks": [],
        "next_steps": [], "evidence_gaps": [], "note": "fallback",
    })

    result = run_product_research_agent("unknown product")
    assert result["decision"] == "NEEDS MORE RESEARCH"
    assert result["financials"]["estimated_profit"] is None
    assert result["evidence_gaps"]
