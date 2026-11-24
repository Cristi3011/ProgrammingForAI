# Evaluation protocol

**Question:** Which of `chronological`, `popularity`, `for_you`, and `learned` puts a user's later likes in its top 10?

**Cut-off and snapshot:** We use the 80th percentile of like timestamps, or `--cutoff`, and copy the SQLite database. The copy removes likes and posts at or after the cut-off.

**Users:** We evaluate users with at least 3 likes before the cut-off and at least 1 later like on a post still in the snapshot.

**Candidates:** The existing `FeedService.get_feed` result provides each strategy's candidates and ranking. `popularity` is an evaluation-only ranking inside the script.

**Relevance and metric:** A later like is relevant. NDCG@10 is DCG divided by the ideal DCG of the same relevant posts.

**Intervals and slices:** We report 95% paired bootstrap intervals over users with a fixed seed. Slices are new (`<10` likes), casual (`10-49`), regular (`50-199`), and power (`200+`) before the cut-off.

**Known limitations:** The learned model may have seen evaluation ratings in its training period; this inflation of its score is a limitation and the protocol records the database and cut-off. MovieLens is an older, sparsely timed rating population, unlike a fresh social feed, so winning slices should not be assumed to transfer unchanged.
