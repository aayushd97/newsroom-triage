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

- Done: setup; data/my_labels.csv; scoring on my_label with official_label kept; Groq pacing and retry-after; blocked answers scored as BLOCKED (tests/test_scoring.py); v1 token budget (reasoning_effort low, max_tokens 200); v2 SYSTEM_PROMPT rewritten from my Week 1 rules, low-confidence line at 0.6 (Claude Code's number, not mine). Tests: 19 passed, 1 failed (the confidence floor test, left on purpose).
- Latest versions.md row: v1, 21/30, 0.7000, kappa 0.6029, 1 blocked. v2 not yet appended. v2 live runs: 26/30, 0.8667, kappa 0.8193, 0 blocked, same in both runs, same four wrong items (ids 18, 23, 28, 29) in both. Per-item results in results/v2_scoring.csv (first run).
- Findings so far: prompt tokens per request went from 229 (v1) to 414 (v2). Every v2 answer had confidence 0.85 or above, so confidence does not separate right from wrong yet and no floor can be chosen from this data. Retrieved notes from categories.md are unchanged and may disagree with the prompt.
- Next step: append the v2 row once approved, then the CONFIDENCE_FLOOR step. C2 not started.
