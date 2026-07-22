"""DEFAULT_CHAIN structure + D-01 Role B tiers (LOCKED).

hard set = {g1_criticality, g2_triangle_free_diam2, g_connectivity}; everything deeper
(g3_deep, g4_omega_window, g5, g6) is flag_only. The chain is cost-ordered: the cheap
criticality/connectivity checks precede the expensive kappa/omega deep checks.
"""
from alpha2.gate.runner import default_chain


def test_default_chain_tiers_match_role_b():
    tiers = {name: tier for name, tier, _ in default_chain()}
    assert tiers["g1_criticality"] == "hard"
    assert tiers["g2_triangle_free_diam2"] == "hard"
    assert tiers["g_connectivity"] == "hard"
    assert tiers["g3_deep"] == "flag_only"
    assert tiers["g4_omega_window"] == "flag_only"
    assert tiers["g5_unavoidables"] == "flag_only"
    assert tiers["g6_safe_families"] == "flag_only"


def test_hard_set_is_exactly_three():
    hard = [name for name, tier, _ in default_chain() if tier == "hard"]
    assert set(hard) == {"g1_criticality", "g2_triangle_free_diam2", "g_connectivity"}


def test_chain_is_cost_ordered():
    names = [name for name, _, _ in default_chain()]
    # cheap criticality/connectivity precede the expensive kappa/omega deep checks
    assert names.index("g1_criticality") < names.index("g3_deep")
    assert names.index("g_connectivity") < names.index("g4_omega_window")
    assert names[0] == "g1_criticality"


def test_every_check_is_callable():
    for name, tier, fn in default_chain():
        assert callable(fn), name
        assert tier in ("hard", "flag_only"), (name, tier)
