"""Both retrieval methods, and the setting that switches between them."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest
from app import engine, config

METHODS = ["overlap", "bm25"]
THRESHOLD_NAME = {"overlap": "KNOWLEDGE_THRESHOLD", "bm25": "BM25_THRESHOLD"}
MANY_SHARED_WORDS = "business earnings market shares company profit world sports science research"
NONSENSE = "zzzz qqqq xxxx"


@pytest.fixture
def method(request, monkeypatch):
    monkeypatch.setattr(config, "RETRIEVAL_METHOD", request.param)
    return request.param


def test_the_setting_switches_the_algorithm(monkeypatch):
    monkeypatch.setitem(engine._METHODS, "overlap", lambda q: ["from overlap"])
    monkeypatch.setitem(engine._METHODS, "bm25", lambda q: ["from bm25"])
    monkeypatch.setattr(config, "RETRIEVAL_METHOD", "overlap")
    assert engine.retrieve("anything") == ["from overlap"]
    monkeypatch.setattr(config, "RETRIEVAL_METHOD", "bm25")
    assert engine.retrieve("anything") == ["from bm25"]


def test_the_two_methods_really_score_differently(monkeypatch):
    results = {}
    for m in METHODS:
        monkeypatch.setattr(config, "RETRIEVAL_METHOD", m)
        results[m] = engine.retrieve(MANY_SHARED_WORDS)
        assert results[m], f"{m} found nothing for a query full of shared words"
    assert results["overlap"][0]["score"] != results["bm25"][0]["score"]


def test_an_unknown_method_is_an_error_not_a_silent_fallback(monkeypatch):
    monkeypatch.setattr(config, "RETRIEVAL_METHOD", "embeddings")
    with pytest.raises(ValueError, match="RETRIEVAL_METHOD"):
        engine.retrieve("anything")


@pytest.mark.parametrize("method", METHODS, indirect=True)
@pytest.mark.parametrize("limit", [1, 2, 3])
def test_at_most_the_configured_number_of_passages(method, limit, monkeypatch):
    monkeypatch.setattr(config, "KNOWLEDGE_PASSAGES", limit)
    hits = engine.retrieve(MANY_SHARED_WORDS)
    assert 1 <= len(hits) <= limit


@pytest.mark.parametrize("method", METHODS, indirect=True)
def test_every_result_respects_its_own_threshold(method, monkeypatch):
    monkeypatch.setattr(config, "KNOWLEDGE_PASSAGES", 6)
    name = THRESHOLD_NAME[method]
    hits = engine.retrieve(MANY_SHARED_WORDS)
    assert hits and all(h["score"] >= getattr(config, name) for h in hits)
    monkeypatch.setattr(config, name, 1000)
    assert engine.retrieve(MANY_SHARED_WORDS) == []


@pytest.mark.parametrize("method", METHODS, indirect=True)
def test_nonsense_words_return_nothing(method):
    assert engine.retrieve(NONSENSE) == []
    assert engine.retrieve("") == []


def test_bm25_rarity_weight_is_always_above_zero_and_rarer_is_higher():
    n = 6
    weights = [engine._bm25_idf(n, k) for k in range(1, n + 1)]
    assert all(w > 0 for w in weights), "a word in every passage must not score zero or below"
    assert weights == sorted(weights, reverse=True)


def test_bm25_adding_words_to_a_question_never_lowers_a_score(monkeypatch):
    monkeypatch.setattr(config, "RETRIEVAL_METHOD", "bm25")
    monkeypatch.setattr(config, "BM25_THRESHOLD", 0)
    monkeypatch.setattr(config, "KNOWLEDGE_PASSAGES", 6)
    base = {h["heading"]: h["score"] for h in engine.retrieve("world")}
    more = {h["heading"]: h["score"] for h in engine.retrieve("world is a the and business")}
    assert base and all(more[h] >= s for h, s in base.items())
