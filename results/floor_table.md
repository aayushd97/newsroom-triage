# Confidence floor table (offline, from the two saved v2 runs)

Rule used by the app: an answer is blocked when confidence is below the floor. A blocked answer counts as wrong and is its own label, BLOCKED, in kappa. Scored against my_label. No API calls were made to build this table.

| Floor | Run | Correct /30 | Accuracy | Kappa | Blocked | Blocked and right | Blocked and wrong |
|---|---|---|---|---|---|---|---|
| 0.5 | 1 | 26 | 0.8667 | 0.8193 | 0 | 0 | 0 |
| 0.5 | 2 | 26 | 0.8667 | 0.8193 | 0 | 0 | 0 |
| 0.6 | 1 | 26 | 0.8667 | 0.8193 | 0 | 0 | 0 |
| 0.6 | 2 | 26 | 0.8667 | 0.8193 | 0 | 0 | 0 |
| 0.8 | 1 | 26 | 0.8667 | 0.8193 | 0 | 0 | 0 |
| 0.8 | 2 | 26 | 0.8667 | 0.8193 | 0 | 0 | 0 |
| 0.9 | 1 | 26 | 0.8667 | 0.8193 | 0 | 0 | 0 |
| 0.9 | 2 | 26 | 0.8667 | 0.8209 | 1 | 0 | 1 |
| 0.93 | 1 | 26 | 0.8667 | 0.8230 | 3 | 0 | 3 |
| 0.93 | 2 | 24 | 0.8000 | 0.7368 | 4 | 2 | 2 |
| 0.95 | 1 | 26 | 0.8667 | 0.8230 | 3 | 0 | 3 |
| 0.95 | 2 | 24 | 0.8000 | 0.7368 | 4 | 2 | 2 |
| 0.96 | 1 | 1 | 0.0333 | 0.0247 | 29 | 25 | 4 |
| 0.96 | 2 | 2 | 0.0667 | 0.0498 | 28 | 24 | 4 |

Run 1 and run 2 are the same prompt and settings. They differ only because confidence numbers vary slightly between calls. The answers were identical.

Confidence values seen: run 1 [np.float64(0.92), np.float64(0.95), np.float64(0.99)], run 2 [np.float64(0.85), np.float64(0.92), np.float64(0.95), np.float64(0.96), np.float64(0.99)].
