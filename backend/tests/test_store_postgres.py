"""The Postgres path of store.py.

The tests that need a real database are skipped unless TEST_DATABASE_URL is
set, and they must point at a scratch database, never the real runs table.
The offline tests need no database and always run."""
import os, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest
from app import engine, store

TEST_URL = os.environ.get("TEST_DATABASE_URL")
needs_db = pytest.mark.skipif(not TEST_URL, reason="TEST_DATABASE_URL is not set")


@pytest.fixture
def postgres(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_URL)
    monkeypatch.setattr(store, "_ready", False)
    return store


def _trace(**kw):
    tr = engine.Trace(headline="Postgres test headline", branch="classify",
                      final="Sports", confidence=0.95, mode="demo", ms=12)
    tr.passages = [{"file": "categories.md", "heading": "World", "score": 0.2}]
    tr.guardrails = [{"name": "answer is not empty", "passed": True}]
    for k, v in kw.items():
        setattr(tr, k, v)
    return tr


# ------------------------------------------------------------ offline, always run
def test_sqlite_is_the_default_when_database_url_is_unset():
    assert "DATABASE_URL" not in os.environ
    assert store.kind() == "sqlite"

def test_an_unreachable_database_gives_a_clear_error_without_the_address(monkeypatch):
    secret_host = "db-host-that-must-not-leak.invalid"
    monkeypatch.setenv("DATABASE_URL", f"postgresql://someuser:s3cretpw@{secret_host}:1/dbname")
    monkeypatch.setattr(store, "RETRY_PAUSE", 0)
    monkeypatch.setattr(store, "CONNECT_TIMEOUT", 2)
    with pytest.raises(store.DatabaseUnavailable) as e:
        store.count_runs()
    for secret in (secret_host, "s3cretpw", "someuser", "dbname"):
        assert secret not in str(e.value)

def test_a_malformed_url_is_reported_without_echoing_it(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:hunter2@host:notaport/db")
    with pytest.raises(store.StoreError) as e:
        store.count_runs()
    assert "hunter2" not in str(e.value)

def test_a_failed_postgres_save_does_not_stop_the_answer(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db-host-that-must-not-leak.invalid:1/d")
    monkeypatch.setattr(store, "RETRY_PAUSE", 0)
    monkeypatch.setattr(store, "CONNECT_TIMEOUT", 2)
    tr = engine.classify("Striker scores a goal in the cup match")
    assert tr.final == "Sports"

def test_a_save_against_an_unreachable_database_gives_up_within_about_five_seconds(monkeypatch):
    import time
    # 10.255.255.1 is not routable, so the connect hangs until the timeout, or fails at once
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@10.255.255.1:5432/d")
    assert store.SAVE_TIMEOUT == 4 and store.CONNECT_TIMEOUT == 10   # reads keep the longer timeout
    t0 = time.time()
    with pytest.raises(store.DatabaseUnavailable):
        store.save_run(_trace())
    assert time.time() - t0 < 5.5, "a save must make one 4 second attempt, not retry"


# ------------------------------------------------------- need a real scratch database
@needs_db
def test_a_saved_run_comes_back_with_the_same_shape_as_sqlite(postgres):
    postgres.save_run(_trace())
    row = postgres.recent_runs(1)[0]
    assert set(row) == {"id", "created_at", "headline", "branch", "answer",
                        "confidence", "blocked", "mode", "ms"}
    assert isinstance(row["confidence"], float) and row["confidence"] == 0.95
    assert isinstance(row["created_at"], str) and "T" in row["created_at"]
    assert row["blocked"] is False and row["answer"] == "Sports" and row["ms"] == 12

@needs_db
def test_count_grows_by_one_per_save(postgres):
    before = postgres.count_runs()
    postgres.save_run(_trace(blocked=True, final="I am not able to answer that one."))
    assert postgres.count_runs() == before + 1
    assert postgres.recent_runs(1)[0]["blocked"] is True

@needs_db
def test_recent_runs_are_newest_first_and_limited(postgres):
    for i in range(3):
        postgres.save_run(_trace(headline=f"order test {i}"))
    runs = postgres.recent_runs(2)
    assert len(runs) == 2 and runs[0]["id"] > runs[1]["id"]
    assert runs[0]["headline"] == "order test 2"

@needs_db
def test_a_rejected_row_names_the_constraint_not_the_connection(postgres):
    with pytest.raises(store.StoreError) as e:
        postgres.save_run(_trace(branch="not_a_branch"))
    assert "check constraint" in str(e.value)

@needs_db
def test_a_nul_character_in_a_headline_is_dropped_not_rejected(postgres):
    postgres.save_run(_trace(headline="before\x00after"))
    assert postgres.recent_runs(1)[0]["headline"] == "beforeafter"
