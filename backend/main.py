
"""FastAPI backend. Run: uvicorn main:app --reload"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import memory
from scraper import scrape_sources, load_sources
from analyzer import build_brief

app = FastAPI(title="CreditPolicy AI")

# Allow local development and deployed Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://creditpolicy-ai-yyx.vercel.app"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

memory.init()


@app.get("/")
def home():
    return {
        "message": "CreditPolicy AI API is running!",
        "status": "success"
    }


@app.post("/api/generate")
def generate():
    try:
        df = scrape_sources()
        brief = build_brief(
            df,
            memory.recent(3),
            memory.recall_context()
        )
        saved = memory.save(brief)
        memory.remember(saved)
        return saved

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Briefing failed: {e}"
        )


@app.get("/api/briefings")
def briefings():
    return memory.list_all()


@app.get("/api/briefings/{bid}")
def briefing(bid: int):
    b = memory.get(bid)

    if not b:
        raise HTTPException(
            status_code=404,
            detail="Briefing not found"
        )

    return b


@app.get("/api/sources")
def sources():
    return load_sources()

