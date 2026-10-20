# Newsroom Triage

Paste a news headline, get a category, see exactly how it decided.

Built for Week 2 of the AI and Machine Learning mentorship programme, Option C. It is two services that find each other through configuration.

- `backend/` is a FastAPI service. It owns the model call, retrieval, guardrails and the database.
- `frontend/` is a Gradio page. It knows nothing about the model or the database. It only calls the backend over HTTP.

The backend serves four endpoints, and their shapes are fixed:

- `POST /classify` takes a headline and returns the category, confidence, branch, passages, guardrails and whether it was blocked.
- `GET /runs?limit=50` returns the most recent questions and answers.
- `POST /score` takes a golden list of text and label pairs and returns the correct count, accuracy and kappa.
- `GET /health` returns the mode, the knowledge files and what is switched on.

## Environment variables

Backend:

- `GROQ_API_KEY` is the Groq key. Put it in a file called `.env` in the repo root or in `backend/`. Never commit it. With no key the backend runs on a built-in stand-in, and `/health` says `demo`.
- `DATABASE_URL` is the Postgres connection string, for example from Neon. When it is set, the backend stores runs in Postgres. When it is unset, the backend uses SQLite, so local runs and the tests need nothing. Treat it like a key: keep it in `.env`, never commit it, and never paste it into a chat or a screenshot.
- `TRIAGE_DB` is optional. It is the path of the SQLite file. The default is `backend/triage.db`.
- `PORT` is optional. The default is 8000.

Frontend:

- `BACKEND_URL` is the address of the backend. The default, `http://127.0.0.1:8000`, is for local use only. A deployed frontend must set it.
- `PORT` is optional. The default is 7860.

A variable that is already set in the environment always wins over `.env`.

## Run the backend

You need Python 3.12 or later. From the repo root:

    cd backend
    python3.12 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/python main.py

It listens on http://127.0.0.1:8000. Run it from the `backend` folder.

## Run the frontend

In a second terminal, from the repo root:

    cd frontend
    python3.12 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    BACKEND_URL=http://127.0.0.1:8000 .venv/bin/python app.py

Open http://127.0.0.1:7860. The Health tab shows which backend the page is talking to and what is switched on.

## The database

SQLite is the default. Postgres is used only when `DATABASE_URL` is set. The table, its keys, its index and the reasons are in `docs/schema.md`. All database code is in `backend/app/store.py`.

To copy the rows from a SQLite file into Postgres once, run this from the `backend` folder with `DATABASE_URL` set. It is safe to run twice, because rows keep their id and a row that is already there is skipped.

    .venv/bin/python scripts/migrate_sqlite_to_postgres.py

Neon puts a free database to sleep after about five minutes without use, so the first request after a quiet spell is slow. The backend waits up to 10 seconds to connect and tries once more. If the database cannot be reached, `/runs` answers with a 503, `/health` reports the database as down, and `/classify` still answers but cannot save the run.

## Retrieval

The app finds notes to show the model from the files in `backend/app/knowledge/`. The setting `RETRIEVAL_METHOD` in `backend/app/config.py` chooses how:

- `"overlap"` counts the words a headline shares with a note. This is the default.
- `"bm25"` is a standard search score written by hand in `backend/app/engine.py`. It counts rare words for more than common ones. It has its own `BM25_THRESHOLD`, `BM25_K1` and `BM25_B`.

Both use the same notes and the same word splitting, so only the scoring differs. The comparison is in `results/retrieval_offline.md` (no model calls) and `results/v4_scoring.csv` (one live scoring run). Before and after traces for four headlines are in `results/retrieval_before.md` and `results/retrieval_after.md`.

## The file you change to tune the assistant

`backend/app/config.py`. It holds the prompt, the routing rules, the guardrails, the confidence floor and the token settings.

## Tests

    cd backend
    .venv/bin/pytest -q

The tests run in demo mode on a temporary SQLite database. They never read `.env`, never call Groq and never touch Neon. Five more tests need a real Postgres database and are skipped unless `TEST_DATABASE_URL` is set. Point it at a scratch database, never the real one.

## Scoring log

`results/versions.md` records every scoring run. The scoring uses my own Week 1 hand labels, with the official label kept as a second column.

## Live deployment and measurements

- Backend: https://newsroom-triage-backend.onrender.com
- Frontend: https://newsroom-triage-frontend.onrender.com/

Measured on the deployed backend on 20 October 2026. The raw tables are in `results/`.

- Warm latency, 20 classify requests, 4 seconds apart: median 784 ms, fastest 452 ms, worst 1,212 ms, average 761 ms as seen from my laptop. The backend's own `ms` field was 606 ms median. It stops before the database save, so the difference of about 150 ms is the network, Render and the save. See `results/latency_deployed.md`.
- Cold start after 65 idle minutes: the first request, `GET /health`, took 32.5 seconds, and a classify straight after took 0.9 seconds. Both Render and Neon had gone to sleep, so the 32.5 seconds includes both and I could not separate them. The frontend page load took 131 ms but it was already awake, so it is not a cold start figure. See `results/cold_start_deployed.md`.
- Tokens per classify request: about 414 prompt and 50 completion, taken from the 30 item scoring run `results/v3_scoring.csv` (12,432 and 1,504 tokens over 30 items), because the backend does not return token counts.
- Cost of 10,000 classifications a day on `openai/gpt-oss-120b`, at $0.15 per million input tokens and $0.60 per million output tokens from Groq's models page: 414.4 x 0.15 + 50.1 x 0.60 is about 92 millionths of a dollar per request, so about $0.92 a day, or about $28 over 30 days. I am fairly sure of the prices but Groq's pricing page did not list them, so check the console before quoting them.
- The free tier does not fit 10,000 a day. Groq's limits page lists 1,000 requests and 200,000 tokens a day for this model, and 10,000 requests use about 4.6 million tokens, which is 23 times the token limit. The token limit allows about 430 requests a day.
- If the bill had to be smaller, the biggest single change is a smaller model, `openai/gpt-oss-20b`, at half the price. It would change accuracy, so it needs a scoring run first. Dropping the retrieved notes or shortening the prompt each save about 16 to 18 percent. Even all of these together leave about a third of the bill, so a tenth would need some requests to skip the model.

## Deploying on Render

Use two services, one with root directory `backend` and one with `frontend`. For both, the build command is `pip install -r requirements.txt`. The start command is `python main.py` for the backend and `python app.py` for the frontend. Set `PYTHON_VERSION` to a full version such as `3.12.3` on both. Render's documentation says a `.python-version` file is read from the root of the repo, and it does not say whether the files inside `backend/` and `frontend/` are read, so the environment variable is the safe choice. On the backend set `GROQ_API_KEY` and `DATABASE_URL`. On the frontend set `BACKEND_URL` to the backend's public address.
