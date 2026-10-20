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

- Done: setup; data/my_labels.csv copied; scoring uses my_label with official_label kept; Groq calls paced (30 req, 8,000 tokens per minute) with retry-after on 429; blocked answers scored as BLOCKED; tests/test_scoring.py added. Tests: 3 failed (the planted config tests), 17 passed.
- Latest runs (not yet in versions.md): demo 18/30, 0.600, kappa 0.4322, 0 blocked. Live v0 5/30, 0.1667, kappa 0.1156, 24 blocked.
- Known cause of the 24 blocks: with retrieved notes in the prompt, gpt-oss-120b spends about 78 of max_tokens=80 on reasoning, finish_reason is "length", content is empty, parse gives UNPARSED.
- Next step: user decides whether to append the v0 row, then the C1 config.py fixes (prompt, tie-break, floor) and the max_tokens or reasoning_effort fix. C2 not started.
