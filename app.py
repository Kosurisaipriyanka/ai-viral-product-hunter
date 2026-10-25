"""Streamlit dashboard for AI Viral Product Hunter."""
import pandas as pd
import requests
import streamlit as st

from product_decisions import recommend_product, rank_product_comparisons
from automated_discovery import discover_candidates, NICHE_CANDIDATES
from research_history import save_research_run, list_research_runs, delete_research_run, clear_research_history
from research_exports import create_excel_report, create_pdf_report

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Viral Product Hunter", page_icon="🔎", layout="wide")
st.title("🔎 AI Viral Product Hunter")
st.caption("Explore product ideas using clearly labelled demo data and Google Trends signals.")

tab_demo, tab_catalog, tab_trends, tab_score, tab_youtube, tab_shortlist, tab_report, tab_profit, tab_supplier, tab_research_export, tab_agent, tab_compare, tab_discovery, tab_history, tab_exports = st.tabs(
    [
        "Sample candidates",
        "Public demo catalog",
        "Google Trends",
        "Opportunity score",
        "YouTube discovery",
        "Product shortlist",
        "Combined research",
        "Profit calculator",
        "Supplier comparison",
        "Product research report",
        "Research Agent",
        "Product comparison",
        "Automated discovery",
        "Research history",
        "Export reports",
    ]
)

with tab_demo:
    st.subheader("Sample product candidates")
    categories = ["Pet Gadgets", "Home & Kitchen", "Fitness", "Beauty Accessories", "Travel Accessories"]
    category = st.selectbox("Choose a product category", categories, key="sample_category")

    if st.button("Hunt Sample Products", type="primary"):
        try:
            response = requests.get(f"{API_URL}/products", params={"category": category}, timeout=5)
            response.raise_for_status()
            st.session_state["products"] = response.json()["products"]
            st.session_state["category"] = category
        except requests.RequestException:
            st.session_state["products"] = None
            st.error("Cannot connect to the API. Start the backend with: python -m uvicorn api:app --reload")

    products = st.session_state.get("products")
    if products is None and "products" in st.session_state:
        st.info("The API is unavailable. Start the backend and try again.")
    elif products:
        df = pd.DataFrame(products)
        st.subheader(f"Sample results: {st.session_state.get('category', category)}")
        st.warning("These are illustrative sample products and scores, not verified live market data.")
        m1, m2, m3 = st.columns(3)
        m1.metric("Products", len(df))
        m2.metric("Average sample score", f"{df['viral_score'].mean():.0f}/100")
        m3.metric("Average estimated retail price", f"₹{df['estimated_retail_price_inr'].mean():,.0f}")
        st.dataframe(df, width="stretch", hide_index=True)
        st.download_button("Download sample results as CSV", data=df.to_csv(index=False).encode("utf-8"),
                           file_name="sample_product_candidates.csv", mime="text/csv")
    else:
        st.info("Choose a category and click **Hunt Sample Products**.")

with tab_catalog:
    st.subheader("Search the public demo catalog")
    st.warning("This is a mock catalog for development—not live marketplace listings, current seller availability, or verified supplier prices.")
    with st.form("catalog_search_form"):
        search_term = st.text_input("Product keyword", value="organizer", max_chars=100)
        limit = st.slider("Maximum results", min_value=1, max_value=30, value=10)
        search_clicked = st.form_submit_button("Search Catalog", type="primary")

    if search_clicked:
        if not search_term.strip():
            st.error("Enter a product keyword to search.")
        else:
            try:
                response = requests.get(
                    f"{API_URL}/catalog",
                    params={"query": search_term.strip(), "limit": limit},
                    timeout=15,
                )
                response.raise_for_status()
                st.session_state["catalog_result"] = response.json()
            except requests.RequestException:
                st.session_state["catalog_result"] = None
                st.error("Could not reach the catalog API. Check that the backend is running.")

    catalog_result = st.session_state.get("catalog_result")
    if catalog_result:
        st.caption(f"Source: {catalog_result['source']} · Search: {catalog_result['query']}")
        if catalog_result.get("error"):
            st.error(catalog_result["error"])
        elif catalog_result["products"]:
            catalog_df = pd.DataFrame(catalog_result["products"])
            st.write(f"Found {catalog_result['count']} demo product(s).")
            st.dataframe(catalog_df, width="stretch", hide_index=True)
            st.download_button(
                "Download catalog results as CSV",
                data=catalog_df.to_csv(index=False).encode("utf-8"),
                file_name="demo_catalog_results.csv",
                mime="text/csv",
            )
        else:
            st.info("No matching products in this demo catalog. Try a broader keyword such as 'phone', 'beauty', or 'kitchen'.")
        st.caption(catalog_result.get("note", ""))

with tab_trends:
    st.subheader("Google Trends interest")
    st.write("Compare relative search interest in India over the past three months.")
    st.caption("Interest is indexed from 0 to 100. It is not sales volume or proof that a product will go viral.")
    with st.form("trends_form"):
        keywords_text = st.text_input(
            "Keywords separated by commas",
            value="pet gadgets,home organization,travel accessories",
            max_chars=300,
        )
        trends_clicked = st.form_submit_button("Fetch Google Trends", type="primary")

    if trends_clicked:
        if not keywords_text.strip():
            st.error("Enter at least one keyword.")
        else:
            try:
                response = requests.get(
                    f"{API_URL}/trends",
                    params={"keywords": keywords_text, "geo": "IN"},
                    timeout=35,
                )
                response.raise_for_status()
                st.session_state["trends_result"] = response.json()
            except requests.RequestException:
                st.session_state["trends_result"] = None
                st.error("Could not fetch Google Trends. Check the backend and try again.")

    trends_result = st.session_state.get("trends_result")
    if trends_result:
        if trends_result.get("error"):
            st.error(f"Google Trends request failed: {trends_result['error']}")
        elif trends_result.get("items"):
            trends_df = pd.DataFrame(trends_result["items"])
            st.dataframe(trends_df, width="stretch", hide_index=True)
            st.download_button(
                "Download Trends results as CSV",
                data=trends_df.to_csv(index=False).encode("utf-8"),
                file_name="google_trends_interest.csv",
                mime="text/csv",
            )
        else:
            st.info("No trend data returned. Try fewer or different keywords.")
        st.caption(trends_result.get("note", ""))

