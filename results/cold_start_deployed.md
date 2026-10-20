# Cold start of the deployed services

Measured on 20 October 2026 from my laptop. The last request to the backend ended at 18:50:06 UTC and nothing was sent to either service for 65.0 minutes. The measurements began at 19:55:06 UTC. The waiting script only slept.

| Measurement | Result |
|---|---|
| (a) `GET /health` on the backend, after the idle | **32,528 ms**, HTTP 200, database reported "ok" |
| (b) `POST /classify` on the backend, straight after (a) | **885 ms** total, HTTP 200, the `ms` field said 589 |
| (c) One page load of the frontend | **Not a cold measurement.** Measured later, at 21:18 UTC, once I had the address: 131 ms for the first load and 121 ms for a second straight after (HTTP 200, 27,432 bytes, the page title was present). |

For comparison, the warm median for a classify request was 784 ms (`results/latency_deployed.md`). So the first request after an idle hour cost about 32 seconds, and the request straight after was back to normal.

What (a) includes. Both the backend and the database had gone to sleep, so the 32.5 seconds includes the backend service starting up on Render and the Neon database waking, because `/health` counts the rows. I cannot split the two from the outside. Earlier, a separate test of Neon alone after 7 idle minutes cost about 790 ms more than a warm connection (`results/neon_timing.md`). If Neon took about that long here, nearly all of the 32 seconds was Render starting the service, but that is an inference from a different measurement and not something I measured in this run.

What (b) includes. By then both halves were awake, so (b) is close to a normal warm request. It does not show the cost of a cold start.

What (c) shows. The frontend answered the first request as fast as the second, so it was already awake. I do not know when it was last used before that, and it was not part of the 65 minute idle, because I only got its address afterwards. So there is no frontend cold start figure here. A real one needs the frontend left alone with no one opening it for a long enough idle, which I have not done.

Caveats. This is one measurement, not an average. The 65 minute idle is longer than the five minutes Neon needs to sleep, and I did not check whether Render's free tier sleeps sooner than 65 minutes, so the 32 seconds is the cost after an hour and not the shortest idle that causes it. Anyone who loads the frontend first would also wait for the frontend service to wake, and I could not measure that.
