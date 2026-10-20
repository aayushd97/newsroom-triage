"""All database access lives in this file, so the database can be swapped by
changing only this file. Today it is SQLite."""
import os, json, time, sqlite3, pathlib

HERE = pathlib.Path(__file__).parent
DB_PATH = os.environ.get("TRIAGE_DB", str(HERE.parent / "triage.db"))


def db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            headline TEXT NOT NULL,
            branch TEXT NOT NULL,
            answer TEXT,
            confidence REAL,
            passages TEXT,
            guardrails TEXT,
            blocked INTEGER NOT NULL DEFAULT 0,
            mode TEXT NOT NULL,
            ms INTEGER NOT NULL)""")

def save_run(tr):
    """Store one answered question. tr is the engine's Trace."""
    init_db()   # cheap, and the table comes back if the file was removed
    with db() as c:
        c.execute("""INSERT INTO runs (created_at, headline, branch, answer,
                     confidence, passages, guardrails, blocked, mode, ms)
                     VALUES (?,?,?,?,?,?,?,?,?,?)""",
                  (time.strftime("%Y-%m-%d %H:%M:%S"), tr.headline, tr.branch,
                   tr.final, tr.confidence, json.dumps(tr.passages),
                   json.dumps(tr.guardrails), int(tr.blocked), tr.mode, tr.ms))

def recent_runs(limit=50):
    with db() as c:
        rows = c.execute("""SELECT id, created_at, headline, branch, answer,
                            confidence, blocked, mode, ms
                            FROM runs ORDER BY id DESC LIMIT ?""", (limit,)).fetchall()
    return [dict(r) for r in rows]

def count_runs():
    with db() as c:
        return c.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