with tab_score:
    st.subheader("Experimental product opportunity score")
    st.warning("This heuristic uses Google Trends only. It does not include real product sales, competition, margins, or supplier reliability, and it does not predict virality.")
    with st.form("opportunity_form"):
        score_keywords = st.text_input(
            "Keywords separated by commas",
            value="pet gadgets,home organization,travel accessories",
            max_chars=300,
        )
        score_clicked = st.form_submit_button("Calculate Opportunity Scores", type="primary")

    if score_clicked:
        if not score_keywords.strip():
            st.error("Enter at least one keyword.")
        else:
            try:
                response = requests.get(
                    f"{API_URL}/opportunities",
                    params={"keywords": score_keywords, "geo": "IN"},
                    timeout=35,
                )
                response.raise_for_status()
                st.session_state["opportunity_result"] = response.json()
            except requests.RequestException:
                st.session_state["opportunity_result"] = None
                st.error("Could not calculate scores. Check the backend and try again.")

    opportunity_result = st.session_state.get("opportunity_result")
    if opportunity_result:
        if opportunity_result.get("error"):
            st.error(f"Google Trends request failed: {opportunity_result['error']}")
        elif opportunity_result.get("items"):
            score_df = pd.DataFrame(opportunity_result["items"])
            st.dataframe(score_df, width="stretch", hide_index=True)
            st.download_button(
                "Download opportunity scores as CSV",
                data=score_df.to_csv(index=False).encode("utf-8"),
                file_name="experimental_opportunity_scores.csv",
                mime="text/csv",
            )
        else:
            st.info("No scoreable trend data returned. Try different keywords.")
        method = opportunity_result.get("score_method", {})
        st.caption(f"Formula: {method.get('formula', 'Not available')}")
        st.caption(method.get("limits", ""))
        st.caption(method.get("warning", ""))

with tab_youtube:
    st.subheader("YouTube product discovery")
    st.write("Search public YouTube video metadata for product ideas, demonstrations, reviews, and problem-solving gadgets.")
    st.caption("Uses the official YouTube Data API. View counts can show content attention, but they do not prove product sales or demand.")
    with st.form("youtube_search_form"):
        youtube_query = st.text_input("Product or problem keyword", value="TikTok made me buy it gadgets", max_chars=100)
        youtube_region = st.selectbox("Video region", ["US", "IN", "GB", "CA", "AU"], index=0)
        youtube_limit = st.slider("Maximum videos", min_value=1, max_value=25, value=10)
        youtube_clicked = st.form_submit_button("Search YouTube", type="primary")

    if youtube_clicked:
        if not youtube_query.strip():
            st.error("Enter a keyword to search.")
        else:
            try:
                response = requests.get(
                    f"{API_URL}/youtube/search",
                    params={"query": youtube_query.strip(), "max_results": youtube_limit, "region_code": youtube_region},
                    timeout=45,
                )
                response.raise_for_status()
                st.session_state["youtube_result"] = response.json()
            except requests.RequestException:
                st.session_state["youtube_result"] = None
                st.error("Could not reach the YouTube search API. Check that the backend is running.")

    youtube_result = st.session_state.get("youtube_result")
    if youtube_result:
        if youtube_result.get("error"):
            st.error(youtube_result["error"])
        elif youtube_result.get("items"):
            youtube_df = pd.DataFrame(youtube_result["items"])
            st.write(f"Found {youtube_result['count']} video(s) for **{youtube_result['query']}**.")
            st.dataframe(
                youtube_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "url": st.column_config.LinkColumn("YouTube link"),
                    "thumbnail": st.column_config.ImageColumn("Thumbnail"),
                    "views": st.column_config.NumberColumn("Views", format="%d"),
                    "likes": st.column_config.NumberColumn("Likes", format="%d"),
                    "comments": st.column_config.NumberColumn("Comments", format="%d"),
                    "relevance_score": st.column_config.NumberColumn("Relevance score", format="%d"),
                    "relevance_label": st.column_config.TextColumn("Relevance"),
                },
            )
            st.download_button(
                "Download YouTube results as CSV",
                data=youtube_df.to_csv(index=False).encode("utf-8"),
                file_name="youtube_product_discovery.csv",
                mime="text/csv",
            )
        else:
            st.info("No videos returned. Try a broader keyword.")
        st.caption(youtube_result.get("note", ""))

with tab_shortlist:
    st.subheader("First-pass product shortlist")
    st.write("Search YouTube and rank videos using visible keyword signals inspired by your product research criteria.")
    st.warning("This is a transparent keyword screen, not an AI verdict or a prediction of sales. It cannot verify supplier prices, shipping, competition, or actual demand.")
    with st.form("shortlist_form"):
        shortlist_query = st.text_input("Product or problem keyword", value="useful home gadgets", max_chars=100)
        shortlist_region = st.selectbox("Video region", ["US", "IN", "GB", "CA", "AU"], index=0, key="shortlist_region")
        shortlist_limit = st.slider("Maximum videos to screen", min_value=1, max_value=25, value=10, key="shortlist_limit")
        shortlist_clicked = st.form_submit_button("Build Product Shortlist", type="primary")

    if shortlist_clicked:
        if not shortlist_query.strip():
            st.error("Enter a keyword to search.")
        else:
            try:
                response = requests.get(
                    f"{API_URL}/youtube/shortlist",
                    params={"query": shortlist_query.strip(), "max_results": shortlist_limit, "region_code": shortlist_region},
                    timeout=45,
                )
                response.raise_for_status()
                st.session_state["shortlist_result"] = response.json()
            except requests.RequestException:
                st.session_state["shortlist_result"] = None
                st.error("Could not reach the shortlist API. Check that the backend is running.")

    shortlist_result = st.session_state.get("shortlist_result")
    if shortlist_result:
        if shortlist_result.get("error"):
            st.error(shortlist_result["error"])
        elif shortlist_result.get("items"):
            shortlist_df = pd.DataFrame(shortlist_result["items"])
            st.dataframe(
                shortlist_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "url": st.column_config.LinkColumn("YouTube link"),
                    "thumbnail": st.column_config.ImageColumn("Thumbnail"),
                    "views": st.column_config.NumberColumn("Views", format="%d"),
                    "likes": st.column_config.NumberColumn("Likes", format="%d"),
                    "comments": st.column_config.NumberColumn("Comments", format="%d"),
                },
            )
            st.download_button(
                "Download product shortlist as CSV",
                data=shortlist_df.to_csv(index=False).encode("utf-8"),
                file_name="product_shortlist_first_pass.csv",
                mime="text/csv",
            )
        else:
            st.info("No videos returned. Try a broader keyword.")
        method = shortlist_result.get("screening_method", {})
        st.caption(f"Screening method: {method.get('formula', 'Not available')}")
        st.caption(method.get("warning", ""))
        st.caption(shortlist_result.get("note", ""))

