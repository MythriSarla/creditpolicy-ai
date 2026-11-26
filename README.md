# CreditPolicy AI: Credit Market Briefing Assistant

A Gen AI app for credit teams in BFSI. It scrapes current public sources, asks an LLM to write a structured credit-market briefing, and compares it with the previous briefing so changes in policy, rates and regulation stand out.

**Live demo:** <frontend URL, if deployed>

## How it works

1. **Firecrawl** scrapes RBI (current rates, press releases, monetary policy), MoSPI, SEBI circulars and Economic Times BFSI. The sources are listed in `backend/sources.json`.
2. **Pandas** collects the scraped pages into one table that is passed to the LLM.
3. **LLM (Gemini, with model fallbacks; Anthropic as an alternative)** returns a JSON briefing: summary, key indicators (repo rate, CRR, SLR and so on), changes against the previous briefing, risks and sources.
4. **Memory:** every briefing is saved in SQLite (`briefings.db`) and compared with earlier ones. **Memento** adds a knowledge-graph memory layer on top, with entity extraction and recall.
5. **React + Vite** frontend shows the latest briefing, a history list, and a table of what changed.

## Tech stack

Python, FastAPI, Firecrawl, Pandas, LLM APIs (Gemini / Anthropic), Memento, SQLite, React, Vite.

## Setup

### Backend

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your API keys
python -m uvicorn main:app --reload
```

The backend runs at http://127.0.0.1:8000.

### Frontend (second terminal)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and click **Generate briefing**. For a deployed backend, set `VITE_API_URL` to the backend URL before building.

## Environment variables

See `backend/.env.example`. Never commit your real `.env`.

| Variable | Purpose |
|---|---|
| `FIRECRAWL_API_KEY` | Scraping |
| `GEMINI_API_KEY` | Briefing generation |
| `GOOGLE_API_KEY` | Used by Memento's Gemini calls (same key) |
| `USE_MEMENTO` | `1` turns on the Memento memory layer, `0` turns it off |
| `MEMENTO_*_MODEL` | Models Memento uses for extraction and chat |

## API

- `POST /api/generate`: scrape, analyse and save a new briefing
- `GET /api/briefings`: list past briefings
- `GET /api/briefings/{id}`: one briefing
- `GET /api/sources`: configured sources

## Known limitations

- Memento's relation-extraction step can be skipped when the Gemini API returns 503 (high demand). The briefing is still saved, and the comparison with previous briefings works through SQLite.
- Memento requires a Python build with SQLite extension support. Use Python from python.org or Homebrew, not the system Python.
- Some source pages (for example RBI Monetary Policy) return little text when scraped, so indicators come from the sources that do load.
- <If deployed: Memento is switched off in production because its local database and embedding models are heavy for a free tier.>

## Project context

Built for <course name and code> as a Gen AI App (Firecrawl, Memento).