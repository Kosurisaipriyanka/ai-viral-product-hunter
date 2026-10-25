"""Streamlit dashboard for AI Viral Product Hunter."""
import pandas as pd
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Viral Product Hunter", page_icon="🔎", layout="wide")
st.title("🔎 AI Viral Product Hunter")
st.caption("Explore product ideas using clearly labelled demo data and Google Trends signals.")

tab_demo, tab_catalog, tab_trends = st.tabs(
    ["Sample candidates", "Public demo catalog", "Google Trends"]
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
        st.dataframe(df, use_container_width=True, hide_index=True)
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
            st.dataframe(catalog_df, use_container_width=True, hide_index=True)
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
            st.dataframe(trends_df, use_container_width=True, hide_index=True)
            st.download_button(
                "Download Trends results as CSV",
                data=trends_df.to_csv(index=False).encode("utf-8"),
                file_name="google_trends_interest.csv",
                mime="text/csv",
            )
        else:
            st.info("No trend data returned. Try fewer or different keywords.")
        st.caption(trends_result.get("note", ""))

st.divider()
st.caption("Product trend signals and authorized live marketplace data are separate integrations. Never interpret demo records as verified market evidence.")
