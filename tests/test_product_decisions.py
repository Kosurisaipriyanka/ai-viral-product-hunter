
from product_decisions import recommend_product


def test_negative_profit_is_high_risk():
    result = recommend_product(
        selling_price=500,
        total_cost=850,
        trends_interest=65,
        youtube_views=250_000,
        supplier_name="Supplier A",
    )
    assert result["decision"] == "HIGH RISK"


def test_missing_evidence_needs_more_research():
    result = recommend_product(
        selling_price=1499,
        total_cost=850,
        trends_interest=30,
        youtube_views=50_000,
        supplier_name="Supplier A",
    )
    assert result["decision"] == "NEEDS MORE RESEARCH"


def test_strong_sample_signals_are_promising():
    result = recommend_product(
        selling_price=1499,
        total_cost=850,
        trends_interest=65,
        youtube_views=250_000,
        supplier_name="Supplier A",
    )
    assert result["decision"] == "PROMISING SIGNAL"


def test_zero_selling_price_is_high_risk():
    result = recommend_product(
        selling_price=0,
        total_cost=850,
        trends_interest=65,
        youtube_views=250_000,
        supplier_name="Supplier A",
    )
    assert result["decision"] == "HIGH RISK"



def test_opportunity_score_rewards_complete_evidence():
    from product_decisions import calculate_opportunity_score

    result = calculate_opportunity_score(
        trends_interest=80,
        relevant_video_count=8,
        total_video_count=10,
        top_relevant_views=500_000,
        margin_percent=40,
        supplier_verified=True,
    )
    assert 75 <= result["score"] <= 100
    assert result["label"] == "STRONGER OPPORTUNITY SIGNAL"
    assert result["evidence_gaps"] == []


def test_opportunity_score_penalizes_missing_evidence():
    from product_decisions import calculate_opportunity_score

    result = calculate_opportunity_score(
        trends_interest=None,
        relevant_video_count=0,
        total_video_count=0,
        top_relevant_views=None,
        margin_percent=None,
        supplier_verified=False,
    )
    assert result["score"] == 0
    assert result["label"] == "WEAK OR INCOMPLETE SIGNAL"
    assert len(result["evidence_gaps"]) >= 4


def test_opportunity_score_is_bounded():
    from product_decisions import calculate_opportunity_score

    result = calculate_opportunity_score(
        trends_interest=100,
        relevant_video_count=10,
        total_video_count=10,
        top_relevant_views=10_000_000,
        margin_percent=80,
        supplier_verified=True,
    )
    assert 0 <= result["score"] <= 100
