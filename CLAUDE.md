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

- Done: setup; data/my_labels.csv; scoring on my_label with official_label kept; Groq pacing and retry-after; blocked answers scored as BLOCKED (tests/test_scoring.py); v1 token budget (reasoning_effort low, max_tokens 200); v2 SYSTEM_PROMPT from my Week 1 rules (0.6 low-confidence line is Claude Code's number, not mine); results/floor_table.md built offline; v3 CONFIDENCE_FLOOR = 0.6 committed. Tests: 20 passed.
- Latest versions.md row: v2, 26/30, 0.8667, kappa 0.8193, 0 blocked. v3 live run (floor 0.6): 26/30, 0.8667, kappa 0.8198, 0 blocked, not yet appended and its CSV is not saved. Same four wrong ids (18, 23, 28, 29) as v2. Item 28 changed answer between runs (Sci/Tech then Business), still wrong.
- Findings so far: prompt tokens per request 414 since v2. In v3 the lowest confidence on the 30 items was 0.70, so the floor blocked nothing. Hostile inputs (report-only): random characters and recipe were blocked by the floor, French was answered World at 0.95, and a two-category headline got a question back from the model, which the parser turned into World at 0.5, so only the floor stopped it.
- Estimated Groq use today: about 180 requests and about 69,000 tokens (estimate, not logged exactly).
- Next step: append v3 row once approved. C2 not started.