with tab_report:
    st.subheader("Combined product research report")
    st.write("Compare Google Trends search interest with YouTube video attention for one product keyword.")
    st.warning("The combined score is an experimental research signal—not proof of demand, sales, profit, or virality. Google Trends may be unavailable or rate-limited.")
    with st.form("combined_research_form"):
        report_query = st.text_input("Product keyword", value="portable blender", max_chars=100)
        report_region = st.selectbox("Market / region", ["IN", "US", "GB", "CA", "AU"], index=0, key="report_region")
        report_limit = st.slider("YouTube videos to retrieve", min_value=1, max_value=25, value=10, key="report_limit")
        report_clicked = st.form_submit_button("Build Combined Report", type="primary")

    if report_clicked:
        if not report_query.strip():
            st.error("Enter a product keyword.")
        else:
            try:
                response = requests.get(
                    f"{API_URL}/research/report",
                    params={"query": report_query.strip(), "region_code": report_region, "max_results": report_limit},
                    timeout=60,
                )
                response.raise_for_status()
                st.session_state["combined_report"] = response.json()
            except requests.RequestException:
                st.session_state["combined_report"] = None
                st.error("Could not reach the combined research API. Check that the backend is running.")

    combined_report = st.session_state.get("combined_report")
    if combined_report:
        trend = combined_report.get("trend") or {}
        youtube = combined_report.get("youtube") or {}
        col1, col2, col3 = st.columns(3)
        col1.metric("Latest Trends interest", trend.get("latest_interest", "Unavailable"))
        col2.metric("Top YouTube video views", f"{youtube['top_video_views']:,}" if youtube.get("top_video_views") is not None else "Unavailable")
        col3.metric("Combined research score", f"{combined_report['combined_research_score']}/100" if combined_report.get("combined_research_score") is not None else "Unavailable")
        if trend.get("change_percent") is not None:
            st.write(f"Recent Trends change: **{trend['change_percent']}%**")
        elif not trend:
            st.info("Google Trends did not return usable data for this keyword. The combined score is unavailable unless both sources provide data.")
        if youtube.get("error"):
            st.warning(youtube["error"])
        if youtube.get("items"):
            report_df = pd.DataFrame(youtube["items"])
            st.dataframe(
                report_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "url": st.column_config.LinkColumn("YouTube link"),
                    "thumbnail": st.column_config.ImageColumn("Thumbnail"),
                    "views": st.column_config.NumberColumn("Views", format="%d"),
                    "likes": st.column_config.NumberColumn("Likes", format="%d"),
                    "comments": st.column_config.NumberColumn("Comments", format="%d"),
                },
            )
            export_df = pd.DataFrame([{
                "query": combined_report.get("query"),
                "region_code": combined_report.get("region_code"),
                "latest_trends_interest": trend.get("latest_interest"),
                "previous_trends_interest": trend.get("previous_interest"),
                "trends_change_percent": trend.get("change_percent"),
                "top_video_views": youtube.get("top_video_views"),
                "average_video_views": youtube.get("average_views"),
                "combined_research_score": combined_report.get("combined_research_score"),
                "score_method": combined_report.get("score_method"),
            }])
            st.download_button(
                "Download combined research summary as CSV",
                data=export_df.to_csv(index=False).encode("utf-8"),
                file_name="combined_product_research.csv",
                mime="text/csv",
            )
        for warning in combined_report.get("warnings", []):
            st.caption(warning)

