| v | What changed | Correct /30 | Accuracy | Kappa | Blocked |
|---|---|---|---|---|---|
| v0 | supplied prompt, floor 0.00, pacing added, scoring on my labels | 5/30 | 0.1667 | 0.1156 | 24 |
| v0-demo | demo stand-in, no API key. Wiring check only, not a model score | 18/30 | 0.6000 | 0.4322 | 0 |
| v1 | token budget: reasoning_effort low, max_tokens 200 (two settings, one fix) | 21/30 | 0.7000 | 0.6029 | 1 |
