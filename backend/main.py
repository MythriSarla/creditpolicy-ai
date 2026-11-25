"""FastAPI backend. Run: uvicorn main:app --reload"""
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import memory
from scraper import scrape_sources, load_sources
from analyzer import build_brief

app = FastAPI(title="CreditPolicy AI")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])
memory.init()


@app.post("/api/generate")
def generate():
    try:
        df = scrape_sources()
        brief = build_brief(df, memory.recent(3), memory.recall_context())
        saved = memory.save(brief)
        memory.remember(saved)
        return saved
    except Exception as e:
        raise HTTPException(500, f"Briefing failed: {e}")
@app.get("/api/briefings")
def briefings():
    return memory.list_all()


@app.get("/api/briefings/{bid}")
def briefing(bid: int):
    b = memory.get(bid)
    if not b:
        raise HTTPException(404, "Briefing not found")
    return b


@app.get("/api/sources")
def sources():
    return load_sources()