with tab_profit:
    st.subheader("Supplier cost and profit calculator")
    st.write("Enter prices you have verified from a supplier and your intended selling channel. This is a manual calculator; it does not fetch supplier prices automatically.")
    st.info("Example values are only placeholders. Replace them with current quotes, shipping, platform fees, taxes, and your own assumptions before making a decision.")
    with st.form("profit_calculator_form"):
        product_name = st.text_input("Product name", value="Portable blender", max_chars=100)
        c1, c2, c3 = st.columns(3)
        selling_price = c1.number_input("Selling price per order (₹)", min_value=0.0, value=1499.0, step=50.0)
        supplier_cost = c2.number_input("Supplier item cost (₹)", min_value=0.0, value=450.0, step=25.0)
        inbound_shipping = c3.number_input("Shipping to you / fulfilment (₹)", min_value=0.0, value=100.0, step=10.0)
        c4, c5, c6 = st.columns(3)
        packaging_cost = c4.number_input("Packaging cost (₹)", min_value=0.0, value=30.0, step=5.0)
        platform_fee_pct = c5.number_input("Platform/payment fees (%)", min_value=0.0, max_value=100.0, value=12.0, step=1.0)
        ad_cost = c6.number_input("Ad cost per order (₹)", min_value=0.0, value=150.0, step=10.0)
        c7, c8 = st.columns(2)
        returns_reserve_pct = c7.number_input("Returns/refunds reserve (%)", min_value=0.0, max_value=100.0, value=5.0, step=1.0)
        tax_other_cost = c8.number_input("Tax and other cost per order (₹)", min_value=0.0, value=50.0, step=10.0)
        calculate_clicked = st.form_submit_button("Calculate estimated profit", type="primary")

    if calculate_clicked:
        fee_amount = selling_price * platform_fee_pct / 100
        returns_reserve = selling_price * returns_reserve_pct / 100
        total_cost = supplier_cost + inbound_shipping + packaging_cost + fee_amount + ad_cost + returns_reserve + tax_other_cost
        profit = selling_price - total_cost
        margin = (profit / selling_price * 100) if selling_price > 0 else None
        st.session_state["profit_result"] = {
            "product_name": product_name,
            "selling_price_inr": round(selling_price, 2),
            "supplier_cost_inr": round(supplier_cost, 2),
            "shipping_inr": round(inbound_shipping, 2),
            "packaging_inr": round(packaging_cost, 2),
            "platform_fees_inr": round(fee_amount, 2),
            "ad_cost_inr": round(ad_cost, 2),
            "returns_reserve_inr": round(returns_reserve, 2),
            "tax_and_other_cost_inr": round(tax_other_cost, 2),
            "total_estimated_cost_inr": round(total_cost, 2),
            "estimated_profit_per_order_inr": round(profit, 2),
            "estimated_margin_percent": round(margin, 2) if margin is not None else None,
            "values_are_user_estimates": True,
        }

    profit_result = st.session_state.get("profit_result")
    if profit_result:
        m1, m2, m3 = st.columns(3)
        m1.metric("Estimated cost per order", f"₹{profit_result['total_estimated_cost_inr']:,.2f}")
        m2.metric("Estimated profit per order", f"₹{profit_result['estimated_profit_per_order_inr']:,.2f}")
        m3.metric("Estimated margin", f"{profit_result['estimated_margin_percent']:.1f}%" if profit_result["estimated_margin_percent"] is not None else "Unavailable")
        if profit_result["estimated_profit_per_order_inr"] < 0:
            st.error("These assumptions show a loss per order. Check selling price and every cost before proceeding.")
        else:
            st.caption("Positive estimated profit does not guarantee real profit. Verify supplier quality, shipping, taxes, platform fees, advertising, refunds, and other costs.")
        profit_df = pd.DataFrame([profit_result])
        st.dataframe(profit_df, width="stretch", hide_index=True)
        st.download_button(
            "Download profit estimate as CSV",
            data=profit_df.to_csv(index=False).encode("utf-8"),
            file_name="supplier_cost_profit_estimate.csv",
            mime="text/csv",
        )

with tab_supplier:
    st.subheader("Supplier Price Comparison")
    st.write("Compare supplier quotes and estimate which option has the lowest cost.")
    st.info(
        "Enter prices from supplier quotes you have checked. "
        "These values are not fetched or verified automatically."
    )

    comparison_product_name = st.text_input(
        "Product name",
        value="Portable blender",
        key="comparison_product_name",
    )
    comparison_selling_price = st.number_input(
        "Expected selling price per unit (₹)",
        min_value=0.0,
        value=1499.0,
        step=50.0,
        key="comparison_selling_price",
    )

    supplier_data = pd.DataFrame(
        [
            {
                "Supplier": "Supplier A",
                "Item cost (₹)": 450.0,
                "Shipping (₹)": 100.0,
                "Minimum order quantity": 1,
                "Supplier link / notes": "",
            },
            {
                "Supplier": "Supplier B",
                "Item cost (₹)": 0.0,
                "Shipping (₹)": 0.0,
                "Minimum order quantity": 1,
                "Supplier link / notes": "",
            },
            {
                "Supplier": "Supplier C",
                "Item cost (₹)": 0.0,
                "Shipping (₹)": 0.0,
                "Minimum order quantity": 1,
                "Supplier link / notes": "",
            },
        ]
    )

    edited_suppliers = st.data_editor(
        supplier_data,
        num_rows="dynamic",
        hide_index=True,
        key="supplier_comparison_editor",
        column_config={
            "Item cost (₹)": st.column_config.NumberColumn(min_value=0.0, step=10.0),
            "Shipping (₹)": st.column_config.NumberColumn(min_value=0.0, step=10.0),
            "Minimum order quantity": st.column_config.NumberColumn(min_value=1, step=1),
            "Supplier link / notes": st.column_config.TextColumn(
                help="Paste a supplier quote URL or notes you have verified."
            ),
        },
    )

    if st.button("Compare supplier prices", type="primary", key="compare_supplier_prices"):
        results = edited_suppliers.copy()
        results["Product"] = comparison_product_name
        results["Item cost (₹)"] = pd.to_numeric(results["Item cost (₹)"], errors="coerce").fillna(0)
        results["Shipping (₹)"] = pd.to_numeric(results["Shipping (₹)"], errors="coerce").fillna(0)
        results["Total cost per unit (₹)"] = results["Item cost (₹)"] + results["Shipping (₹)"]
        results["Estimated gross profit (₹)"] = comparison_selling_price - results["Total cost per unit (₹)"]
        results["Estimated gross margin (%)"] = results["Estimated gross profit (₹)"].apply(
            lambda profit: round(profit / comparison_selling_price * 100, 2)
            if comparison_selling_price > 0
            else None
        )
        results = results[
            (results["Supplier"].astype(str).str.strip() != "")
            & (results["Item cost (₹)"] > 0)
        ].sort_values("Total cost per unit (₹)")
        st.session_state["supplier_comparison_results"] = results

    if "supplier_comparison_results" in st.session_state:
        results = st.session_state["supplier_comparison_results"]
        if results.empty:
            st.warning("Enter at least one supplier name and a positive item cost, then compare again.")
        else:
            st.dataframe(results, hide_index=True, width="stretch")
            best = results.iloc[0]
            st.metric(
                "Lowest entered cost per unit",
                f"₹{best['Total cost per unit (₹)']:,.2f}",
            )
            st.caption(
                "Gross profit here subtracts only item cost and entered shipping. It excludes platform fees, "
                "advertising, packaging, returns, taxes, and other costs. Use the Profit calculator for a fuller estimate."
            )
            st.download_button(
                "Download supplier comparison CSV",
                data=results.to_csv(index=False).encode("utf-8"),
                file_name="supplier_price_comparison.csv",
                mime="text/csv",
            )

