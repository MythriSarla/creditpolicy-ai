# CreditPolicy AI: Credit Market Briefing Assistant

Generates credit-market briefings for a bank's credit team and compares each
one with the previous briefing.

## How it works
1. Firecrawl scrapes public sources (RBI, SEBI, MoSPI, Economic Times BFSI) listed in `backend/sources.json`.
2. Previous briefings are loaded from storage.
3. An LLM (Gemini) writes a briefing: summary, key indicators, what changed, risks, sources.
4. The React page shows the latest briefing, a history list, and a table of what changed.

## Tech stack
Python, Firecrawl, Pandas, Gemini API, React (Vite)

## Setup
1. Copy `.env.example` to `.env` and add your API keys.
2. Start the backend:
   ```
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```
3. Start the frontend (open a second terminal):
   ```
   cd frontend
   npm install
   npm run dev
   ```
4. Open http://localhost:5173 and click **Generate briefing**.