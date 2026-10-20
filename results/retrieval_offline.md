# Offline retrieval comparison

No API calls. The 30 headlines of my main set, each run through both methods with the settings in `backend/app/config.py` (overlap threshold 0.1; BM25 threshold 0.7, k1 1.5, b 0.75; at most 2 passages).

| Measure | Overlap | BM25 |
|---|---|---|
| (a) Headlines that get any passage | 30 / 30 | 30 / 30 |
| (b) Top passage heading equals my label | 6 / 30 | 7 / 30 |
| (c) Average passages returned | 2.00 | 1.97 |
| Extra: my label's passage is among those returned | 7 / 30 | 10 / 30 |
| Extra: top passage is a non-category heading (can never match) | 13 / 30 | 17 / 30 |

The two methods return the same top passage for 18 of 30 headlines and the same pair of passages, in the same order, for 10 of 30.

What this measures: whether the passage the search puts first has the same heading as the category I gave the headline. The passages are the four category descriptions plus two general ones (`Category rules` and `When two fit`), so a top passage can only equal my label if it is the description of the right category.

What it does not measure: whether the answer is right. The model is not called here. It does not tell us whether a passage helps the model, whether a wrong passage misleads it, or whether the model would have got the item right anyway. A search that ranks the right category first is the aim, but a high figure here does not promise a higher score on the Scoring page. It is also only 30 headlines, so a difference of one or two is noise.

## Per item

| id | My label | Overlap (top 2) | BM25 (top 2) |
|---|---|---|---|
| 1 | Sports | World 0.981, Sci/Tech 0.853 | World 3.597, When two fit 1.861 |
| 2 | World | Category rules 0.853, Sci/Tech 0.853 | Category rules 3.632, Sci/Tech 2.326 |
| 3 | Sports | Category rules 0.853, Sci/Tech 0.853 | Sports 3.749, Category rules 3.029 |
| 4 | Sports | Sci/Tech 0.853, Business 0.834 | Sports 3.749, Business 1.77 |
| 5 | Sports | Category rules 0.64, Sci/Tech 0.64 | Category rules 2.575, When two fit 2.428 |
| 6 | Sci/Tech | Sports 0.612, World 0.588 | World 2.439, When two fit 2.428 |
| 7 | World | Category rules 0.64, Sci/Tech 0.64 | Category rules 2.575, When two fit 2.428 |
| 8 | Business | When two fit 0.688, Sci/Tech 0.426 | When two fit 4.697, Business 1.081 |
| 9 | Business | Sci/Tech 0.853, Category rules 0.64 | Sci/Tech 2.832, Category rules 2.575 |
| 10 | Sci/Tech | Sci/Tech 0.853, Business 0.834 | Category rules 2.575, Sci/Tech 1.647 |
| 11 | Sports | Category rules 0.64, Sci/Tech 0.64 | When two fit 3.089, Category rules 2.575 |
| 12 | World | World 0.588, Category rules 0.426 | World 2.271, Category rules 1.828 |
| 13 | Sports | Sci/Tech 0.426, Business 0.417 | Sci/Tech 1.065, Business 0.891 |
| 14 | Sci/Tech | Sci/Tech 0.853, Category rules 0.426 | Sci/Tech 3.732, Category rules 1.828 |
| 15 | Sci/Tech | Sci/Tech 0.426, Business 0.417 | Sports 0.727 |
| 16 | World | Sci/Tech 0.64, Business 0.626 | World 3.023, When two fit 2.428 |
| 17 | World | World 0.981, Sci/Tech 0.853 | World 4.864, Business 2.878 |
| 18 | World | When two fit 0.918, Category rules 0.64 | When two fit 5.112, Category rules 3.384 |
| 19 | Business | Sci/Tech 0.64, Sports 0.612 | When two fit 1.609, Sports 1.24 |
| 20 | World | When two fit 0.688, Category rules 0.64 | When two fit 4.697, Category rules 3.908 |
| 21 | World | When two fit 0.229, Sports 0.204 | When two fit 1.609, World 1.004 |
| 22 | Business | Sci/Tech 0.64, When two fit 0.459 | When two fit 2.428, Sci/Tech 2.394 |
| 23 | World | World 0.981, Business 0.834 | World 4.87, When two fit 4.697 |
| 24 | World | Sci/Tech 1.066, Category rules 0.853 | Category rules 3.632, When two fit 2.68 |
| 25 | World | Sci/Tech 0.64, Business 0.626 | When two fit 2.428, Business 1.324 |
| 26 | Sports | Category rules 0.426, Sci/Tech 0.426 | Category rules 2.328, Sci/Tech 1.065 |
| 27 | Sports | Category rules 0.426, When two fit 0.229 | Category rules 1.803, World 1.004 |
| 28 | World | When two fit 0.688, Category rules 0.64 | When two fit 2.97, Category rules 2.257 |
| 29 | Sci/Tech | Business 1.251, Sci/Tech 1.066 | World 4.365, Business 4.362 |
| 30 | Sci/Tech | Category rules 0.853, Business 0.626 | Category rules 4.156, Business 2.242 |
