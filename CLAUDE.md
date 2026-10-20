# Working rules

- Branch: do all work on branch week2-work, never on main. Small commits, one per step, clear messages. Open a pull request at the end. I will create the GitHub repo and push myself when I say so.
- Secrets: GROQ_API_KEY lives in .env. Never print, log, commit or ask me to paste a key. The app reads os.environ, so add python-dotenv (pinned in requirements.txt) to load .env for local runs.
- Contract: the four backend endpoints in the brief's C2 section are fixed. Do not change their shapes.
- Golden set: scoring must use MY Week 1 hand labels, not official_label. Keep the official label as a second column so I can report both.
- Frontend: keep Gradio, but it must call the backend over HTTP via a BACKEND_URL environment variable and know nothing about the model or database.
- Rate limits: Groq free tier is 30 requests and 8,000 tokens per minute. engine.score does not pace itself, so add pacing and honour the retry-after header. A 429 is not a bad key.
- Scoring log: before each scoring run, remind me to add a row to results/versions.md (version, what changed, accuracy, kappa, blocked count). Offer to append the row yourself from the run output.
- Tests: do not edit tests to make them pass. Do not weaken guardrails to raise a score. If a change makes the score worse, log it and tell me.
- Honesty: say how sure you are about any library, free-tier or platform fact. I must report one place an assistant was confidently wrong, so flag your own uncertain claims.
- Not your job: do not write my two-page write-up. You can help me find the numbers it needs.
- Style: plain sentences in any README or notes, no em dashes.
- Status: keep a "Current status" section at the bottom of CLAUDE.md. Update it at the end of each session with what is done, the latest versions.md row and the next step.

## Current status

- Done: Week 2 steps up to C2. Scoring on my_label with official_label kept; Groq pacing; BLOCKED scoring; v1 token budget; v2 prompt from my Week 1 rules; v3 floor 0.6. C2 split built and working locally: backend/ (FastAPI, four endpoints, all database access in backend/app/store.py, SQLite) and frontend/ (Gradio, calls the backend over HTTP via BACKEND_URL, own copy of the CSVs). Old root run.py and requirements.txt removed. Backend tests: 26 passed (the 20 existing, unedited, plus 6 in test_api.py). tests/conftest.py is new: it keeps tests off .env, the key and the real database.
- Latest versions.md row: v3, 26/30, 0.8667, kappa 0.8198, 0 blocked. Live Scoring through the new frontend: 26/30, 0.8667, kappa 0.8193, 0 blocked, same four wrong items (ids 18, 23, 28, 29). No new row appended, because the app logic did not change.
- Open points: Render may not read backend/.python-version or frontend/.python-version, since its docs only say the repo root, so set PYTHON_VERSION to a full version (for example 3.12.3) on both services. Starlette's TestClient warns that httpx is deprecated in favour of httpx2, left as is. One long /score request on Render is untested. The frontend venv pulled in its own FastAPI through Gradio, which is harmless.
- Next step: C3, move from SQLite to Neon Postgres using docs/schema.md. Only backend/app/store.py should need to change, plus DATABASE_URL. C4 to C6 not started.
