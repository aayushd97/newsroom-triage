"""The backend service. Four endpoints, fixed by the brief. It owns the model
call, retrieval, guardrails and the database. Run it from the backend folder:

    python main.py
"""
import os, math, pathlib
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Load .env from the current folder, this folder and the repo root, so running
# from backend/ still finds the key. A variable that is already set always wins.
# This must happen before the app package is imported. Tests switch it off.
HERE = pathlib.Path(__file__).resolve().parent
if not os.environ.get("TRIAGE_NO_DOTENV"):
    for folder in (pathlib.Path.cwd(), HERE, HERE.parent):
        load_dotenv(folder / ".env", override=False)

import requests
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from app import config, engine, store


@asynccontextmanager
async def lifespan(_):
    try:
        store.init_db()
    except Exception:
        pass   # the app must start and classify even if the database is down
    yield


api = FastAPI(title="Newsroom Triage backend", lifespan=lifespan)


class ClassifyIn(BaseModel):
    headline: str

class GoldenItem(BaseModel):
    text: str
    label: str

class ScoreIn(BaseModel):
    golden: list[GoldenItem]


def _model_error(e):
    """Turn a failed model call into a short, readable HTTP error."""
    if isinstance(e, engine.RateLimited):
        wait = max(1, math.ceil(e.retry_after))
        return HTTPException(429, f"Groq says slow down (rate limit). Try again in {wait} seconds. This is not a bad key.",
                             headers={"Retry-After": str(wait)})
    if isinstance(e, requests.HTTPError) and e.response is not None:
        code = e.response.status_code
        if code in (401, 403):
            return HTTPException(502, f"Groq rejected the API key (HTTP {code}). Check GROQ_API_KEY on the backend.")
        return HTTPException(502, f"Groq returned HTTP {code}.")
    if isinstance(e, requests.Timeout):
        return HTTPException(504, "Groq did not answer in time.")
    return HTTPException(502, "The backend could not reach Groq.")


@api.post("/classify")
def classify(body: ClassifyIn):
    try:
        tr = engine.classify(body.headline)
    except (engine.RateLimited, requests.RequestException) as e:
        raise _model_error(e)
    return {"category": tr.final, "confidence": tr.confidence, "branch": tr.branch,
            "passages": tr.passages, "guardrails": tr.guardrails, "blocked": tr.blocked,
            "raw_answer": tr.raw_answer, "why_branch": tr.why_branch,
            "mode": tr.mode, "ms": tr.ms}


@api.get("/runs")
def runs(limit: int = Query(50, ge=1, le=500)):
    try:
        rows = store.recent_runs(limit)
    except Exception:
        raise HTTPException(503, "The database is unavailable, so past runs cannot be shown.")
    for r in rows:
        r["blocked"] = bool(r["blocked"])
    return {"runs": rows}


@api.post("/score")
def score(body: ScoreIn):
    try:
        s = engine.score([g.model_dump() for g in body.golden])
    except (engine.RateLimited, requests.RequestException) as e:
        raise _model_error(e)
    return s


@api.get("/health")
def health():
    files = [f for f in config.KNOWLEDGE_FILES
             if (engine.HERE / "knowledge" / f).exists()]
    try:
        database = {"kind": store.kind(), "status": "ok", "rows": store.count_runs()}
    except Exception:
        database = {"kind": store.kind(), "status": "down"}
    return {"mode": "live" if engine.live_mode() else "demo",
            "knowledge": files,
            "missing": [f for f in config.KNOWLEDGE_FILES if f not in files],
            "model": config.MODEL,
            "key_present": engine.live_mode(),
            "database": database,
            "confidence_floor": config.CONFIDENCE_FLOOR,
            "passages_shown": config.KNOWLEDGE_PASSAGES,
            "relevance_threshold": config.KNOWLEDGE_THRESHOLD,
            "reasoning_effort": config.REASONING_EFFORT,
            "max_tokens": config.MAX_TOKENS,
            "routing_rules": len(config.ROUTING_RULES),
            "banned_phrases": len(config.BANNED_PHRASES)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
