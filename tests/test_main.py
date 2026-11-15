"""Tests for QuantumTunnel-X: every number checked against analytics."""
import math

import pytest

import main as m


# ---- rectangular barrier (exact closed form)
def test_kappa_electron_1ev():
    assert abs(m.kappa_per_nm(1.0) - 5.1232) < 0.01


def test_zero_width_transmits_all():
    assert m.transmission_rect(0.5, 2.0, 0.0) == 1.0


def test_below_barrier_value():
    t = m.transmission_rect(1.0, 2.0, 1.0)
    assert abs(t - 1.420e-4) < 0.05 * 1.420e-4


def test_width_monotone_below_barrier():
    assert (m.transmission_rect(1.0, 2.0, 2.0)
            < m.transmission_rect(1.0, 2.0, 1.0)
            < m.transmission_rect(1.0, 2.0, 0.5))


def test_at_top_limit_formula():
    expect = 1.0 / (1.0 + m.M_E * 2.0 * m.EV_J * 1e-18 / (2.0 * m.HBAR ** 2))
    assert abs(m.transmission_rect(2.0, 2.0, 1.0) - expect) < 1e-12


def test_above_barrier_resonance_is_one():
    # k2 a = pi with a = 1 nm -> the barrier is invisible
    k2 = math.pi
    e_above = (k2 * 1e9 * m.HBAR) ** 2 / (2.0 * m.M_E) / m.EV_J
    assert abs(m.transmission_rect(2.0 + e_above, 2.0, 1.0) - 1.0) < 1e-9


def test_heavy_mass_tunnels_less():
    assert (m.transmission_rect(1.0, 2.0, 1.0, m.M_ALPHA)
            < m.transmission_rect(1.0, 2.0, 1.0, m.M_E))


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        m.transmission_rect(0.0, 2.0, 1.0)
    with pytest.raises(ValueError):
        m.kappa_per_nm(-1.0)


# ---- WKB vs exact
def test_wkb_none_above_barrier():
    assert m.transmission_wkb(3.0, 2.0, 1.0) is None


def test_wkb_prefactor_at_half_height():
    ratio = m.transmission_rect(1.0, 2.0, 3.0) / m.transmission_wkb(1.0, 2.0, 3.0)
    assert abs(ratio - 4.0) < 0.1  # 16 E (V0-E) / V0^2 at E = V0/2


def test_wkb_overestimates_near_top():
    ratio = m.transmission_wkb(1.98, 2.0, 1.0) / m.transmission_rect(1.98, 2.0, 1.0)
    assert ratio > 3.0


def test_wkb_table_rows():
    rows = m.wkb_error_table()
    assert len(rows) == 6
    assert abs(rows[2]["ratio_exact_over_wkb"] - 4.0) < 0.15


# ---- transfer matrix vs analytic
def test_tm_matches_rect_below():
    tm = m.transmission_layers(1.0, [(2.0, 1.0)])
    assert abs(tm - m.transmission_rect(1.0, 2.0, 1.0)) < 1e-9


def test_tm_matches_rect_above():
    tm = m.transmission_layers(3.0, [(2.0, 0.7)])
    assert abs(tm - m.transmission_rect(3.0, 2.0, 0.7)) < 1e-9


# ---- wave packet
def test_packet_narrow_recovers_exact():
    t = m.packet_transmission(1.0, 0.01, 2.0, 1.0)
    assert abs(t - m.transmission_rect(1.0, 2.0, 1.0)) < 0.05 * m.transmission_rect(1.0, 2.0, 1.0)


def test_packet_spread_helps_below_barrier():
    assert (m.packet_transmission(1.0, 0.3, 2.0, 1.0)
            > m.transmission_rect(1.0, 2.0, 1.0))


# ---- alpha decay (Gamow)
def test_alpha_u238_billennia():
    r = m.alpha_half_life(*m.ALPHA_MODELS["U-238-like"])
    assert 1.0e9 < r["half_life_years"] < 2.0e10


def test_alpha_po212_microseconds():
    r = m.alpha_half_life(*m.ALPHA_MODELS["Po-212-like"])
    assert 1.0e-8 < r["half_life_s"] < 1.0e-5


def test_alpha_gamow_ordering():
    u = m.alpha_half_life(*m.ALPHA_MODELS["U-238-like"])
    po = m.alpha_half_life(*m.ALPHA_MODELS["Po-212-like"])
    assert u["gamow_g"] > po["gamow_g"] > 0


def test_geiger_nuttall_monotone():
    s = m.geiger_nuttall_series()
    assert all(s[i]["log10_half_life_s"] > s[i + 1]["log10_half_life_s"]
               for i in range(len(s) - 1))


