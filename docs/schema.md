# Database schema: tables, keys, indexes, and why

This is the Postgres schema for Neon. The SQLite version used by the local fallback and the existing tests is left as it was.

## Tables

One table, `runs`. Every question the app is asked is one row, and nothing else needs to be stored.

I rejected splitting out `run_passages` and `run_guardrails` tables. That would let me ask how often one guardrail fails, but nothing in this app asks that. It would also need joins on every read, and `/classify` already returns passages and guardrails as lists, so a single row with two JSON columns matches the shape of the data. I would revisit this if I needed to analyse guardrail failures across many runs.

I rejected a table for scoring history as well. It is outside the brief, and `results/versions.md` already records each scoring run.

```sql
CREATE TABLE runs (
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
);

CREATE INDEX runs_created_at_idx ON runs (created_at);
```

All eleven SQLite fields are kept, with the same names.

## Columns

**id** is BIGINT, an identity column. SQLite used an auto-incrementing integer. Cost: new rows start at 1 in an empty Postgres table. The rows copied from SQLite keep their old ids, and the id counter was moved past the highest one, so new rows carry on from there.

**created_at** is TIMESTAMPTZ with a default of `now()`. SQLite stored a local time string with no time zone. Postgres stores an exact moment, so sorting and filtering by time work properly. Cost: the Postgres path should let the database fill this in rather than sending `time.strftime(...)` from Python, and the SQLite fallback keeps its text column.

**headline** is TEXT NOT NULL. No length limit, because a pasted article can be long and Postgres handles long text without a penalty. Postgres text cannot hold a NUL character, so the Postgres path drops any NUL from the headline and the answer before saving. SQLite accepted them.

**branch** is TEXT with a CHECK for classify, explain or refuse. A CHECK is easier to change than an ENUM, because adding a branch is one line and not a type migration. Cost: if I add a routing branch in `config.py` and forget the CHECK, inserts for it fail (see Constraints).

**answer** is TEXT and nullable, as in SQLite.

**confidence** is NUMERIC(3,2) with a CHECK between 0 and 1. The model returns values like 0.95 and the app clamps them to 0 to 1, so two decimals is enough and the values are stored exactly. Cost: Python gets Decimal objects back, which have to be converted to float before they go into the `/classify` JSON reply.

**passages** and **guardrails** are JSONB, defaulting to an empty list. SQLite stored these as JSON text. JSONB can be queried and indexed later, and it rejects malformed JSON. Cost: the SQLite code writes `json.dumps(...)`, so the Postgres path must write the same string with a `::jsonb` cast or a JSON adapter.

**blocked** is BOOLEAN NOT NULL DEFAULT false. SQLite used 0 or 1. A real boolean makes any other value impossible. Cost: `engine._save` writes `int(tr.blocked)`, so the Postgres path must write a real boolean while the SQLite path keeps the integer.

**mode** is TEXT with a CHECK for live or demo.

**ms** is INTEGER NOT NULL with a CHECK that it is not negative.

## Keys

The primary key is `id`, an identity column. The primary key's index also serves `ORDER BY id DESC LIMIT 50`, which is the query behind `/runs`, so that query needs no extra index.

## Constraints

NOT NULL is kept on the same columns as SQLite. CHECKs cover the three-value columns (branch, mode), the range of confidence, and ms.

The important behaviour is what happens when a constraint fails. `engine._save` catches every error and carries on, so a rejected row would vanish without a trace. I want to keep that rule, because a broken database must never stop an answer, and C4 requires the app to keep classifying when the database is down. The change I want is that a failed save is logged with the error message, so a rejected row is visible. Without it, adding a branch to `config.py` would silently lose every run on that branch.

## Indexes

I ran this query (replace the date window as needed):

```sql
SELECT count(*) FILTER (WHERE blocked) AS blocked, count(*) AS total
FROM runs
WHERE created_at >= now() - interval '24 hours';
```

This is the question I would ask in practice: how many answers were blocked recently. The index is `runs_created_at_idx` on `created_at`.

Without an index, Postgres reads every row to apply the time filter. With one, it jumps to the recent rows. A table of a few hundred rows will not show this, because Postgres reads a small table directly even when an index exists. I measured it on a scratch copy seeded with about 100,000 generated rows:

