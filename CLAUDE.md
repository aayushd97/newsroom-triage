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

- Done: Week 2 steps up to C3. C2 split (backend/ FastAPI, frontend/ Gradio over HTTP via BACKEND_URL). C3: runs now live in Neon Postgres when DATABASE_URL is set, SQLite stays the default when it is unset. All database code is in backend/app/store.py (psycopg 3.3.6, 10 second connect timeout, one retry, table created once per process, prepared statements off, errors never include connection details). A failed save is logged by engine._save. /health reports the database kind, status and rows. Schema is docs/schema.md, updated where the code differs. DATABASE_URL is treated like a key: never printed, logged or committed.
- Migration: backend/triage.db (38 rows) copied to Neon with scripts/migrate_sqlite_to_postgres.py, ids kept, safe to run twice (second run inserted 0). A live run on Neon added id 39 to Neon only, SQLite stayed at 38. The older root triage.db (201 rows, earlier scoring history) is NOT migrated and its ids overlap, so it needs a decision.
- Index proof (100,000 scratch rows): 5.9 ms seq scan to 0.7 ms bitmap index scan, recorded in docs/schema.md. Scratch table dropped, runs_created_at_idx still present.
- Neon wake-up (results/neon_timing.md): 946 ms for the first connect plus query after 7 idle minutes, 153 ms straight after. One measurement.
- Tests: 30 passed, 5 skipped (the 5 need TEST_DATABASE_URL and have not been run against a real database).
- Latest versions.md row: v3, 26/30, 0.8667, kappa 0.8198, 0 blocked. No new row, scoring logic unchanged.
- Open points: the 5 Postgres tests are unverified live. If Neon is unreachable a failed save can add up to about 21 seconds to /classify (10 second timeout, one retry). Render and .python-version, and one long /score request on Render, are still unverified.
- Next step: C4, handle the other half being down (screenshots). C4 to C6 not started.