def test_geiger_nuttall_straight_line():
    fit = m.geiger_nuttall_fit()
    assert fit["r"] > 0.999 and fit["slope"] > 0


def test_one_mev_five_orders():
    q1 = m.alpha_half_life(86, 222, 5.0)["half_life_s"]
    q2 = m.alpha_half_life(86, 222, 6.0)["half_life_s"]
    assert q1 / q2 > 1.0e5


# ---- STM
def test_stm_kappa():
    assert abs(m.stm_kappa() - 11.458) < 0.05


def test_stm_factor_per_angstrom():
    assert abs(m.stm_factor_per_angstrom() - 9.90) < 0.35


def test_stm_current_ratio_exact():
    ratio = m.stm_current(0.5) / m.stm_current(1.5)
    expect = math.exp(2.0 * m.stm_kappa() * 1.0)
    assert abs(ratio / expect - 1.0) < 1e-9


def test_stm_resolution_sub_pm():
    assert 0.2 < m.stm_vertical_resolution_pm() < 1.0


# ---- tunnel diode toy model
def test_diode_tunnel_peak_at_vp():
    assert abs(m.diode_tunnel_current(m.DIODE_VP_V) - m.DIODE_IP_MA) < 1e-12


def test_diode_ndr_slope_signs():
    assert m.diode_slope(0.30) < 0     # inside the NDR region
    assert m.diode_slope(0.05) > 0     # rising toward the peak


def test_diode_peak_valley():
    pv = m.diode_peak_valley()
    assert abs(pv["peak_v"] - m.DIODE_VP_V) < 0.02
    assert pv["valley_ma"] < pv["peak_ma"]
    assert pv["peak_valley_ratio"] > 2.0


# ---- resonant tunneling
def test_resonance_peak_near_one():
    scan = m.resonance_scan()
    assert scan["transmission"] > 0.99
    assert 0.0 < scan["energy_ev"] < 1.0


def test_resonance_beats_single_barrier():
    scan = m.resonance_scan()
    single = m.transmission_rect(scan["energy_ev"], 1.0, 2.0)
    assert scan["transmission"] / single > 100.0


def test_off_resonance_suppressed():
    scan = m.resonance_scan()
    off = m.transmission_double_barrier(min(scan["energy_ev"] + 0.25, 0.98))
    assert off < 0.05


# ---- Fowler-Nordheim
def test_fn_slope_identity():
    j1 = m.fn_current_density(3.0e9)
    j2 = m.fn_current_density(5.0e9)
    slope = (math.log(j2 / 5.0e9 ** 2) - math.log(j1 / 3.0e9 ** 2)) / (1.0 / 5.0e9 - 1.0 / 3.0e9)
    assert abs(slope - m.fn_slope()) < 1e-6 * abs(m.fn_slope())


def test_fn_monotone_and_phi():
    assert m.fn_current_density(6.0e9) > m.fn_current_density(5.0e9) > 0.0
    assert m.fn_current_density(5.0e9, 5.5) < m.fn_current_density(5.0e9, 4.5)


# ---- classifier
def test_classifier_regimes():
    rep = m.regime_report()
    assert rep["electron_half_height_1nm"] == "tunneling-dominant"
    assert rep["electron_above_barrier"] == "classical-over-barrier"
    assert rep["alpha_below_coulomb_top"] == "tunneling-dominant"
    assert rep["alpha_above_barrier"] == "classical-over-barrier"
    assert rep["electron_near_top"] == "mixed"


# ---- gates, seats, checks suite
def test_hold_gates_14():
    assert len(m.HOLD_GATES) == 14
    assert all(v.startswith("HOLD") for v in m.HOLD_GATES.values())


def test_gates():
    assert m.gate("teleportation_claim") == "HOLD"
    assert m.gate("claim_ftl") == "HOLD"
    assert m.gate("radiation_source_live") == "HOLD"
    assert m.gate("run_simulation") == "PROCEED"


def test_seats_never_override():
    b = m.brains_report()
    assert b["decider"]["can_override_hold"] is False
    assert b["advisor"]["can_override_hold"] is False
    assert b["flow"]["rendered"] is False and b["flow"]["live"] == 0
    assert len(b["decider"]["trace_sha256_16"]) == 16


def test_run_checks_all_pass():
    checks = m.run_checks()
    assert all(ok for _, ok in checks)
    assert len(checks) == 50


def test_main_demo_exit_zero(capsys):
    assert m.main([]) == 0
    out = capsys.readouterr().out
    assert "CHECKS 50/50" in out
    assert "VERDICT PROCEED" in out


def test_hold_demo_exit_codes():
    assert m.main(["hold-demo", "teleportation_claim"]) == 2
    assert m.main(["hold-demo", "run_simulation"]) == 0
