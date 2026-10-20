# Warm latency of the deployed backend

Measured on 20 October 2026 from my laptop against the deployed backend (`https://newsroom-triage-backend.onrender.com`). 20 `POST /classify` requests, one at a time, 4 seconds apart, using the first 20 of my 30 main headlines. Each request opened a new connection, so the total includes the connection set-up. A warm-up `GET /health` was sent first and took 206 ms (status 200), so the service was already awake and no request below includes a cold start.

| n | Item id | Status | Total (ms) | `ms` field (ms) | Difference (ms) | Category | Confidence |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 200 | 595 | 436 | 159 | Sports | 0.95 |
| 2 | 2 | 200 | 859 | 696 | 163 | World | 0.95 |
| 3 | 3 | 200 | 452 | 315 | 137 | Sports | 0.95 |
| 4 | 4 | 200 | 732 | 581 | 151 | Sports | 0.99 |
| 5 | 5 | 200 | 778 | 587 | 191 | Sports | 0.95 |
| 6 | 6 | 200 | 527 | 359 | 168 | Sci/Tech | 0.95 |
| 7 | 7 | 200 | 494 | 356 | 138 | World | 0.95 |
| 8 | 8 | 200 | 819 | 623 | 196 | Business | 0.95 |
| 9 | 9 | 200 | 873 | 713 | 160 | Business | 0.92 |
| 10 | 10 | 200 | 910 | 738 | 172 | Sci/Tech | 0.95 |
| 11 | 11 | 200 | 1212 | 1043 | 169 | Sports | 0.95 |
| 12 | 12 | 200 | 791 | 679 | 112 | World | 0.95 |
| 13 | 13 | 200 | 608 | 498 | 110 | Sports | 0.95 |
| 14 | 14 | 200 | 528 | 368 | 160 | Sci/Tech | 0.95 |
| 15 | 15 | 200 | 635 | 500 | 135 | Sci/Tech | 0.95 |
| 16 | 16 | 200 | 865 | 706 | 159 | World | 0.95 |
| 17 | 17 | 200 | 1183 | 1048 | 135 | World | 0.95 |
| 18 | 18 | 200 | 877 | 751 | 126 | Business | 0.92 |
| 19 | 19 | 200 | 695 | 588 | 107 | Business | 0.95 |
| 20 | 20 | 200 | 789 | 663 | 126 | World | 0.95 |

All 20 of 20 requests returned HTTP 200 and none was blocked.

| Measure (ms) | Total as I see it | `ms` field | Difference |
|---|---|---|---|
| Median | 783.5 | 605.5 | 155.0 |
| Worst | 1212 | 1048 | 196 |
| Fastest | 452 | 315 | 107 |
| Average | 761 | 612 | 149 |

## What `ms` measures
The backend starts a clock when `engine.classify` begins and reads it just before it saves the run. So `ms` covers the routing check, the retrieval of notes, the call to Groq with its wait for the reply, and the guardrail checks. It is taken before the database save, so it leaves out the save.

## What the total includes that `ms` does not
- The trip from my laptop to Render and back: DNS, the connection and the TLS handshake, because each request opened a new connection.
- Render's proxy and FastAPI reading the request and building the reply.
- The database save to Neon, which happens after `ms` is read and before the reply is sent. The save makes one connection attempt with a 4 second limit.

The difference, between 107 and 196 ms here, is those three together. I cannot split them from the outside, so I do not know how much of it is the database save.

## Caveats
- 20 requests from one place at one time of day. The Groq call is most of the time and it varies with Groq's load.
- This is warm latency only. The cold start after an idle spell is in `results/cold_start_deployed.md`.
