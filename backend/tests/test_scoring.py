"""Scoring must count a blocked answer the same way in accuracy and kappa."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from sklearn.metrics import cohen_kappa_score
from app import engine

CATS = ["World", "Sports", "Business", "Sci/Tech"]
GOLDEN = [{"text": f"item {i}", "label": CATS[i % 4]} for i in range(30)]
LABEL = {g["text"]: g["label"] for g in GOLDEN}


def _fake_classify(blocked_texts):
    """Every item answered correctly, except the ones listed, which are blocked."""
    def classify(text):
        if text in blocked_texts:
            return engine.Trace(headline=text, branch="classify", final=engine.SAFE,
                                confidence=0.2, blocked=True)
        return engine.Trace(headline=text, branch="classify", final=LABEL[text],
                            confidence=0.9)
    return classify


def test_blocked_answers_are_scored_as_their_own_label(monkeypatch):
    blocked = {"item 0", "item 1", "item 2"}
    monkeypatch.setattr(engine, "classify", _fake_classify(blocked))
    s = engine.score(GOLDEN)
    got = {r["text"]: r["got"] for r in s["rows"]}
    assert all(got[t] == "BLOCKED" for t in blocked)
    assert s["blocked"] == 3
    assert s["total"] == 30 and s["correct"] == 27 and s["accuracy"] == 0.9


def test_kappa_uses_the_same_thirty_items_as_accuracy(monkeypatch):
    blocked = {"item 0", "item 1", "item 2"}
    monkeypatch.setattr(engine, "classify", _fake_classify(blocked))
    s = engine.score(GOLDEN)
    truth = [g["label"] for g in GOLDEN]
    preds = ["BLOCKED" if g["text"] in blocked else g["label"] for g in GOLDEN]
    assert s["kappa"] < 1.0, "blocked items must lower kappa, not vanish from it"
    assert s["kappa"] == round(cohen_kappa_score(truth, preds), 4)


def test_nothing_blocked_gives_perfect_scores(monkeypatch):
    monkeypatch.setattr(engine, "classify", _fake_classify(set()))
    s = engine.score(GOLDEN)
    assert s["blocked"] == 0 and s["accuracy"] == 1.0 and s["kappa"] == 1.0