with tab_research_export:
    st.subheader("Product Research Report and Decision")
    st.write(
        "Combine saved research signals with supplier and cost estimates. "
        "The recommendation uses visible rules and is not a prediction of sales or virality."
    )

    # Reuse results already collected in the current Streamlit session.
    trend_result = st.session_state.get("trends_result") or {}
    youtube_result = st.session_state.get("youtube_result") or {}
    supplier_result = st.session_state.get("supplier_comparison_results")
    saved_profit = st.session_state.get("profit_result") or {}

    trends_interest = None
    trend_items = trend_result.get("items", []) if isinstance(trend_result, dict) else []
    if trend_items:
        trend_df = pd.DataFrame(trend_items)
        for column in ("latest_interest", "latest_value", "current_interest", "interest", "latest"):
            if column in trend_df.columns:
                vals = pd.to_numeric(trend_df[column], errors="coerce").dropna()
                if not vals.empty:
                    trends_interest = float(vals.max())
                    break
        # Some Trends responses contain a date/value series instead of a latest-value field.
        if trends_interest is None:
            numeric_cols = [c for c in trend_df.columns if c.lower() in ("value", "interest", "trend_value")]
            for column in numeric_cols:
                vals = pd.to_numeric(trend_df[column], errors="coerce").dropna()
                if not vals.empty:
                    trends_interest = float(vals.iloc[-1])
                    break

    top_views = None
    youtube_items = youtube_result.get("items", []) if isinstance(youtube_result, dict) else []
    if youtube_items:
        views = pd.to_numeric(
            pd.DataFrame(youtube_items).get("views", pd.Series(dtype=float)),
            errors="coerce",
        ).dropna()
        if not views.empty:
            top_views = int(views.max())

    supplier_name = ""
    supplier_cost = None
    supplier_shipping = None
    if isinstance(supplier_result, pd.DataFrame) and not supplier_result.empty:
        best_supplier = supplier_result.iloc[0]
        supplier_name = str(best_supplier.get("Supplier", ""))
        supplier_cost = pd.to_numeric(pd.Series([best_supplier.get("Item cost (₹)")]), errors="coerce").iloc[0]
        supplier_shipping = pd.to_numeric(pd.Series([best_supplier.get("Shipping (₹)")]), errors="coerce").iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Saved Trends interest", f"{trends_interest:g}" if trends_interest is not None else "Not found")
    c2.metric("Top YouTube views", f"{top_views:,}" if top_views is not None else "Not found")
    c3.metric("Lowest-cost saved supplier", supplier_name or "Not found")
    c4.metric(
        "Saved profit estimate",
        f"₹{saved_profit['estimated_profit_per_order_inr']:,.2f}"
        if saved_profit.get("estimated_profit_per_order_inr") is not None else "Not found",
    )
    st.caption(
        "Session results may refer to different products or searches. Confirm they match before using them. "
        "Missing data is not evidence of zero demand."
    )

    default_product = str(saved_profit.get("product_name") or "Portable blender")
    default_selling = float(saved_profit.get("selling_price_inr", 1499.0) or 1499.0)
    default_other_costs = sum(float(saved_profit.get(key, 0) or 0) for key in (
        "packaging_inr", "platform_fees_inr", "ad_cost_inr", "returns_reserve_inr", "tax_and_other_cost_inr"
    ))

    with st.form("product_research_export_form"):
        report_product_name = st.text_input("Product name", value=default_product, max_chars=100)
        report_trends_interest = st.number_input(
            "Google Trends interest (0–100; enter 0 if unavailable)", min_value=0, max_value=100,
            value=max(0, min(100, int(trends_interest))) if trends_interest is not None else 0,
        )
        report_youtube_views = st.number_input(
            "Top relevant YouTube views (enter 0 if unavailable)", min_value=0,
            value=int(top_views or 0), step=1000,
        )
        report_supplier_name = st.text_input("Supplier name", value=supplier_name, max_chars=100)
        report_supplier_cost = st.number_input(
            "Supplier item cost per unit (₹)", min_value=0.0,
            value=float(supplier_cost) if supplier_cost is not None and pd.notna(supplier_cost) else 0.0,
        )
        report_shipping = st.number_input(
            "Shipping per unit (₹)", min_value=0.0,
            value=float(supplier_shipping) if supplier_shipping is not None and pd.notna(supplier_shipping) else 0.0,
        )
        report_selling_price = st.number_input(
            "Expected selling price per order (₹)", min_value=0.0, value=default_selling, step=50.0,
        )
        report_other_costs = st.number_input(
            "Other costs per order (₹)", min_value=0.0, value=max(0.0, default_other_costs),
            help="Include packaging, platform/payment fees, ads, returns/refunds reserve, taxes, and other costs.",
        )
        report_notes = st.text_area(
            "Research notes", placeholder="Add supplier quote links, quality checks, competition notes, and concerns."
        )
        create_report = st.form_submit_button("Generate Product Research Report", type="primary")

    if create_report:
        total_cost = report_supplier_cost + report_shipping + report_other_costs
        estimated_profit = report_selling_price - total_cost
        estimated_margin = estimated_profit / report_selling_price * 100 if report_selling_price > 0 else None

        decision_result = recommend_product(
            selling_price=report_selling_price,
            total_cost=total_cost,
            trends_interest=report_trends_interest,
            youtube_views=report_youtube_views,
            supplier_name=report_supplier_name,
        )
        decision = decision_result["decision"]
        reasons = decision_result["reasons"]

        research_report = pd.DataFrame([{
            "product_name": report_product_name,
            "google_trends_interest_0_100": report_trends_interest,
            "top_relevant_youtube_views": report_youtube_views,
            "supplier_name": report_supplier_name,
            "supplier_item_cost_inr": report_supplier_cost,
            "shipping_per_unit_inr": report_shipping,
            "expected_selling_price_inr": report_selling_price,
            "other_costs_per_order_inr": report_other_costs,
            "total_estimated_cost_inr": round(total_cost, 2),
            "estimated_profit_per_order_inr": round(estimated_profit, 2),
            "estimated_margin_percent": round(estimated_margin, 2) if estimated_margin is not None else None,
            "decision": decision,
            "decision_reasons": " ".join(reasons),
            "research_notes": report_notes,
            "data_status": "Verify product match, source data, supplier quote, and all costs",
        }])
        st.session_state["product_research_report"] = research_report
        st.session_state["product_research_decision"] = decision
        st.session_state["product_research_decision_reasons"] = reasons

    research_report = st.session_state.get("product_research_report")
    if isinstance(research_report, pd.DataFrame):
        decision = st.session_state.get("product_research_decision", "NEEDS MORE RESEARCH")
        reasons = st.session_state.get("product_research_decision_reasons", [])
        if decision == "PROMISING SIGNAL":
            st.success("PROMISING SIGNAL — " + " ".join(reasons))
        elif decision == "HIGH RISK":
            st.error("HIGH RISK — " + " ".join(reasons))
        else:
            st.warning("NEEDS MORE RESEARCH — " + " ".join(reasons))
        st.dataframe(research_report, hide_index=True, width="stretch")
        st.download_button(
            "Download Product Research Report CSV",
            data=research_report.to_csv(index=False).encode("utf-8"),
            file_name="product_research_report.csv",
            mime="text/csv",
        )

    st.caption(
        "Transparent starter rules: negative estimated profit or invalid selling price = HIGH RISK; "
        "missing key evidence = NEEDS MORE RESEARCH; PROMISING SIGNAL requires Trends interest ≥ 50, "
        "YouTube views ≥ 100,000, and estimated margin ≥ 30%. These thresholds are not validated predictors. "
        "The estimate excludes any costs you did not enter."
    )

