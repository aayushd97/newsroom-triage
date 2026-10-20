"""Keeps every test off the real key, the real .env and the real database.
Runs before any test file is imported."""
import os, tempfile

os.environ["TRIAGE_NO_DOTENV"] = "1"          # main.py must not read .env
os.environ.pop("GROQ_API_KEY", None)          # tests run in demo mode
os.environ.pop("DATABASE_URL", None)          # no test ever touches Neon
os.environ["TRIAGE_DB"] = os.path.join(tempfile.mkdtemp(), "test_triage.db")
