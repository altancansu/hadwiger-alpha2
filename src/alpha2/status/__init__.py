"""Derived instance statuses (VRF-03): KILLED / SHC-CANDIDATE / RESISTANT.

Status is a READ-ONLY DERIVED VIEW over the immutable, hash-chained corpus + the
append-only JSONL results log — never stored, never mutated state. Transitions (e.g.
RESISTANT -> KILLED once a longer budget kills) are RECOMPUTED from records; they never
edit a stored record. Importing this package pulls in no solver libraries: the view is
pure stdlib + `corpus.manifest` (for the instance-key scheme) + `corpus.schema` shape.
"""
