"""All database access lives in this file, so the database can be swapped by
changing only this file. SQLite is the default. Postgres (Neon) is used only
when DATABASE_URL is set. The table is described in docs/schema.md.

Nothing here ever puts a connection detail (host, user, password) into an
error message, because those messages get logged and shown."""
import os, json, time, sqlite3, pathlib, threading

HERE = pathlib.Path(__file__).parent
DB_PATH = os.environ.get("TRIAGE_DB", str(HERE.parent / "triage.db"))

CONNECT_TIMEOUT = 10   # seconds. Neon can take a few seconds to wake up.
RETRY_PAUSE = 1.0      # seconds between the first failed connect and the one retry


class StoreError(RuntimeError):
    """A database problem. The message is safe to log and to show."""

class DatabaseUnavailable(StoreError):
    """The database could not be reached or refused the login."""


def _url():
    return os.environ.get("DATABASE_URL") or None

def kind():
    return "postgres" if _url() else "sqlite"


# ---------------------------------------------------------------- SQLite
def db():
    """The SQLite connection. Kept for the SQLite path and the existing tests."""
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def _sqlite_init():
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

def _sqlite_save(tr):
    _sqlite_init()   # cheap, and the table comes back if the file was removed
    with db() as c:
        c.execute("""INSERT INTO runs (created_at, headline, branch, answer,
                     confidence, passages, guardrails, blocked, mode, ms)
                     VALUES (?,?,?,?,?,?,?,?,?,?)""",
                  (time.strftime("%Y-%m-%d %H:%M:%S"), tr.headline, tr.branch,
                   tr.final, tr.confidence, json.dumps(tr.passages),
                   json.dumps(tr.guardrails), int(tr.blocked), tr.mode, tr.ms))

def _sqlite_recent(limit):
    _sqlite_init()
    with db() as c:
        rows = c.execute("""SELECT id, created_at, headline, branch, answer,
                            confidence, blocked, mode, ms
                            FROM runs ORDER BY id DESC LIMIT ?""", (limit,)).fetchall()
    return [dict(r) for r in rows]

def _sqlite_count():
    _sqlite_init()
    with db() as c:
        return c.execute("SELECT COUNT(*) FROM runs").fetchone()[0]


# -------------------------------------------------------------- Postgres
# The same DDL as docs/schema.md.
PG_DDL = [
    """CREATE TABLE IF NOT EXISTS runs (
        id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
        headline    TEXT NOT NULL,
        branch      TEXT NOT NULL CHECK (branch IN ('classify', 'explain', 'refuse')),
        answer      TEXT,
        confidence  NUMERIC(3,2) CHECK (confidence BETWEEN 0 AND 1),
        passages    JSONB NOT NULL DEFAULT '[]'::jsonb,
        guardrails  JSONB NOT NULL DEFAULT '[]'::jsonb,
        blocked     BOOLEAN NOT NULL DEFAULT false,
        mode        TEXT NOT NULL CHECK (mode IN ('live', 'demo')),
        ms          INTEGER NOT NULL CHECK (ms >= 0)
    )""",
    "CREATE INDEX IF NOT EXISTS runs_created_at_idx ON runs (created_at)",
]

_ready = False                 # has the table been created in this process?
_ready_lock = threading.Lock()


def _wrap(e):
    """Turn a driver error into one with a message that is safe to log."""
    import psycopg
    if isinstance(e, psycopg.OperationalError):
        return DatabaseUnavailable("lost the connection to the database")
    primary = getattr(getattr(e, "diag", None), "message_primary", None) or "database error"
    return StoreError(f"{type(e).__name__}: {primary}")

def _pg_connect():
    """Open a connection. One retry if it fails, because a sleeping Neon database
    may time out the first attempt while it wakes."""
    import psycopg
    for attempt in (1, 2):
        try:
            return psycopg.connect(_url(), connect_timeout=CONNECT_TIMEOUT)
        except psycopg.OperationalError as e:
            if (e.sqlstate or "").startswith("28"):     # bad login, retrying will not help
                raise DatabaseUnavailable("the database rejected the login") from None
            if attempt == 2:
                raise DatabaseUnavailable("could not connect to the database") from None
            time.sleep(RETRY_PAUSE)
        except (psycopg.Error, ValueError):
            raise StoreError("DATABASE_URL could not be used, check its format") from None

def _pg_open():
    """A connection with the table in place. The table is created once per
    process, and again on the next call if that failed."""
    global _ready
    import psycopg
    conn = _pg_connect()
    if not _ready:
        with _ready_lock:
            if not _ready:
                try:
                    for sql in PG_DDL:
                        conn.execute(sql)
                    conn.commit()
                except psycopg.Error as e:
                    conn.close()
                    raise _wrap(e) from None
                _ready = True
    return conn

def _clean(s):
    """Postgres text cannot hold a NUL character. SQLite can, so drop it here."""
    return None if s is None else str(s).replace("\x00", "")

def _pg_save(tr):
    import psycopg
    from psycopg.types.json import Jsonb
    conn = _pg_open()
    try:
        with conn:   # commits, or rolls back on an error, then closes
            # created_at is left out on purpose, the database fills it in
            conn.execute("""INSERT INTO runs (headline, branch, answer, confidence,
                            passages, guardrails, blocked, mode, ms)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                         (_clean(tr.headline), tr.branch, _clean(tr.final),
                          float(tr.confidence), Jsonb(tr.passages), Jsonb(tr.guardrails),
                          bool(tr.blocked), tr.mode, int(tr.ms)))
    except psycopg.Error as e:
        raise _wrap(e) from None

def _pg_recent(limit):
    import psycopg
    conn = _pg_open()
    try:
        with conn:
            rows = conn.execute("""SELECT id, created_at, headline, branch, answer,
                                   confidence, blocked, mode, ms
                                   FROM runs ORDER BY id DESC LIMIT %s""",
                                (limit,)).fetchall()
    except psycopg.Error as e:
        raise _wrap(e) from None
    # Same shape as SQLite: confidence as a float, created_at as an ISO string
    return [{"id": r[0], "created_at": r[1].isoformat(),
             "headline": r[2], "branch": r[3], "answer": r[4],
             "confidence": None if r[5] is None else float(r[5]),
             "blocked": r[6], "mode": r[7], "ms": r[8]} for r in rows]

def _pg_count():
    import psycopg
    conn = _pg_open()
    try:
        with conn:
            return conn.execute("SELECT count(*) FROM runs").fetchone()[0]
    except psycopg.Error as e:
        raise _wrap(e) from None


# ------------------------------------------------- what the rest of the app calls
def init_db():
    if kind() == "postgres":
        _pg_open().close()
    else:
        _sqlite_init()

def save_run(tr):
    """Store one answered question. tr is the engine's Trace."""
    return _pg_save(tr) if kind() == "postgres" else _sqlite_save(tr)

def recent_runs(limit=50):
    return _pg_recent(limit) if kind() == "postgres" else _sqlite_recent(limit)

def count_runs():
    return _pg_count() if kind() == "postgres" else _sqlite_count()
