"""
==============================================================================

  THIS IS THE ONLY FILE YOU NEED TO CHANGE.

  Everything below is written in plain English. You are allowed to change
  any of it. You are not expected to understand the rest of the project.

  There are four things here:

     1. SYSTEM_PROMPT    what the assistant is told to do
     2. ROUTING_RULES    which kind of question goes down which branch
     3. GUARDRAILS       what the assistant must refuse to do
     4. SETTINGS         a few numbers you can turn up and down

  After you change something, run the app again and look at the Scoring
  page. If the number went up, your change helped. If it went down, it
  did not. That is the whole job.

==============================================================================
"""

# -----------------------------------------------------------------------------
#  1. SYSTEM_PROMPT
#     The instructions the assistant follows. This one is deliberately poor.
#     Improving it is your main task.
# -----------------------------------------------------------------------------

SYSTEM_PROMPT = """
Sort a news item into exactly one category: World, Sports, Business or Sci/Tech.

World: mainly about governments, politicians, armies, diplomacy or disasters, in any country. If politics is the reason behind the story, choose World even when it affects another field.
Sports: mainly about a game, player, team or competition, including transfers and injuries. It must be about the sport itself, not its finances or politics.
Business: mainly about the money side of any company: profits, share prices, takeovers, sales, job cuts, prices.
Sci/Tech: mainly about a discovery, a study, a gadget, software or a space mission, and what it does or how it works.

If two categories fit, ask which newspaper section the story would sit in and choose that one. If you still cannot decide, choose the closest fit and give a low confidence, below 0.6. Give a high confidence only when one category clearly fits.
"""


# -----------------------------------------------------------------------------
#  2. ROUTING_RULES
#     Before the model is asked anything, the app checks this list.
#     If a phrase on the left appears in the question, it goes down that branch.
#     Branches are: "classify", "explain", "refuse".
#     Rules are checked from the top down. The first match wins.
# -----------------------------------------------------------------------------

ROUTING_RULES = [
    ("why did you",        "explain"),
    ("explain",            "explain"),
    ("how confident",      "explain"),
    ("ignore your",        "refuse"),
    ("your instructions",  "refuse"),
]


# -----------------------------------------------------------------------------
#  3. GUARDRAILS
#     Checked AFTER the model answers. If any of these fail, the answer is
#     replaced with a safe message instead of being shown.
# -----------------------------------------------------------------------------

# The assistant must never claim to be a person.
BANNED_PHRASES = [
    "as a human",
    "i am a person",
]

# The assistant must only ever answer with one of these four words.
ALLOWED_CATEGORIES = ["World", "Sports", "Business", "Sci/Tech"]

# If the model is less sure than this, the app says it does not know
# instead of guessing. 0.0 means never refuse. 1.0 means always refuse.
# 0.6 matches the prompt's own definition of low confidence. It was not tuned
# on the 30 items. In v2 no answer fell below 0.85, so at this floor nothing
# is blocked yet and it only acts as a safety net for inputs that are not news.
CONFIDENCE_FLOOR = 0.6


# -----------------------------------------------------------------------------
#  4. SETTINGS
# -----------------------------------------------------------------------------

# Which documents in the knowledge folder the app may read from.
# Add a file to app/knowledge/ and add its name here to switch it on.
KNOWLEDGE_FILES = [
    "categories.md",
]

# How many pieces of a document the app is allowed to show the model.
KNOWLEDGE_PASSAGES = 2

# How sure a keyword match has to be before a passage counts as relevant.
KNOWLEDGE_THRESHOLD = 0.10

# How the app finds the passages to show the model.
#   "overlap"  counts the words the question shares with a passage. This is the
#              original method. It only knows words, not which words matter.
#   "bm25"     a standard search score. Rare words count for more than common
#              ones, and repeating a word helps less each time.
# Switch between them to compare. Both use the same passages and the same words.
RETRIEVAL_METHOD = "overlap"

MODEL = "openai/gpt-oss-120b"
TEMPERATURE = 0

# This model thinks before it answers, and the thinking counts against the
# reply limit. If the limit is too small the thinking uses it all and the
# answer comes back empty. "low" thinks briefly. MAX_TOKENS is a ceiling, not
# a charge: you only pay for the tokens actually used.
REASONING_EFFORT = "low"
MAX_TOKENS = 200

# Groq free tier limits for this model, per minute. The app waits rather than
# going over them. A 429 from Groq means slow down, not a bad key.
REQUESTS_PER_MINUTE = 30
TOKENS_PER_MINUTE = 8000
