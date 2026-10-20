"""The web page. It only talks to the backend over HTTP, at BACKEND_URL.
It reads no model and no database: every number on screen comes from one of
the four backend endpoints. Run it from the frontend folder:

    python app.py
"""
import os, pathlib, functools

import pandas as pd
import requests
import gradio as gr

HERE = pathlib.Path(__file__).resolve().parent

# The default is for local use only. A deployed page must set BACKEND_URL.
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

CLASSIFY_TIMEOUT = 60
QUICK_TIMEOUT = 30
SCORE_TIMEOUT = 600    # live scoring is paced to the free tier and takes minutes

PAGE_ERROR = "Something went wrong in this page. Try again, and check the Health tab."


# ------------------------------------------------------------ talking to the backend
def call(method, path, timeout, **kwargs):
    """Returns (data, None) on success or (None, readable message) on any failure."""
    try:
        r = requests.request(method, BACKEND_URL + path, timeout=timeout, **kwargs)
    except requests.ConnectionError:
        return None, (f"Cannot reach the backend at {BACKEND_URL}. It may be stopped or "
                      "still starting. Start it, or check BACKEND_URL, then try again.")
    except requests.Timeout:
        return None, (f"The backend did not answer within {timeout} seconds. "
                      "It may be waking up or busy. Try again in a moment.")
    except requests.RequestException:
        return None, "The request to the backend failed. Try again in a moment."
    try:
        body = r.json()
    except ValueError:
        body = None
    if r.status_code >= 400:
        detail = body.get("detail") if isinstance(body, dict) else None
        if isinstance(detail, str) and detail:
            return None, detail
        if r.status_code == 404:
            return None, "The backend is running but does not have that page. Check BACKEND_URL."
        return None, f"The backend returned an error (HTTP {r.status_code})."
    if body is None:
        return None, "The backend sent a reply this page could not read."
    return body, None


def guarded(on_error):
    """Whatever goes wrong inside a handler, show a sentence and not a stack trace."""
    def wrap(fn):
        @functools.wraps(fn)
        def inner(*args):
            try:
                return fn(*args)
            except Exception:
                return on_error(PAGE_ERROR)
        return inner
    return wrap


def _golden():
    """The thirty main items scored against my Week 1 hand labels, with the
    official label kept alongside so both can be reported."""
    p, mine = HERE / "week1_data.csv", HERE / "data" / "my_labels.csv"
    if not p.exists() or not mine.exists():
        return []
    df = pd.read_csv(p)
    m = df[df["set"] == "main"].merge(pd.read_csv(mine), on="id", how="inner")
    return [{"text": r.text, "label": r.my_label, "official": r.official_label}
            for r in m.itertuples()]


# ------------------------------------------------------------------ page 1
@guarded(lambda msg: (f"**{msg}**", ""))
def do_classify(headline):
    d, err = call("POST", "/classify", CLASSIFY_TIMEOUT, json={"headline": headline or ""})
    if err:
        return f"## Could not classify\n\n{err}", ""
    if d["blocked"]:
        verdict = f"## Blocked\n\n{d['category']}"
    else:
        verdict = f"## {d['category']}\n\nConfidence {d['confidence']:.2f}"
    trace = [
        f"**Branch**  `{d['branch']}` because {d['why_branch']}",
        f"**Mode**  {d['mode']}" + ("  (no API key, using the stand-in)" if d["mode"] == "demo" else ""),
        f"**Time**  {d['ms']} ms",
        "",
        "**Passages retrieved**",
    ]
    if d["passages"]:
        for p in d["passages"]:
            trace.append(f"- `{p['file']}` / {p['heading']}  (score {p['score']})")
    else:
        trace.append("- none scored above the threshold")
    trace += ["", "**Guardrails**"]
    for g in d["guardrails"]:
        trace.append(f"- {'PASS' if g['passed'] else 'FAIL'}  {g['name']} - {g['detail']}")
    return verdict, "\n".join(trace)


