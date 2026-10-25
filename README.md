AI Viral Product Hunter
A Python web application for researching product ideas using trend
signals, YouTube video engagement, estimated costs, and transparent
screening rules.
Important: This project is a research aid. A trend index is not
sales volume, YouTube views do not prove product demand, demo-catalog
records are not verified listings, and recommendations do not
guarantee virality or profit.

Features
- Sample product candidates: explore illustrative product ideas by
  category.
- Public demo catalog: search a clearly labelled mock/demo
  catalog.
- Google Trends: inspect relative search-interest signals for
  keywords in India.
- Opportunity score: calculate an experimental heuristic based on
  trend data.
- YouTube discovery: search public video metadata through the
  official YouTube Data API.
- Product shortlist and combined research: review product research
  signals in the dashboard.
- Profit calculator: estimate per-order profit and margin using
  entered costs.
- Supplier comparison: compare supplier details entered by the
  user; supplier quotes are not automatically verified.
- Product research report: combine research inputs, display a
  transparent decision category, and export a CSV report.
- Product comparison and ranking: compare up to three manually researched products, rank by the transparent opportunity score, review evidence gaps, and export CSV.
- Automated product discovery: research curated candidate ideas by niche using Google Trends and YouTube public metadata, rank candidates, and export a CSV shortlist. Candidate ideas are not live marketplace discoveries.\n- Guided Research Agent: orchestrate Google Trends and YouTube research,
  review evidence gaps, estimate entered costs, and provide supplier search links.
- Optional LLM review: configure an OpenAI-compatible chat-completions API
  to summarize strengths, risks, evidence gaps, and suggested next steps.
- Automated tests: test backend endpoints and the product decision
  rules.
Technology stack
- Python
- Streamlit for the dashboard
- FastAPI and Uvicorn for the backend API
- Pandas for tabular data and CSV reports
- pytrends for Google Trends access
- YouTube Data API for video metadata
- Pytest for automated tests
- Git and GitHub for version control
Requirements
- Python 3.12 or a compatible Python version supported by the
  project's dependencies
- Git
- A Google/YouTube Data API key for YouTube discovery (optional for
  other features)
Setup on Windows
Open PowerShell in the project folder.
1. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
If PowerShell blocks activation, you can run the environment's Python
directly with .venv\Scripts\python.exe.
2. Install dependencies
If the repository contains requirements.txt, run:
python -m pip install -r requirements.txt
If a dependency file is not present, install the dependencies listed in
the project's dependency configuration before running the app. Do not
install packages into the global Python environment unless necessary.
3. Configure the YouTube API key (optional)
Create a local .env file if the backend expects it, and set:
YOUTUBE_API_KEY=your_key_here
Replace the placeholder with your own key. Never commit .env or
share your API key. Ensure .env is included in .gitignore.
Optional: enable the LLM review in the Research Agent tab. Add these settings to your local `.env` file (only the API key is required; the other values have defaults):\nAI_MODEL_API_KEY=your_llm_api_key_here\nAI_MODEL_BASE_URL=https://api.openai.com/v1\nAI_MODEL_NAME=gpt-4o-mini\nUse a provider endpoint and model that support the OpenAI-compatible `/chat/completions` format. This feature may incur provider charges. Never commit `.env` or share keys. Without a key, the research workflow still runs with rule-based findings.\n\n4. Start the FastAPI backend
In the first terminal:
python -m uvicorn api:app --reload
The API should be available at http://127.0.0.1:8000. Open
http://127.0.0.1:8000/docs to inspect the API routes.
5. Start the Streamlit dashboard
Open a second terminal in the same project folder and activate the same
virtual environment. Then run:
python -m streamlit run app.py
Open the local URL shown by Streamlit, commonly http://localhost:8501.

Keep both terminals running while using the app.
Run tests
From the project root, with the virtual environment activated:
python -m py_compile app.py product_decisions.py
python -m pytest -v
A successful run should finish with all tests passing. A dependency
deprecation warning may appear without indicating a test failure; review
any actual failures separately.
Product decision rules
The product report uses explicit screening rules such as:
- HIGH RISK: selling price is invalid or estimated profit is
  negative.
- NEEDS MORE RESEARCH: key evidence is missing or the entered
  signals do not meet the screening thresholds.
- PROMISING SIGNAL: entered evidence and estimated margin meet the
  configured thresholds.
These are starter heuristics, not validated machine-learning
predictions. Confirm that all trend, video, supplier, and cost inputs
refer to the same product. Profit estimates are only as complete as the
costs entered by the user.
Data and limitations
- Google Trends provides relative interest indices, not units sold.
- Google Trends access through pytrends is unofficial and may be
  rate-limited or temporarily unavailable.
- YouTube results describe public video metadata and engagement, not
  product purchases.
- The demo catalog is illustrative and must not be presented as live
  marketplace inventory.
- Supplier comparisons are based on entered information and do not
  verify supplier legitimacy or live pricing.
- The application does not guarantee profitability, demand, or viral
  performance.
Suggested final verification
- [ ] Start the API and open /docs.
- [ ] Start the Streamlit dashboard and open all tabs.
- [ ] Try a sample-product search and a demo-catalog search.
- [ ] Try Google Trends and YouTube discovery with valid inputs
  (external services can be rate-limited).
- [ ] Generate a Product Research Report and download its CSV.
- [ ] Run python -m pytest -v.
- [ ] Check git status, then commit and push any final changes.
Repository hygiene
Keep API keys, .env, .venv, caches, and generated local files out of
Git. Review .gitignore before pushing.
