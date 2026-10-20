"""The working parts. Option A never needs to read this file."""
import os, re, json, time, pathlib, math
from dataclasses import dataclass, field, asdict
from typing import Optional

from . import config

HERE = pathlib.Path(__file__).parent
CATS = ["World", "Sports", "Business", "Sci/Tech"]

# The database code lives in store.py. These names stay here because callers
# and tests already use engine.db() and engine.init_db().
from . import store
from .store import db, init_db


# -------------------------------------------------------------- retrieval
def _tokens(s):
    return re.findall(r"[a-z0-9]+", str(s).lower())

def _chunks():
    """Each heading section of each switched-on file is one passage."""
    out = []
    for name in config.KNOWLEDGE_FILES:
        p = HERE / "knowledge" / name
        if not p.exists():
            continue
        current, buf = "(top)", []
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith("#"):
                if buf:
                    out.append((name, current, " ".join(buf).strip()))
                current, buf = line.lstrip("# ").strip(), []
            else:
                buf.append(line)
        if buf:
            out.append((name, current, " ".join(buf).strip()))
    return [c for c in out if c[2]]

def retrieve(question):
    """Plain keyword overlap. Deliberately simple so its failures are visible."""
    q = set(_tokens(question))
    if not q:
        return []
    scored = []
    for fname, heading, body in _chunks():
        b = set(_tokens(heading + " " + body))
        if not b:
            continue
        score = len(q & b) / math.sqrt(len(b))
        if score >= config.KNOWLEDGE_THRESHOLD:
            scored.append({"file": fname, "heading": heading,
                           "text": body[:400], "score": round(score, 3)})
    scored.sort(key=lambda d: -d["score"])
    return scored[: config.KNOWLEDGE_PASSAGES]


# ---------------------------------------------------------------- routing
def route(question):
    low = str(question).lower()
    for phrase, branch in config.ROUTING_RULES:
        if phrase.lower() in low:
            return branch, f'matched the rule "{phrase}"'
    return "classify", "no rule matched, so the default branch was used"


# ------------------------------------------------------------ model call
def _demo_classify(text):
    """Used when there is no API key. A deliberately dumb stand-in."""
    hints = {
        "Sports":   ["match", "cup", "olympic", "coach", "league", "striker",
                     "goal", "season", "tournament", "championship", "player"],
        "Business": ["profit", "shares", "market", "bank", "earnings", "deal",
                     "economy", "prices", "revenue", "merger", "billion"],
        "Sci/Tech": ["software", "chip", "nasa", "research", "scientists",
                     "space", "internet", "microsoft", "technology", "study"],
        "World":    ["president", "minister", "troops", "election", "talks",
                     "killed", "government", "united nations", "border"],
    }
    toks = set(_tokens(text))
    best, score = "World", 0
    for cat, words in hints.items():
        hit = len(toks & set(words))
        if hit > score:
            best, score = cat, hit
    conf = min(0.35 + 0.15 * score, 0.95)
    return best, round(conf, 2)

class RateLimited(RuntimeError):
    """Groq answered 429. Not a bad key: wait retry_after seconds and try again."""
    def __init__(self, retry_after):
        super().__init__(f"rate limited by Groq, retry after {retry_after}s")
        self.retry_after = retry_after

_window = []   # [time, tokens] for each live call in the last minute

def _pace(estimate):
    """Wait until one more call fits inside the per-minute request and token limits."""
    while True:
        now = time.time()
        _window[:] = [w for w in _window if now - w[0] < 60]
        used = sum(w[1] for w in _window)
        if not _window or (len(_window) < config.REQUESTS_PER_MINUTE
                           and used + estimate <= config.TOKENS_PER_MINUTE):
            entry = [now, estimate]
            _window.append(entry)
            return entry
        time.sleep(max(0.1, 60 - (now - _window[0][0]) + 0.05))

def _groq_classify(text, prompt, passages):
    import requests
    key = os.environ["GROQ_API_KEY"]
    context = ""
    if passages:
        context = "\n\nYou may use these notes:\n" + "\n".join(
            f"- {p['heading']}: {p['text']}" for p in passages)
    body = {
        "model": config.MODEL,
        "temperature": config.TEMPERATURE,
        "max_tokens": config.MAX_TOKENS,
        "reasoning_effort": config.REASONING_EFFORT,
        "messages": [
            {"role": "system", "content": prompt + context},
            {"role": "user", "content":
             f"News item:\n{text}\n\n"
             'Reply with JSON only: {"category": "...", "confidence": 0.0}'},
        ],
    }
    # Rough guess of the call's size: about 3 characters a token, plus the reply cap.
    sent = sum(len(m["content"]) for m in body["messages"])
    entry = _pace(sent // 3 + body["max_tokens"])
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers={"Authorization": f"Bearer {key}"},
                      json=body, timeout=60)
    if r.status_code == 429:
        try:
            wait = float(r.headers.get("retry-after", ""))
        except ValueError:
            wait = 0.0
        raise RateLimited(wait)
    r.raise_for_status()
    data = r.json()
    entry[1] = data.get("usage", {}).get("total_tokens", entry[1])
    raw = data["choices"][0]["message"]["content"]
    return _parse(raw)

