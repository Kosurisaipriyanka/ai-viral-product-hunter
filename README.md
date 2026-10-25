# AI Viral Product Hunter

A beginner-friendly product research dashboard. **Phase 1 uses clearly labelled sample data only**; it does not claim to detect live viral trends.

## Features
- Streamlit dashboard with category selection, sample product scores, and CSV export.
- FastAPI backend with health and product endpoints.
- Automated tests and GitHub Actions.
- No paid API keys are required for this phase.

## Requirements
- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/) for dependency management

## Run on Windows
Open a terminal in this repository folder.

1. Install uv if needed, following the official uv installation instructions.
2. Install dependencies:
   ```powershell
   uv sync --extra dev
   ```
3. In terminal 1, start the API:
   ```powershell
   uv run uvicorn api:app --reload
   ```
4. In terminal 2, start the dashboard:
   ```powershell
   uv run streamlit run app.py
   ```
5. Open the local URL Streamlit prints (normally http://localhost:8501). The API health endpoint is http://127.0.0.1:8000/health.

## Run tests
```powershell
uv run pytest -q
```

## Data and next steps
All initial products and scores are illustrative sample data. They are not live search results, supplier quotes, or verified demand. Later phases can add permitted data sources, optional API integrations, supplier comparison, and more robust profit estimates. Never commit API keys; put local secrets in `.env` (which is ignored by Git) and use GitHub Actions secrets for CI integrations.
