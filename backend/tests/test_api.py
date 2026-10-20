"""The four endpoints, through FastAPI's TestClient, in demo mode (no key)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from main import api
from app import engine, store

# Words the demo stand-in knows, so the answer is confident and not blocked.
SPORTS = "Striker scores a goal in the cup match"
BUSINESS = "Bank reports record profit as shares rise on earnings"


@pytest.fixture
def client():
    return TestClient(api)


def test_classify_returns_the_contract_shape(client):
    r = client.post("/classify", json={"headline": SPORTS})
    assert r.status_code == 200
    d = r.json()
    for key in ("category", "confidence", "branch", "passages", "guardrails", "blocked"):
        assert key in d
    for key in ("raw_answer", "why_branch", "mode", "ms"):
        assert key in d
    assert d["category"] == "Sports" and d["blocked"] is False
    assert d["branch"] == "classify" and d["mode"] == "demo"
    assert isinstance(d["passages"], list) and isinstance(d["guardrails"], list)


def test_runs_lists_what_was_asked(client):
    headline = "Runs test: " + BUSINESS
    client.post("/classify", json={"headline": headline})
    r = client.get("/runs", params={"limit": 5})
    assert r.status_code == 200
    runs = r.json()["runs"]
    assert 1 <= len(runs) <= 5
    assert runs[0]["headline"] == headline
    assert runs[0]["blocked"] is False


def test_score_returns_the_contract_shape(client):
    golden = [{"text": SPORTS, "label": "Sports"},
              {"text": BUSINESS, "label": "Business"},
              {"text": SPORTS, "label": "World"}]
    r = client.post("/score", json={"golden": golden})
    assert r.status_code == 200
    d = r.json()
    for key in ("correct", "total", "accuracy", "kappa", "blocked", "rows"):
        assert key in d
    assert d["total"] == 3 and d["correct"] == 2
    assert d["accuracy"] == pytest.approx(0.6667, abs=1e-4)
    assert len(d["rows"]) == 3


def test_health_reports_mode_and_never_the_key(client, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_this_is_a_fake_test_key")
    d = client.get("/health").json()
    assert d["mode"] == "live" and d["key_present"] is True
    assert "gsk_this_is_a_fake_test_key" not in client.get("/health").text
    monkeypatch.delenv("GROQ_API_KEY")
    d = client.get("/health").json()
    assert d["mode"] == "demo" and d["key_present"] is False
    assert isinstance(d["knowledge"], list) and "categories.md" in d["knowledge"]
    assert d["database"]["status"] == "ok"
    assert d["model"]


def test_classify_still_answers_when_the_database_save_fails(client, monkeypatch):
    def broken(_):
        raise RuntimeError("database is down")
    monkeypatch.setattr(store, "save_run", broken)
    r = client.post("/classify", json={"headline": SPORTS})
    assert r.status_code == 200
    d = r.json()
    assert d["category"] == "Sports" and d["blocked"] is False


def test_runs_and_health_say_so_when_the_database_is_down(client, monkeypatch):
    def broken(*_):
        raise RuntimeError("database is down")
    monkeypatch.setattr(store, "recent_runs", broken)
    monkeypatch.setattr(store, "count_runs", broken)
    r = client.get("/runs")
    assert r.status_code == 503 and "database" in r.json()["detail"].lower()
    assert client.get("/health").json()["database"]["status"] == "down"
