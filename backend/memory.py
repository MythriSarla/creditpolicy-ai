"""Briefing memory.
SQLite is the main store (the website reads full briefings from it).
Memento is an optional second memory layer, switched on with USE_MEMENTO=1 in .env.
If Memento is missing or fails, the app keeps working with SQLite only."""
import json, os, sqlite3, datetime as dt
from pathlib import Path

DB = Path(__file__).parent / "briefings.db"


def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS briefings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT, conclusions TEXT, brief TEXT)""")


def save(brief):
    created = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    conclusions = brief.get("summary", "")
    with _conn() as c:
        cur = c.execute("INSERT INTO briefings(created_at, conclusions, brief) VALUES (?,?,?)",
                        (created, conclusions, json.dumps(brief)))
        bid = cur.lastrowid
    return {"id": bid, "created_at": created, **brief}


def recent(n=3):
    with _conn() as c:
        rows = c.execute("SELECT * FROM briefings ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    return [{"id": r["id"], "created_at": r["created_at"], **json.loads(r["brief"])} for r in rows]


def get(bid):
    with _conn() as c:
        r = c.execute("SELECT * FROM briefings WHERE id=?", (bid,)).fetchone()
    return None if not r else {"id": r["id"], "created_at": r["created_at"], **json.loads(r["brief"])}


def list_all():
    with _conn() as c:
        rows = c.execute("SELECT id, created_at, conclusions FROM briefings ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


# ---------- Memento (optional second memory layer) ----------
_MS = None


def _store():
    """Returns a Memento MemoryStore, or None if it is off or not working."""
    global _MS
    if os.getenv("USE_MEMENTO") != "1":
        return None
    if _MS is None:
        try:
            from memento import MemoryStore
            _MS = MemoryStore()
        except Exception as e:
            print(f"[memento] unavailable: {e}")
            return None
    return _MS


def remember(brief):
    """Save a briefing's conclusions into Memento."""
    s = _store()
    if not s:
        return
    try:
        lines = [f"Credit-market briefing on {brief['created_at'][:10]}: {brief['summary']}"]
        for c in brief.get("changes", []):
            lines.append(f"{c['topic']}: {c['current']} ({c['direction']})")
        s.ingest("\n".join(lines))
        print("[memento] saved briefing")
    except Exception as e:
        print(f"[memento] ingest failed: {e}")


def recall_context():
    """Ask Memento what it knows from earlier briefings. Returns text, or '' if off."""
    s = _store()
    if not s:
        return ""
    try:
        return s.recall("What were the earlier credit-market conclusions?").text
    except Exception as e:
        print(f"[memento] recall failed: {e}")
        return ""