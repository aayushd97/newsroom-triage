| v | What changed | Correct /30 | Accuracy | Kappa | Blocked |
|---|---|---|---|---|---|
| v0 | supplied prompt, floor 0.00, pacing added, scoring on my labels | 5/30 | 0.1667 | 0.1156 | 24 |
| v0-demo | demo stand-in, no API key. Wiring check only, not a model score | 18/30 | 0.6000 | 0.4322 | 0 |
| v1 | token budget: reasoning_effort low, max_tokens 200 (two settings, one fix) | 21/30 | 0.7000 | 0.6029 | 1 |
| v2 | SYSTEM_PROMPT rewritten from my Week 1 rules; low-confidence line set at 0.6 (Claude Code's number, not mine). Retrieval notes unchanged. Second run gave 26/30, 0.8667, kappa 0.8193, 0 blocked, identical answers. | 26/30 | 0.8667 | 0.8193 | 0 |
| v3 | CONFIDENCE_FLOOR 0.6, taken from the prompt's definition of low confidence, not tuned on the 30 items. Floor blocked nothing on the 30. | 26/30 | 0.8667 | 0.8198 | 0 |
| v4 | RETRIEVAL_METHOD bm25, BM25_THRESHOLD 0.7, k1 1.5, b 0.75. Prompt and floor unchanged. | 26/30 | 0.8667 | 0.8193 | 0 |
