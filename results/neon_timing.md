# Neon wake-up timing (for C6)

Measured on 20 October 2026 from my laptop, over the pooled endpoint, using the backend's own connect settings (10 second connect timeout, prepared statements off). Nothing touched the database for 7 minutes before the first measurement (the free plan is meant to suspend after about 5 minutes idle). Each measurement is one new connection plus one `SELECT count(*) FROM runs`, which returned 39 rows.

| Measurement | Connect | Query | Total |
|---|---|---|---|
| First, after 7 minutes idle | 885 ms | 61 ms | 946 ms |
| Second, straight after | 118 ms | 35 ms | 153 ms |

The first request cost about 790 ms more than the second. That is the wake-up cost I would report, plus the usual connection time.

How sure I am: this is one measurement, not an average. I could not check from here whether Neon had really suspended the database. A wake-up under one second is faster than I expected, so it may have woken from a lighter idle state, and a longer or colder idle may be slower. The connect timeout is 10 seconds with one retry, so the longest a failed connect can take is about 21 seconds.