st.divider()
st.caption("Product trend signals and authorized live marketplace data are separate integrations. Never interpret demo records as verified market evidence.")

with tab_agent:
    st.subheader("Guided AI Product Research Agent")
    st.write(
        "Run a planned research workflow across Google Trends and YouTube, calculate an estimate from your own cost inputs, "
        "review missing evidence, and open supplier marketplace search links."
    )
    st.info(
        "This is a guided multi-tool workflow. Optional LLM review requires an OpenAI-compatible API key. "
        "Supplier pages are search links only—not scraped or verified supplier offers."
    )
    with st.form("agent_research_form"):
        agent_query = st.text_input("Product keyword", value="portable blender", max_chars=100)
        agent_region = st.selectbox("Market", ["IN", "US", "GB", "CA", "AU"], index=0, key="agent_region")
        agent_limit = st.slider("YouTube videos to inspect", min_value=1, max_value=25, value=10, key="agent_limit")
        st.markdown("**Optional cost estimate**")
        cost_col1, cost_col2 = st.columns(2)
        with cost_col1:
            agent_selling_price = st.number_input("Expected selling price", min_value=0.0, value=0.0, step=50.0)
            agent_supplier_cost = st.number_input("Supplier item cost", min_value=0.0, value=0.0, step=25.0)
        with cost_col2:
            agent_shipping_cost = st.number_input("Shipping per unit", min_value=0.0, value=0.0, step=10.0)
            agent_other_costs = st.number_input("Other costs per order", min_value=0.0, value=0.0, step=10.0)
        agent_supplier_notes = st.text_input(
            "Supplier notes (only after you manually check a listing)",
            value="",
            max_chars=500,
            help="For example: supplier name, product match, shipping estimate, and listing URL. Do not paste secrets.",
        )
        agent_clicked = st.form_submit_button("Run Research Workflow", type="primary")

    if agent_clicked:
        if not agent_query.strip():
            st.error("Enter a product keyword.")
        else:
            try:
                agent_response = requests.get(
                    f"{API_URL}/agent/research",
                    params={
                        "query": agent_query.strip(),
                        "region_code": agent_region,
                        "max_results": agent_limit,
                        "selling_price": agent_selling_price,
                        "supplier_cost": agent_supplier_cost,
                        "shipping_cost": agent_shipping_cost,
                        "other_costs": agent_other_costs,
                        "supplier_notes": agent_supplier_notes,
                    },
                    timeout=75,
                )
                agent_response.raise_for_status()
                st.session_state["agent_research_result"] = agent_response.json()
            except requests.RequestException as exc:
                st.session_state["agent_research_result"] = None
                st.error("The research workflow could not finish. Check the backend, Google Trends availability, and YouTube API setup.")
                st.caption(str(exc))

    agent_result = st.session_state.get("agent_research_result")
    if agent_result:
        st.markdown("### Workflow plan")
        st.dataframe(pd.DataFrame(agent_result.get("plan", [])), hide_index=True, width="stretch")
        decision = agent_result.get("decision", "NEEDS MORE RESEARCH")
        reasons = agent_result.get("decision_reasons", [])
        if decision == "PROMISING SIGNAL":
            st.success(decision + " — " + " ".join(reasons))
        elif decision == "HIGH RISK":
            st.error(decision + " — " + " ".join(reasons))
        else:
            st.warning(decision + " — " + " ".join(reasons))

        financials = agent_result.get("financials", {})
        m1, m2, m3 = st.columns(3)
        m1.metric("Latest Trends interest", (agent_result.get("trend") or {}).get("latest_interest", "Unavailable"))
        m2.metric("Top YouTube views", f"{agent_result['youtube']['top_video_views']:,}" if agent_result.get("youtube", {}).get("top_video_views") is not None else "Unavailable")
        m3.metric("Estimated profit", f"₹{financials['estimated_profit']:,.2f}" if financials.get("estimated_profit") is not None else "Enter costs")
        if financials.get("estimated_margin_percent") is not None:
            st.caption(f"Estimated margin: {financials['estimated_margin_percent']}% based only on entered costs.")

        opportunity = agent_result.get("opportunity_score", {})
        if opportunity:
            st.markdown("### Product opportunity score")
            st.metric("Screening score (out of 100)", opportunity.get("score", 0), help=opportunity.get("method_note", ""))
            st.write(f"**{opportunity.get('label', 'Unrated')}**")
            components = opportunity.get("components", {})
            if components:
                st.dataframe(
                    pd.DataFrame([{"Signal": key.replace("_", " ").title(), "Points": value} for key, value in components.items()]),
                    hide_index=True,
                    width="stretch",
                )
            st.caption(opportunity.get("method_note", ""))
            for gap in opportunity.get("evidence_gaps", []):
                st.write(f"- Evidence gap: {gap}")

        ai_review = agent_result.get("ai_review", {})
        st.markdown("### AI review")
        if ai_review.get("available"):
            st.caption(f"LLM provider/model: {ai_review.get('provider')}")
            st.write(ai_review.get("summary", "No summary returned."))
        else:
            st.info(ai_review.get("note", "Optional LLM review is not available; use the rule-based findings and evidence below."))
        for title, key in [("Strengths", "strengths"), ("Risks", "risks"), ("Suggested next steps", "next_steps"), ("AI evidence gaps", "evidence_gaps")]:
            values = ai_review.get(key, [])
            if values:
                st.markdown(f"**{title}**")
                for value in values:
                    st.write(f"- {value}")

        st.markdown("### Supplier search links")
        for supplier in agent_result.get("supplier_search_links", []):
            st.markdown(f"- [{supplier['name']}]({supplier['url']}) — {supplier['status']}")

        gaps = agent_result.get("evidence_gaps", [])
        if gaps:
            st.markdown("### Evidence still missing")
            for gap in gaps:
                st.write(f"- {gap}")

        youtube_result = agent_result.get("youtube", {})
        relevance_summary = youtube_result.get("relevance_summary", {})
        if relevance_summary.get("scored"):
            st.markdown("### YouTube relevance check")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("High relevance", relevance_summary.get("high", 0))
            r2.metric("Medium relevance", relevance_summary.get("medium", 0))
            r3.metric("Low relevance", relevance_summary.get("low", 0))
            r4.metric("Relevant videos used for view signals", youtube_result.get("relevant_count", 0))
            st.caption("Labels use keyword overlap in titles and descriptions. This is a heuristic, not semantic understanding; inspect videos manually.")

        videos = youtube_result.get("items", [])
        if videos:
            st.markdown("### YouTube evidence")
            video_df = pd.DataFrame(videos)
            st.dataframe(
                video_df,
                hide_index=True,
                width="stretch",
                column_config={
                    "url": st.column_config.LinkColumn("YouTube link"),
                    "views": st.column_config.NumberColumn("Views", format="%d"),
                    "likes": st.column_config.NumberColumn("Likes", format="%d"),
                    "comments": st.column_config.NumberColumn("Comments", format="%d"),
                },
            )
        with st.expander("Sources and limitations"):
            st.json({
                "sources": agent_result.get("sources"),
                "warnings": agent_result.get("warnings"),
            })
        st.download_button(
            "Download Research Agent result as JSON",
            data=__import__("json").dumps(agent_result, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="ai_product_research_agent.json",
            mime="application/json",
        )

        if st.button("Save this agent run to local history", key="save_agent_history"):
            saved_id = save_research_run(
                "research_agent",
                str(agent_result.get("query") or "Research Agent run"),
                agent_result,
            )
            st.success(f"Saved locally to research history (ID {saved_id}).")



with tab_compare:
    st.subheader("Product comparison and ranking")
    st.write("Compare up to three product ideas using the same transparent opportunity-score heuristic.")
    st.warning(
        "Enter evidence for each product from your research. Trends are indexed interest, views are attention rather than sales, "
        "and supplier verification is your own assessment—not an automated supplier check."
    )
    candidates = []
    with st.form("product_comparison_form"):
        for number in range(1, 4):
            with st.expander(f"Product {number}", expanded=(number == 1)):
                product_name = st.text_input("Product name", value=["Portable blender", "Pet hair remover", "Travel organizer"][number - 1], key=f"compare_name_{number}")
                c1, c2, c3 = st.columns(3)
                trends_interest = c1.number_input("Google Trends interest (0–100)", min_value=0, max_value=100, value=0, key=f"compare_trends_{number}")
                relevant_videos = c2.number_input("HIGH/MEDIUM relevant videos", min_value=0, max_value=25, value=0, key=f"compare_relevant_{number}")
                total_videos = c3.number_input("Total videos checked", min_value=0, max_value=25, value=0, key=f"compare_total_{number}")
                c4, c5, c6 = st.columns(3)
                top_views = c4.number_input("Top relevant video views", min_value=0, value=0, step=1000, key=f"compare_views_{number}")
                margin = c5.number_input("Estimated margin (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, key=f"compare_margin_{number}")
                supplier_verified = c6.checkbox("Supplier listing checked", value=False, key=f"compare_supplier_{number}")
                candidates.append({
                    "product_name": product_name,
                    "trends_interest": trends_interest if trends_interest > 0 else None,
                    "relevant_video_count": relevant_videos,
                    "total_video_count": total_videos,
                    "top_relevant_views": top_views if top_views > 0 else None,
                    "margin_percent": margin if margin > 0 else None,
                    "supplier_verified": supplier_verified,
                })
        compare_clicked = st.form_submit_button("Rank Products", type="primary")

    if compare_clicked:
        ranked_products = rank_product_comparisons(candidates)
        st.session_state["ranked_product_comparison"] = ranked_products

    ranked_products = st.session_state.get("ranked_product_comparison")
    if ranked_products:
        comparison_df = pd.DataFrame(ranked_products)
        display_columns = [
            "rank", "product_name", "opportunity_score", "signal", "trend_interest",
            "relevant_videos", "videos_checked", "top_relevant_views",
            "estimated_margin_percent", "supplier_verified", "evidence_gaps",
        ]
        st.markdown("### Ranked shortlist")
        st.dataframe(
            comparison_df[display_columns],
            hide_index=True,
            width="stretch",
            column_config={
                "rank": st.column_config.NumberColumn("Rank", format="%d"),
                "opportunity_score": st.column_config.ProgressColumn("Opportunity score", min_value=0, max_value=100, format="%d/100"),
                "trend_interest": st.column_config.NumberColumn("Trends index", format="%d"),
                "top_relevant_views": st.column_config.NumberColumn("Top relevant views", format="%d"),
                "estimated_margin_percent": st.column_config.NumberColumn("Estimated margin", format="%.1f%%"),
                "supplier_verified": st.column_config.CheckboxColumn("Supplier checked"),
            },
        )
        st.download_button(
            "Download ranked shortlist as CSV",
            data=comparison_df.to_csv(index=False).encode("utf-8"),
            file_name="ranked_product_comparison.csv",
            mime="text/csv",
        )
        st.caption("Rankings are only as reliable as the values entered. Scores are screening heuristics, not predictions of sales, profit, or virality.")



with tab_discovery:
    st.subheader("Automated product discovery")
    st.write("Choose a niche to research curated product ideas using Google Trends and public YouTube metadata.")
    st.info("This workflow automates research across a curated list; it does not scrape marketplaces or verify product sales.")
    with st.form("automated_discovery_form"):
        niche = st.selectbox("Product niche", options=list(NICHE_CANDIDATES.keys()))
        region = st.selectbox("Market", options=["IN", "US", "GB", "CA", "AU"], index=0)
        count = st.slider("Candidate ideas to research", min_value=1, max_value=5, value=5)
        run_discovery = st.form_submit_button("Discover and rank ideas", type="primary")
    if run_discovery:
        with st.spinner("Checking trend signals and YouTube videos for each candidate…"):
            try:
                st.session_state["automated_discovery_result"] = discover_candidates(niche, region, count)
            except Exception as exc:
                st.session_state["automated_discovery_result"] = None
                st.error("Discovery could not complete. Google Trends or YouTube may be temporarily unavailable.")
                st.caption(type(exc).__name__)
    discovery_result = st.session_state.get("automated_discovery_result")
    if discovery_result:
        if discovery_result.get("error"):
            st.warning(discovery_result["error"])
        else:
            discovered = discovery_result.get("items", [])
            if discovered:
                discovery_df = pd.DataFrame(discovered)
                st.markdown("### Ranked candidate ideas")
                st.dataframe(
                    discovery_df,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "rank": st.column_config.NumberColumn("Rank", format="%d"),
                        "opportunity_score": st.column_config.ProgressColumn("Screening score", min_value=0, max_value=100, format="%d/100"),
                        "trends_interest": st.column_config.NumberColumn("Trends index", format="%d"),
                        "top_relevant_views": st.column_config.NumberColumn("Top relevant views", format="%d"),
                    },
                )
                st.download_button(
                    "Download discovery shortlist as CSV",
                    data=discovery_df.to_csv(index=False).encode("utf-8"),
                    file_name="automated_product_discovery.csv",
                    mime="text/csv",
                )
            if discovered and st.button("Save this discovery run to local history", key="save_discovery_history"):
                saved_id = save_research_run(
                    "automated_discovery",
                    str(discovery_result.get("niche") or niche),
                    discovery_result,
                )
                st.success(f"Saved locally to research history (ID {saved_id}).")
            st.caption(discovery_result.get("note", ""))


with tab_history:
    st.subheader("Saved research history")
    st.write("Review previous Research Agent and Automated Discovery runs saved in a local SQLite database on this computer.")
    st.caption("History is local to this machine. It is not synced to GitHub or another computer.")
    history_col1, history_col2 = st.columns(2)
    with history_col1:
        if st.button("Refresh history", key="refresh_research_history"):
            st.rerun()
    with history_col2:
        if st.button("Clear all saved history", key="clear_research_history"):
            removed = clear_research_history()
            st.success(f"Deleted {removed} saved run(s).")
            st.rerun()

    history_runs = list_research_runs(limit=100)
    if not history_runs:
        st.info("No saved runs yet. Use the save button after completing a Research Agent or Automated Discovery workflow.")
    else:
        history_rows = [
            {
                "ID": run["id"],
                "Type": run["run_type"],
                "Title": run["title"],
                "Saved at (UTC)": run["created_at"],
            }
            for run in history_runs
        ]
        st.dataframe(pd.DataFrame(history_rows), hide_index=True, width="stretch")
        selected_id = st.selectbox(
            "Choose a saved run to inspect",
            options=[run["id"] for run in history_runs],
            format_func=lambda value: next(
                f"#{run['id']} · {run['run_type']} · {run['title']} · {run['created_at']}"
                for run in history_runs if run["id"] == value
            ),
        )
        selected_run = next(run for run in history_runs if run["id"] == selected_id)
        st.json(selected_run["payload"])
        st.download_button(
            "Download selected saved run as JSON",
            data=__import__("json").dumps(selected_run, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name=f"research_history_{selected_id}.json",
            mime="application/json",
        )
        if st.button("Delete selected run", key="delete_selected_research_run"):
            delete_research_run(selected_id)
            st.success("Deleted the selected saved run.")
            st.rerun()


with tab_exports:
    st.subheader("Professional research reports")
    st.write("Export a saved research run as an Excel workbook or a shareable PDF report.")
    st.caption("Reports contain the saved run's data and limitations. Scores remain screening heuristics, not proof of sales or guaranteed profit.")
    export_runs = list_research_runs(limit=100)
    if not export_runs:
        st.info("No saved runs available yet. First save a run from Research Agent or Automated discovery.")
    else:
        export_id = st.selectbox(
            "Choose a saved research run",
            options=[run["id"] for run in export_runs],
            format_func=lambda value: next(
                f"#{run['id']} · {run['run_type']} · {run['title']} · {run['created_at']}"
                for run in export_runs if run["id"] == value
            ),
            key="export_report_run_id",
        )
        export_run = next(run for run in export_runs if run["id"] == export_id)
        st.write(f"**Selected:** {export_run['title']} · {export_run['run_type']}")
        left, right = st.columns(2)
        safe_filename = "".join(ch.lower() if ch.isalnum() else "_" for ch in export_run["title"]).strip("_") or "research_report"
        with left:
            try:
                excel_bytes = create_excel_report(export_run)
                st.download_button(
                    "Download Excel report (.xlsx)",
                    data=excel_bytes,
                    file_name=f"{safe_filename}_research.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                )
            except Exception:
                st.error("Excel report could not be generated. Check that report dependencies are installed.")
        with right:
            try:
                pdf_bytes = create_pdf_report(export_run)
                st.download_button(
                    "Download PDF report",
                    data=pdf_bytes,
                    file_name=f"{safe_filename}_research.pdf",
                    mime="application/pdf",
                )
            except Exception:
                st.error("PDF report could not be generated. Check that report dependencies are installed.")