The scratch table `runs_scratch` has the same columns and constraints as `runs` and no index on `created_at`. It holds 100,000 generated rows spread over about four months (22 June to 20 October), with 12 percent blocked. 834 rows fall in the last 24 hours. I ran the query with `EXPLAIN (ANALYZE, BUFFERS)` three times before and three times after creating the index and running `ANALYZE`, and kept the middle run each time.

Before the index. Execution times: 5.936, 5.941, 5.898 ms. Middle run, 5.936 ms:

```
Aggregate  (cost=3313.78..3313.80 rows=1 width=16) (actual time=5.912..5.912 rows=1.00 loops=1)
  Buffers: shared hit=2054
  ->  Seq Scan on runs_scratch  (cost=0.00..3204.24 rows=21909 width=1) (actual time=0.011..5.836 rows=834.00 loops=1)
        Filter: (created_at >= (now() - '24:00:00'::interval))
        Rows Removed by Filter: 99166
        Buffers: shared hit=2054
Planning Time: 0.058 ms
Execution Time: 5.936 ms
```

After the index. Execution times: 0.752, 0.701, 0.692 ms. Middle run, 0.701 ms:

```
Aggregate  (cost=1559.63..1559.64 rows=1 width=16) (actual time=0.676..0.677 rows=1.00 loops=1)
  Buffers: shared hit=688
  ->  Bitmap Heap Scan on runs_scratch  (cost=18.43..1555.68 rows=791 width=1) (actual time=0.099..0.598 rows=834.00 loops=1)
        Recheck Cond: (created_at >= (now() - '24:00:00'::interval))
        Heap Blocks: exact=683
        Buffers: shared hit=688
        ->  Bitmap Index Scan on runs_scratch_created_at_idx  (cost=0.00..18.23 rows=791 width=0) (actual time=0.048..0.048 rows=834.00 loops=1)
              Index Cond: (created_at >= (now() - '24:00:00'::interval))
              Index Searches: 1
              Buffers: shared hit=5
Planning:
  Buffers: shared hit=4
Planning Time: 0.093 ms
Execution Time: 0.701 ms
```

In plain English: before the index Postgres read all 100,000 rows and threw 99,166 of them away, and after it Postgres used the index, found the 834 recent rows directly and read about a third of the pages, so the query went from about 5.9 ms to about 0.7 ms, roughly 8 times faster. Postgres did choose the index, as a bitmap index scan and not a plain index scan, because my generated rows were stored in random time order. Real runs are stored in time order, so I would expect a plain index scan there, but I have not tested that. Both times are small because every page was already in memory (all `shared hit`). The gap would be wider on a cold read, and it grows with the table.

Indexes I rejected:

- On `id`: the primary key already has one.
- Partial index `WHERE blocked`: it would help a "show me blocked runs" page, and I have no such query yet.
- `(mode, created_at)`: I have no query that filters by mode.
- On `branch`: it has three values, so an index would rarely be chosen over reading the table.

Each index slows inserts a little and uses space, and this table is written on every request, so I kept it to one.

## Migration notes

- Postgres is used when `DATABASE_URL` is set. Without it the app uses SQLite as before. The existing tests rely on that, and it also gives the "database down, still classifies" behaviour.
- The Postgres path writes `blocked` as a boolean, `passages` and `guardrails` as JSON, and leaves `created_at` to the database.
- Existing rows in `triage.db` are copied once by a script. Converting them: `blocked` 0 or 1 to false or true, the JSON text to JSONB, and `created_at` from a local-time string to a timestamp. The old strings came from `time.strftime`, which uses the local clock, so they are read as Europe/London time.
- The Neon connection string points at the pooled endpoint (PgBouncer). Neon's documentation says its PgBouncer supports protocol-level prepared statements, but the code still switches them off (`prepare_threshold=None`), because nothing here repeats a query often enough to gain from them and switching them off rules out a class of errors. The code never uses `SET` or SQL-level `PREPARE`, which the pooled endpoint does not support.
- The code uses `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` with the DDL above. It runs them once per process, and again on the next request if that failed.
- Error messages from the Postgres path name the problem (could not connect, login rejected, or which constraint failed) and never include the host, user or password.
- Neon sleeps after five minutes without activity, so the first query after a quiet spell is slow. The connection needs a timeout and a clear failure message, and the wake-up time goes into the latency figures.