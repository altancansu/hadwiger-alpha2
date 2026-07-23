# Deferred Items — Phase 07 (p0-cdm-frontier)

Out-of-scope test failures discovered during 07-03 execution (scope: schema/verifier/store only).
These are executable RED contracts for later plans, NOT regressions:

| Test module | Missing module | Owning plan |
|-------------|----------------|-------------|
| tests/pool/cdm/test_generation_counts.py | alpha2.pool.cdm.generate (stream_mtf) | 07-04 |
| tests/pool/cdm/test_generation_crosscheck.py | alpha2.pool.cdm.generate (stream_mtf) | 07-04 |
| tests/pool/cdm/test_disconnected_complement.py | alpha2.pool.cdm.adjudicate (classify_cdm_fail) | 07-05 |

Go GREEN as those modules land. No action for 07-03.