def _parse(raw):
    """Models wrap JSON in prose and fences. Get the category out anyway."""
    s = str(raw).strip()
    m = re.search(r"\{.*\}", s, re.S)
    if m:
        try:
            d = json.loads(m.group(0))
            cat = str(d.get("category", "")).strip()
            conf = float(d.get("confidence", 0.5))
            for c in CATS:
                if cat.lower() == c.lower():
                    return c, max(0.0, min(1.0, conf))
        except Exception:
            pass
    low = s.lower()
    for c in CATS:
        if c.lower() in low:
            return c, 0.5
    if "sci" in low or "tech" in low:
        return "Sci/Tech", 0.5
    return "UNPARSED", 0.0

def live_mode():
    return bool(os.environ.get("GROQ_API_KEY"))


# ------------------------------------------------------------- guardrails
def check(answer, confidence, branch):
    results = []
    low = str(answer).lower()

    hit = [p for p in config.BANNED_PHRASES if p.lower() in low]
    results.append({"name": "no banned phrase", "passed": not hit,
                    "detail": f"found {hit}" if hit else "none found",
                    "blocking": True})

    ok_cat = branch != "classify" or answer in config.ALLOWED_CATEGORIES
    results.append({"name": "answer is one of the four", "passed": ok_cat,
                    "detail": answer if not ok_cat else "yes",
                    "blocking": True})

    sure = confidence >= config.CONFIDENCE_FLOOR
    results.append({"name": "confident enough", "passed": sure,
                    "detail": f"{confidence:.2f} against floor {config.CONFIDENCE_FLOOR:.2f}",
                    "blocking": True})

    substantial = len(str(answer).strip()) > 0
    results.append({"name": "answer is not empty", "passed": substantial,
                    "detail": f"{len(str(answer).strip())} characters",
                    "blocking": True})
    return results


# ------------------------------------------------------------------- run
@dataclass
class Trace:
    headline: str
    branch: str = ""
    why_branch: str = ""
    passages: list = field(default_factory=list)
    raw_answer: str = ""
    confidence: float = 0.0
    guardrails: list = field(default_factory=list)
    blocked: bool = False
    final: str = ""
    mode: str = "demo"
    ms: int = 0

SAFE = "I am not able to answer that one."
BLOCKED = "BLOCKED"   # how a blocked answer is counted when scoring

def classify(headline):
    t0 = time.time()
    tr = Trace(headline=str(headline))
    tr.mode = "live" if live_mode() else "demo"

    if not str(headline).strip():
        tr.branch, tr.why_branch = "refuse", "the input was empty"
        tr.final = "Please paste a news headline first."
        tr.guardrails = check(tr.final, 1.0, "refuse")
        tr.ms = int((time.time() - t0) * 1000)
        _save(tr)
        return tr

    tr.branch, tr.why_branch = route(headline)
    tr.passages = retrieve(headline)

    if tr.branch == "refuse":
        tr.final = "I cannot do that. I only sort news items into categories."
        tr.confidence = 1.0
    elif tr.branch == "explain":
        if tr.passages:
            tr.final = ("Here is the rule I follow. "
                        + tr.passages[0]["text"][:220])
        else:
            tr.final = "I do not have a note covering that."
        tr.confidence = 1.0
    else:
        if tr.mode == "live":
            cat, conf = _groq_classify(headline, config.SYSTEM_PROMPT, tr.passages)
        else:
            cat, conf = _demo_classify(headline)
        tr.final, tr.confidence = cat, conf

    tr.raw_answer = tr.final
    tr.guardrails = check(tr.final, tr.confidence, tr.branch)
    failed = [g for g in tr.guardrails if g["blocking"] and not g["passed"]]
    if failed:
        tr.blocked = True
        tr.final = SAFE
    tr.ms = int((time.time() - t0) * 1000)
    _save(tr)
    return tr

def _save(tr):
    try:
        store.save_run(tr)
    except Exception:
        pass   # a broken database must never stop an answer


# ---------------------------------------------------------------- scoring
def score(golden):
    """golden: list of {'text':..., 'label':...}. Returns per-item and totals."""
    from sklearn.metrics import cohen_kappa_score
    rows, preds, truth = [], [], []
    for g in golden:
        for attempt in range(4):
            try:
                tr = classify(g["text"])
                break
            except RateLimited as e:
                if attempt == 3:
                    raise
                time.sleep(e.retry_after or 5)
        # A blocked answer is its own label, so it counts against accuracy and
        # kappa alike. No labels= list: every item stays in kappa, whatever it got.
        got = BLOCKED if tr.blocked else tr.final
        rows.append({"text": g["text"][:90], "expected": g["label"],
                     "official": g.get("official", ""), "got": got, "ok": got == g["label"],
                     "branch": tr.branch, "confidence": tr.confidence})
        preds.append(got)
        truth.append(g["label"])
    correct = sum(r["ok"] for r in rows)
    k = cohen_kappa_score(truth, preds) if len(set(truth)) > 1 else 0.0
    return {"rows": rows, "correct": correct, "total": len(rows),
            "accuracy": round(correct / len(rows), 4) if rows else 0.0,
            "kappa": round(float(k), 4),
            "blocked": sum(p == BLOCKED for p in preds)}
