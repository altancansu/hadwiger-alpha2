---
id: verifier-O-canary
created: 2026-07-21
resolves_phase: 2
source: phase-1 code-review WR-01
severity: warning
---

# Verifier trust-root degrades under `python -O`

`src/alpha2/verify/model.py::verify_model` is entirely `assert`-based (verbatim from Appendix C).
Under `python -O` / `PYTHONOPTIMIZE=1`, all asserts are stripped and the verifier silently
becomes `return True` — defeating the project's core epistemic-integrity invariant
("nothing counts as found until the independent verifier passes").

**Phase 2 (trust-root-corpus-schema / verifier hardening) must:**
- Convert the verifier to raise explicit exceptions (not `assert`), OR
- Add an `-O` canary at import/entry that hard-fails if `__debug__` is False, so the
  verifier can never run in optimized mode.
- Add a regression test asserting the verifier rejects a mutated/invalid model even under `-O`.

Ref: 01-REVIEW.md WR-01 / WR-02; 01-RESEARCH.md § Security Domain (deferred-to-Phase-2 row).