# ------------------------------------------------------------------ page 2
@guarded(lambda msg: (f"**{msg}**", None))
def do_score():
    golden = _golden()
    if len(golden) != 30:
        return (f"Expected 30 labelled items from week1_data.csv and data/my_labels.csv, "
                f"found {len(golden)}."), None
    payload = [{"text": g["text"], "label": g["label"]} for g in golden]
    s, err = call("POST", "/score", SCORE_TIMEOUT, json={"golden": payload})
    if err:
        return f"## Could not run the scoring\n\n{err}", None
    h, _ = call("GET", "/health", QUICK_TIMEOUT)
    mode = {"live": "live model", "demo": "demo stand-in, the prompt is ignored"}.get(
        (h or {}).get("mode"), "unknown")
    head = (f"## {s['correct']} / {s['total']} correct\n\n"
            f"Accuracy **{s['accuracy']*100:.1f}%**  ·  Cohen's kappa **{s['kappa']}**"
            f"  ·  Blocked **{s.get('blocked', 0)}**\n\n"
            f"Mode: {mode}")
    rows = s["rows"]
    # the backend only knows the label it was sent, so pair the official label by position
    for row, g in zip(rows, golden):
        row["official"] = g["official"]
    df = pd.DataFrame(rows)[["text", "expected", "official", "got", "ok", "confidence"]]
    return head, df


# ------------------------------------------------------------------ page 3
@guarded(lambda msg: (f"**{msg}**", pd.DataFrame()))
def do_runs():
    d, err = call("GET", "/runs", QUICK_TIMEOUT, params={"limit": 50})
    if err:
        return f"**Could not load past runs.** {err}", pd.DataFrame()
    if not d["runs"]:
        return "Nothing yet. Classify something first.", pd.DataFrame()
    return f"Showing the last {len(d['runs'])} runs.", pd.DataFrame(d["runs"])


# ------------------------------------------------------------------ page 4
@guarded(lambda msg: f"**{msg}**")
def do_health():
    lines = ["## This page", "", f"- **Backend address**  `{BACKEND_URL}`", ""]
    d, err = call("GET", "/health", QUICK_TIMEOUT)
    if err:
        return "\n".join(lines + ["## Backend", "", f"**Not reachable.** {err}"])
    db = d.get("database", {})
    if db.get("status") == "ok":
        db_line = f"working, {db.get('rows', '?')} rows stored"
    else:
        db_line = "DOWN. Answers still work, but runs cannot be saved or shown."
    lines += [
        "## What is switched on in the backend", "",
        f"- **Mode**  {d['mode']}",
        f"- **Model key**  {'present, using the real model' if d['key_present'] else 'NOT SET, using the demo stand-in'}",
        f"- **Model**  `{d['model']}`",
        f"- **Database**  {db_line}",
        f"- **Knowledge files loaded**  {d['knowledge'] if d['knowledge'] else 'none'}",
    ]
    if d.get("missing"):
        lines.append(f"- **Listed but not found**  {d['missing']}  ← check the file name in config.py")
    lines += [
        f"- **Passages shown to the model**  {d['passages_shown']}",
        f"- **Relevance threshold**  {d['relevance_threshold']}",
        f"- **Confidence floor**  {d['confidence_floor']}",
        f"- **Reasoning effort**  {d['reasoning_effort']}, up to {d['max_tokens']} reply tokens",
        f"- **Routing rules**  {d['routing_rules']}",
        f"- **Banned phrases**  {d['banned_phrases']}",
    ]
    return "\n".join(lines)


def build():
    with gr.Blocks(title="Newsroom Triage") as demo:
        gr.Markdown("# Newsroom Triage\nPaste a news headline. It tells you which "
                    "of four categories it belongs to, and shows you exactly how it decided.")
        with gr.Tab("Classify"):
            inp = gr.Textbox(label="News headline", lines=3,
                             placeholder="Paste a headline here")
            btn = gr.Button("Classify", variant="primary")
            out = gr.Markdown()
            tr = gr.Markdown()
            btn.click(do_classify, inp, [out, tr])
        with gr.Tab("Scoring"):
            gr.Markdown("Runs your thirty labelled items from Week 1 and scores itself. "
                        "With a real key this takes a few minutes, because it waits to stay "
                        "inside the free tier limits.")
            sbtn = gr.Button("Run the scoring", variant="primary")
            shead = gr.Markdown()
            stab = gr.Dataframe(wrap=True)
            sbtn.click(do_score, None, [shead, stab])
        with gr.Tab("Runs"):
            gr.Markdown("Every question this app has been asked.")
            rbtn = gr.Button("Refresh")
            rstat = gr.Markdown()
            rtab = gr.Dataframe(wrap=True)
            rbtn.click(do_runs, None, [rstat, rtab])
        with gr.Tab("Health"):
            hbtn = gr.Button("Check")
            hout = gr.Markdown()
            hbtn.click(do_health, None, hout)
    return demo


if __name__ == "__main__":
    build().launch(server_name="0.0.0.0",
                   server_port=int(os.environ.get("PORT", 7860)),
                   share=False)
