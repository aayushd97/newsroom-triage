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

- Done: Week 2 up to C3, plus C5. C2 split (backend FastAPI, frontend Gradio over HTTP via BACKEND_URL). C3 Postgres on Neon when DATABASE_URL is set, SQLite default, all in backend/app/store.py. Saves now make one 4 second connect attempt with no retry, reads keep 10 seconds and one retry. C5: RETRIEVAL_METHOD setting ("overlap" default, or "bm25"), hand-written BM25 with BM25_THRESHOLD 0.7, k1 1.5, b 0.75, tests in backend/tests/test_retrieval.py. Tests: 46 passed, 5 skipped (the 5 need TEST_DATABASE_URL and have not been run against a real database).
- Latest versions.md row: v3, 26/30, 0.8667, kappa 0.8198, 0 blocked. v4 NOT appended yet, waiting for my say so. Offered row: "RETRIEVAL_METHOD bm25, BM25_THRESHOLD 0.7, k1 1.5, b 0.75. Prompt and floor unchanged." with 26/30, 0.8667, kappa 0.8193, 0 blocked.
- C5 findings: offline, top passage matches my label for 6/30 (overlap) and 7/30 (BM25); the label's own passage appears at all for 7/30 and 10/30; BM25 puts a non-category passage first more often (17/30 against 13/30). Live BM25 run: same score as v3. 20 of 30 items got different passages, none changed answer. The one item that changed answer (28) had identical passages under both methods, so that is run-to-run noise. Prompt tokens 12,282 against 12,432. Default method not changed.
- Open points: whether the model uses the retrieved notes at all is untested (an ablation with no passages would show it, costs 30 requests). BM25 here does not remove common words, so a pile of common words can pass its threshold. The 5 Postgres tests are unverified live. Render and .python-version, and one long /score request on Render, are still unverified. Root triage.db (201 rows) still not migrated.
- Next step: my decision on the v4 row and the default method. C4 (the other half being down, screenshots) and C6 (cost and speed) not started.
