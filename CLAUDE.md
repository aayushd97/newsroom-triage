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

- Done: Week 2 up to C6, except the frontend cold start. C2 split, C3 Neon Postgres (saves one 4 second attempt, reads 10 seconds and one retry), C5 retrieval (overlap default, BM25 behind RETRIEVAL_METHOD), C4 screenshots committed (five, none shows a key or database address; c4_database_down_health.png does not exist). C6 measured on the deployed backend https://newsroom-triage-backend.onrender.com. Tests: 46 passed, 5 skipped (the 5 need TEST_DATABASE_URL and have not been run against a real database).
- Latest versions.md row: v4, 26/30, 0.8667, kappa 0.8193, 0 blocked (BM25, default stays overlap).
- C6 numbers: warm latency median 784 ms, worst 1,212, fastest 452, average 761 (ms field median 606, taken before the database save). Cold start after 65 idle minutes: health 32.5 s, classify straight after 0.9 s, frontend NOT measured because I was only given a placeholder address. About 414 prompt and 50 completion tokens per request. 10,000 a day on gpt-oss-120b is about $0.92 a day. Free tier 1,000 requests and 200,000 tokens a day, so about 430 requests a day.
- Open points: the frontend live address is missing from the README and the frontend cold start is unmeasured. The 5 Postgres tests are unverified live. Render and .python-version, and one long /score request on Render, are still unverified. Root triage.db (201 rows) not migrated. Whether gpt-oss-20b holds accuracy is untested. The page shows only "HTTP 503" when Render's proxy answers for a stopped backend.
- Next step: send me the frontend address so I can add it and measure the page load. The two-page write-up is yours.
