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
- `DATABASE_URL` is for the Postgres step. It is not used yet. SQLite is the database for now, and it stays the fallback when this variable is unset.
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

## The file you change to tune the assistant

`backend/app/config.py`. It holds the prompt, the routing rules, the guardrails, the confidence floor and the token settings.

## Tests

    cd backend
    .venv/bin/pytest -q

The tests run in demo mode on a temporary database. They never read `.env` and never call Groq.

## Scoring log

`results/versions.md` records every scoring run. The scoring uses my own Week 1 hand labels, with the official label kept as a second column.

## Deploying on Render

Use two services, one with root directory `backend` and one with `frontend`. For both, the build command is `pip install -r requirements.txt`. The start command is `python main.py` for the backend and `python app.py` for the frontend. Set `PYTHON_VERSION` to a full version such as `3.12.3` on both. Render's documentation says a `.python-version` file is read from the root of the repo, and it does not say whether the files inside `backend/` and `frontend/` are read, so the environment variable is the safe choice. On the backend set `GROQ_API_KEY`. On the frontend set `BACKEND_URL` to the backend's public address.
