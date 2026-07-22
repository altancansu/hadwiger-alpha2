"""The G1-G6 gate (GATE-01/GATE-02): step 1 of the 7-step kill-battery runbook.

Definitions are FROZEN verbatim from the author's Appendix E §2
(`.planning/reference/alpha2-program-source.md`) — never invented or paraphrased.

Kill-semantics are D-01 Role B (LOCKED): the ONLY checks that may KILL are the minimal
hard-gate {G1 even-n criticality `nu == n//2`, G2 triangle-free/diameter-2, connectivity}.
G3-deep (kappa, delta), G4 (omega window), G5, G6 run FLAG-ONLY for studied pools — they
record regime + reason + witness onto the result but never terminate the runbook. seed-137
PASSES the hard-gate; its G3/G4 failures are flags, not kills.
"""
