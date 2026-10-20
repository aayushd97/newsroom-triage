"""Copy every row from a SQLite runs table into Postgres, once.

    cd backend
    .venv/bin/python scripts/migrate_sqlite_to_postgres.py [path/to/triage.db]

Safe to run twice. Rows keep their SQLite id, and a row whose id is already in
Postgres is skipped, so nothing is duplicated. After the copy the id counter is
moved past the highest id, so new rows carry on from there. The script prints
counts and statuses only, never the connection string.

Conversions:
  blocked     0 or 1                    to a real boolean
  passages    JSON text                 to JSONB
  guardrails  JSON text                 to JSONB
  created_at  local time string         to a timestamp, read as Europe/London
"""
import os, sys, json, pathlib, sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

BACKEND = pathlib.Path(__file__).resolve().parents[1]
for folder in (pathlib.Path.cwd(), BACKEND, BACKEND.parent):
    load_dotenv(folder / ".env", override=False)
sys.path.insert(0, str(BACKEND))

import psycopg
from psycopg.types.json import Jsonb
from app import store

LONDON = ZoneInfo("Europe/London")

INSERT = """INSERT INTO runs (id, created_at, headline, branch, answer, confidence,
                             passages, guardrails, blocked, mode, ms)
            OVERRIDING SYSTEM VALUE
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id) DO NOTHING"""


def convert(r):
    created = datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=LONDON)
    passages = json.loads(r["passages"]) if r["passages"] else []
    guardrails = json.loads(r["guardrails"]) if r["guardrails"] else []
    return (r["id"], created, store._clean(r["headline"]), r["branch"],
            store._clean(r["answer"]), r["confidence"], Jsonb(passages),
            Jsonb(guardrails), bool(r["blocked"]), r["mode"], r["ms"]), created


def main():
    if not os.environ.get("DATABASE_URL"):
        sys.exit("DATABASE_URL is not set, nothing to migrate into.")
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else BACKEND / "triage.db"
    if not src.exists():
        sys.exit(f"SQLite file not found: {src}")
    lite = sqlite3.connect(src)
    lite.row_factory = sqlite3.Row
    rows = lite.execute("SELECT * FROM runs ORDER BY id").fetchall()
    print(f"SQLite rows: {len(rows)}")

    conn = store._pg_open()
    inserted = skipped = rejected = unreadable = 0
    expected = {}
    try:
        before = conn.execute("SELECT count(*) FROM runs").fetchone()[0]
        print(f"Postgres rows before: {before}")
        for r in rows:
            try:
                values, created = convert(r)
            except (ValueError, TypeError):
                unreadable += 1
                continue
            try:
                with conn.transaction():          # a savepoint, so one bad row does not undo the rest
                    n = conn.execute(INSERT, values).rowcount
            except psycopg.Error as e:
                rejected += 1
                print(f"  id {r['id']} rejected: {type(e).__name__}: {e.diag.message_primary}")
                continue
            inserted += n
            skipped += 1 - n
            expected[r["id"]] = (values[2], values[3], values[8], values[10], created)
        top = conn.execute("SELECT max(id) FROM runs").fetchone()[0]
        if top is not None:
            conn.execute("SELECT setval(pg_get_serial_sequence('runs', 'id'), %s)", (top,))
        conn.commit()

        after = conn.execute("SELECT count(*) FROM runs").fetchone()[0]
        got = {row[0]: row[1:] for row in conn.execute(
            "SELECT id, headline, branch, blocked, ms, created_at FROM runs WHERE id = ANY(%s)",
            (list(expected),)).fetchall()}
    except psycopg.Error as e:
        conn.rollback()
        sys.exit(f"Migration stopped and rolled back: {store._wrap(e)}")
    finally:
        conn.close()

    # Same id must hold the same row. A different row under a known id means a clash.
    different = [i for i, want in expected.items() if i not in got or got[i] != want]
    print(f"Inserted: {inserted}, already there and skipped: {skipped}, "
          f"rejected: {rejected}, unreadable: {unreadable}")
    print(f"Postgres rows after: {after}")
    sample = sorted(expected)[:3] + sorted(expected)[-2:]
    print("Compared ids:", ", ".join(f"{i}={'same' if i not in different else 'DIFFERENT'}" for i in dict.fromkeys(sample)))
    print(f"Rows whose content differs between SQLite and Postgres: {len(different)}")
    if different or rejected or unreadable:
        sys.exit(1)


if __name__ == "__main__":
    main()
