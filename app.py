"""Streamlit dashboard for AI Viral Product Hunter."""
import pandas as pd
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Viral Product Hunter", page_icon="🔎", layout="wide")
st.title("🔎 AI Viral Product Hunter")
st.caption("Explore product ideas using clearly labelled demo data and Google Trends signals.")

tab_demo, tab_catalog, tab_trends, tab_score, tab_youtube, tab_shortlist, tab_report, tab_profit, tab_supplier, tab_research_export = st.tabs(
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
    st.subheader("Product Research Report")
    st.write(
        "Combine saved Google Trends, YouTube, supplier comparison, "
        "and profit calculator results into one downloadable report."
    )

    # Reuse results already collected in this Streamlit session.
    trend_result = st.session_state.get("trends_result") or {}
    youtube_result = st.session_state.get("youtube_result") or {}
    supplier_result = st.session_state.get("supplier_comparison_results")
    profit_result = st.session_state.get("profit_result") or {}

    # Extract latest available Trends interest.
    trends_interest = None
    trend_items = trend_result.get("items", [])
    if trend_items:
        trend_df = pd.DataFrame(trend_items)
        possible_columns = [
            "latest_interest",
            "latest_value",
            "current_interest",
            "interest",
        ]
        for column in possible_columns:
            if column in trend_df.columns:
                values = pd.to_numeric(
                    trend_df[column], errors="coerce"
                ).dropna()
                if not values.empty:
                    trends_interest = float(values.iloc[0])
                    break

    # Extract the highest view count from YouTube results.
    youtube_items = youtube_result.get("items", [])
    top_views = None
    if youtube_items:
        views = pd.to_numeric(
            pd.DataFrame(youtube_items).get(
                "views", pd.Series(dtype=float)
            ),
            errors="coerce",
        ).dropna()
        if not views.empty:
            top_views = int(views.max())

    # Reuse the supplier comparison, if available.
    supplier_name = None
    supplier_cost = None
    supplier_shipping = None
    if isinstance(supplier_result, pd.DataFrame) and not supplier_result.empty:
        first_supplier = supplier_result.iloc[0]
        supplier_name = first_supplier.get("Supplier")
        supplier_cost = first_supplier.get("Item cost (₹)")
        supplier_shipping = first_supplier.get("Shipping (₹)")

    # Reuse the profit calculator result, if available.
    product_default = (
        profit_result.get("product_name")
        or "Portable blender"
    )
    selling_default = float(
        profit_result.get("selling_price_inr", 1499.0)
    )

    st.markdown("**Automatically found session results**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Trends interest",
        f"{trends_interest:g}" if trends_interest is not None else "Not found",
    )
    c2.metric(
        "Top YouTube views",
        f"{top_views:,}" if top_views is not None else "Not found",
    )
    c3.metric(
        "Supplier quote",
        supplier_name or "Not found",
    )
    c4.metric(
        "Profit estimate",
        (
            f"₹{profit_result['estimated_profit_per_order_inr']:,.2f}"
            if profit_result.get("estimated_profit_per_order_inr") is not None
            else "Not found"
        ),
    )

    st.caption(
        "These values come from saved results in the current Streamlit session. "
        "Run the relevant research tabs first. Results may not refer to the same product."
    )

    with st.form("product_research_export_form"):
        report_product_name = st.text_input(
            "Product name",
            value=product_default,
        )
        report_trends_interest = st.number_input(
            "Google Trends interest (0–100; 0 if unavailable)",
            min_value=0,
            max_value=100,
            value=max(
                0,
                min(100, int(trends_interest))
                if trends_interest is not None else 0,
            ),
        )
        report_youtube_views = st.number_input(
            "Top relevant YouTube views (0 if unavailable)",
            min_value=0,
            value=top_views or 0,
            step=1000,
        )
        report_supplier_name = st.text_input(
            "Supplier name",
            value=str(supplier_name or ""),
        )
        report_supplier_cost = st.number_input(
            "Supplier item cost (₹)",
            min_value=0.0,
            value=float(supplier_cost)
            if supplier_cost is not None else 0.0,
        )
        report_shipping = st.number_input(
            "Shipping per unit (₹)",
            min_value=0.0,
            value=float(supplier_shipping)
            if supplier_shipping is not None else 0.0,
        )
        report_selling_price = st.number_input(
            "Expected selling price (₹)",
            min_value=0.0,
            value=selling_default,
        )
        report_other_costs = st.number_input(
            "Other costs per order (₹)",
            min_value=0.0,
            value=max(
                0.0,
                float(profit_result.get("platform_fees_inr", 0))
                + float(profit_result.get("packaging_inr", 0))
                + float(profit_result.get("ad_cost_inr", 0))
                + float(profit_result.get("returns_reserve_inr", 0))
                + float(profit_result.get("tax_and_other_cost_inr", 0)),
            ),
            help="Include platform fees, packaging, advertising, returns, taxes, and other costs.",
        )
        report_notes = st.text_area(
            "Research notes",
            placeholder="Record product quality, competition, supplier links, and verification notes.",
        )
        create_report = st.form_submit_button(
            "Generate Product Research Report",
            type="primary",
        )

    if create_report:
        total_cost = (
            report_supplier_cost
            + report_shipping
            + report_other_costs
        )
        estimated_profit = report_selling_price - total_cost
        estimated_margin = (
            estimated_profit / report_selling_price * 100
            if report_selling_price > 0 else None
        )

        research_report = pd.DataFrame([{
            "product_name": report_product_name,
            "google_trends_interest_0_100": report_trends_interest,
            "top_youtube_views": report_youtube_views,
            "supplier_name": report_supplier_name,
            "supplier_item_cost_inr": report_supplier_cost,
            "shipping_per_unit_inr": report_shipping,
            "selling_price_inr": report_selling_price,
            "other_costs_per_order_inr": report_other_costs,
            "total_estimated_cost_inr": round(total_cost, 2),
            "estimated_profit_per_order_inr": round(estimated_profit, 2),
            "estimated_margin_percent": (
                round(estimated_margin, 2)
                if estimated_margin is not None else None
            ),
            "research_notes": report_notes,
            "data_status": "Mixed saved results and user-entered values; verify before use",
        }])

        st.session_state["product_research_report"] = research_report

    research_report = st.session_state.get("product_research_report")
    if research_report is not None:
        st.dataframe(
            research_report,
            hide_index=True,
            width="stretch",
        )
        st.download_button(
            "Download Product Research Report CSV",
            data=research_report.to_csv(index=False).encode("utf-8"),
            file_name="product_research_report.csv",
            mime="text/csv",
        )

    st.caption(
        "This is a research aid, not a sales or profit prediction. "
        "Confirm that the Trends, YouTube, and supplier results refer to the same product. "
        "Zero values may mean data was unavailable, not that demand or cost is zero."
    )

st.caption("Product trend signals and authorized live marketplace data are separate integrations. Never interpret demo records as verified market evidence.")