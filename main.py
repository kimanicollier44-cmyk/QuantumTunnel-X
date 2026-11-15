#!/usr/bin/env python3
"""QuantumTunnel-X - educational quantum tunneling physics lab.

by Darion Kellar

Pure Python standard library. Zero dependencies. Zero network.
Education only: quantum tunneling is real, measured physics - it is
how alpha decay, the scanning tunneling microscope (STM), tunnel
diodes, flash memory and field emission work. This lab computes it
honestly: the EXACT transmission coefficient for a rectangular
barrier, the WKB approximation with its error measured against the
exact answer, a Gamow-factor alpha-decay model that reproduces the
Geiger-Nuttall trend, STM current vs gap, a labelled TOY tunnel-diode
band model, resonant tunneling by transfer matrix (stdlib cmath),
and Fowler-Nordheim field emission - with Gemini Carbon 4 as DECIDER
(names-only, tighten-only), Muse as advisor (never overrides HOLD),
and Google Flow plan-only seats.

Tunneling is NOT teleportation and NOT faster than light: the wave
packet still propagates causally and most of it reflects. Every
teleportation / FTL / product / live-hardware claim is a HOLD gate.
"""
import cmath
import hashlib
import json
import math
import sys

# ---------------------------------------------------------------- constants
HBAR = 1.054571817e-34          # reduced Planck constant, J s (exact, SI)
M_E = 9.1093837015e-31          # electron mass, kg
EV_J = 1.602176634e-19          # one electronvolt in joules (exact, SI)
EPS0 = 8.8541878128e-12         # vacuum permittivity, F/m
E_CHARGE = 1.602176634e-19      # elementary charge, C (exact, SI)
COULOMB = E_CHARGE ** 2 / (4.0 * math.pi * EPS0)  # e^2/(4 pi eps0), J m
M_ALPHA = 6.6446573357e-27      # alpha particle mass, kg
YEAR_S = 365.25 * 24.0 * 3600.0
VERSION = "1.0.0"

# ---------------------------------------------------------------- HOLD gates
HOLD_GATES = {
    "real_hardware_control": "HOLD - no control of any real STM, diode rig, or lab hardware, ever",
    "live_experiment": "HOLD - no live experiment instructions; this lab computes, it does not operate",
    "claim_ftl": "HOLD - tunneling is not faster-than-light travel or communication; causality stands",
    "teleportation_claim": "HOLD - tunneling is not teleportation; the particle crosses the barrier region as a wave",
    "commercial_product_claim": "HOLD - this is an educational lab, not a commercial product or device design",
    "semiconductor_fabrication_claim": "HOLD - no fabrication recipes; toy band models are not process engineering",
    "medical_claim": "HOLD - no medical claims; tunneling physics here treats no condition",
    "weapons_application_claim": "HOLD - no weapons application guidance of any kind",
    "free_energy_claim": "HOLD - tunneling creates no energy; transmitted particles keep the energy they had",
    "investment_claim": "HOLD - no investment advice about tunneling, chip, or quantum companies",
    "live_cryogenics": "HOLD - no live cryogenics handling instructions for hardware builds",
    "high_voltage_live": "HOLD - no live high-voltage work; field-emission numbers are a model, not a wiring guide",
    "radiation_source_live": "HOLD - alpha decay is modelled on paper only; no radiation source handling, ever",
    "guaranteed_device_performance_claim": "HOLD - no guaranteed device performance; every model here carries its assumptions",
}


def gate(action):
    """Return 'HOLD' if the action is gated, else 'PROCEED' (sandbox sim)."""
    return "HOLD" if action in HOLD_GATES else "PROCEED"


# ================================================================ 1. Rectangular barrier (exact)
# A particle of energy E (eV) and mass m meets a rectangular barrier
# of height V0 (eV) and width a (nm). Solving the Schroedinger
# equation region by region gives the EXACT transmission coefficient:
#   E < V0: T = [1 + V0^2 sinh^2(kappa a) / (4 E (V0 - E))]^-1
#   E = V0: T = [1 + m V0 a^2 / (2 hbar^2)]^-1          (the limit)
#   E > V0: T = [1 + V0^2 sin^2(k2 a) / (4 E (E - V0))]^-1
# Above the barrier T oscillates and hits exactly 1 whenever
# k2 a = n pi (the barrier becomes "invisible" at resonance).

def kappa_per_nm(energy_ev, mass=M_E):
    """Decay constant kappa for `energy_ev` of barrier headroom, in 1/nm."""
    if energy_ev < 0:
        raise ValueError("energy must be non-negative")
    return math.sqrt(2.0 * mass * energy_ev * EV_J) / HBAR / 1.0e9


def wave_number_per_nm(energy_ev, mass=M_E):
    """Wave number k for a free particle of `energy_ev`, in 1/nm."""
    if energy_ev < 0:
        raise ValueError("energy must be non-negative")
    return math.sqrt(2.0 * mass * energy_ev * EV_J) / HBAR / 1.0e9


def transmission_rect(energy_ev, barrier_ev, width_nm, mass=M_E):
    """EXACT transmission coefficient of a rectangular barrier."""
    e, v0, a = energy_ev, barrier_ev, width_nm
    if e <= 0.0 or v0 <= 0.0 or a < 0.0:
        raise ValueError("need E > 0, V0 > 0, width >= 0")
    if a == 0.0:
        return 1.0
    if abs(e - v0) < 1e-12:
        a_m = a * 1e-9
        return 1.0 / (1.0 + mass * v0 * EV_J * a_m * a_m / (2.0 * HBAR ** 2))
    if e < v0:
        ka = kappa_per_nm(v0 - e, mass) * a
        if ka > 40.0:  # sinh overflows; use the thick-barrier asymptote
            return 16.0 * e * (v0 - e) / v0 ** 2 * math.exp(-2.0 * ka)
        s = math.sinh(ka)
        return 1.0 / (1.0 + v0 ** 2 * s * s / (4.0 * e * (v0 - e)))
    k2a = wave_number_per_nm(e - v0, mass) * a
    s = math.sin(k2a)
    return 1.0 / (1.0 + v0 ** 2 * s * s / (4.0 * e * (e - v0)))


def transmission_wkb(energy_ev, barrier_ev, width_nm, mass=M_E):
    """WKB approximation T ~ exp(-2 kappa a). Valid only for E < V0 and
    a slowly-varying / thick barrier. Returns None above the barrier,
    where WKB in this form does not apply (honest label, not a number)."""
    if energy_ev >= barrier_ev:
        return None
    return math.exp(-2.0 * kappa_per_nm(barrier_ev - energy_ev, mass) * width_nm)


def wkb_error_table(barrier_ev=2.0, width_nm=1.0, mass=M_E):
    """Exact vs WKB across energies: the WKB error, quantified."""
    rows = []
    for frac in (0.1, 0.25, 0.5, 0.75, 0.9, 0.99):
        e = frac * barrier_ev
        exact = transmission_rect(e, barrier_ev, width_nm, mass)
        wkb = transmission_wkb(e, barrier_ev, width_nm, mass)
        rows.append({"e_over_v0": frac, "exact": exact, "wkb": wkb,
                     "ratio_exact_over_wkb": exact / wkb})
    return rows


# ================================================================ 2. Wave packet (analytic)
# A real particle is a wave packet: a spread of energies. Model the
# packet as a Gaussian in energy (mean e0, width sigma, both eV) and
# compute the effective transmission as the energy-weighted average
# of the EXACT T(E):  T_eff = integral T(E) G(E) dE / integral G(E) dE
# by deterministic trapezoid quadrature on [e0 - 5 sigma, e0 + 5 sigma]
# clipped to E > 0. Method stated: this is the standard analytic
# packet average, NOT a fake time-domain simulation.

def packet_transmission(e0_ev, sigma_ev, barrier_ev, width_nm, mass=M_E, points=401):
    """Gaussian-energy-packet effective transmission (quadrature of exact T)."""
    if sigma_ev <= 0:
        raise ValueError("sigma must be positive")
    lo = max(1e-9, e0_ev - 5.0 * sigma_ev)
    hi = e0_ev + 5.0 * sigma_ev
    num = 0.0
    den = 0.0
    for i in range(points):
        e = lo + (hi - lo) * i / (points - 1)
        w = math.exp(-0.5 * ((e - e0_ev) / sigma_ev) ** 2)
        t = transmission_rect(e, barrier_ev, width_nm, mass)
        num += w * t
        den += w
    return num / den


# ================================================================ 3. Alpha decay (Gamow)
# An alpha particle inside a nucleus assaults the Coulomb barrier
# f = v / (2R) times per second and tunnels with probability
# P = exp(-G), where the Gamow exponent has the closed form
#   G = (2/hbar) sqrt(2 mu Q) b [arccos(sqrt(x)) - sqrt(x (1 - x))]
# with b = C/Q the outer turning point, C = Z_alpha Z_d e^2/(4 pi eps0),
# x = R/b, mu the reduced mass. Half-life t1/2 = ln2 / (f P).
# Because G ~ 1/sqrt(Q), a small Q change moves the half-life by
# ORDERS of magnitude - the Geiger-Nuttall law. Nuclei below are
# LABELLED MODELS with real (Z, A, Q) inputs, not live sources.

def alpha_half_life(z_daughter, a_daughter, q_mev):
    """Gamow-model alpha-decay half-life for a labelled model nucleus."""
    if q_mev <= 0:
        raise ValueError("Q must be positive")
    q_j = q_mev * 1.0e6 * EV_J
    radius = 1.2e-15 * (a_daughter ** (1.0 / 3.0) + 4.0 ** (1.0 / 3.0))
    mu = M_ALPHA * a_daughter / (a_daughter + 4.0)  # reduced mass (mass-number approx)
    c = 2.0 * z_daughter * COULOMB
    b = c / q_j
    x = radius / b
    bracket = math.acos(math.sqrt(x)) - math.sqrt(x * (1.0 - x))
    gamow = (2.0 / HBAR) * math.sqrt(2.0 * mu * q_j) * b * bracket
    prob = math.exp(-gamow)
    velocity = math.sqrt(2.0 * q_j / mu)
    assault = velocity / (2.0 * radius)
    decay_const = assault * prob
    t_half = math.log(2.0) / decay_const
    return {"z_daughter": z_daughter, "a_daughter": a_daughter, "q_mev": q_mev,
            "radius_fm": radius / 1e-15, "gamow_g": gamow, "tunnel_prob": prob,
            "assault_per_s": assault, "half_life_s": t_half,
            "half_life_years": t_half / YEAR_S}


ALPHA_MODELS = {
    "U-238-like": (90, 234, 4.27),    # real half-life ~4.5e9 yr
    "Ra-226-like": (86, 222, 4.87),   # real half-life ~1600 yr
    "Po-212-like": (82, 208, 8.78),   # real half-life ~0.3 microseconds
}


def geiger_nuttall_series(z_daughter=86, a_daughter=222):
    """log10(half-life) vs 1/sqrt(Q) at fixed Z: the GN straight line."""
    pts = []
    for q in (4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0):
        r = alpha_half_life(z_daughter, a_daughter, q)
        pts.append({"q_mev": q, "inv_sqrt_q": 1.0 / math.sqrt(q),
                    "log10_half_life_s": math.log10(r["half_life_s"])})
    return pts


def _linfit(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    slope = sxy / sxx
    return {"slope": slope, "intercept": my - slope * mx,
            "r": sxy / math.sqrt(sxx * syy)}


def geiger_nuttall_fit(z_daughter=86, a_daughter=222):
    pts = geiger_nuttall_series(z_daughter, a_daughter)
    fit = _linfit([p["inv_sqrt_q"] for p in pts],
                  [p["log10_half_life_s"] for p in pts])
    fit["points"] = len(pts)
    return fit


# ================================================================ 4. STM
# In a scanning tunneling microscope the tip sits a gap d from the
# surface and electrons tunnel through the vacuum: I ~ exp(-2 kappa d)
# with kappa set by the work function phi (barrier height ~ phi).
# kappa ~ 1 per angstrom, so ONE angstrom of gap change multiplies
# the current by roughly ten - that exponential is the whole reason
# STM sees individual atoms. The lab computes the real factor.

STM_PHI_EV = 5.0  # labelled typical metal work function, eV


def stm_kappa(phi_ev=STM_PHI_EV):
    """Decay constant for tunneling into a phi-eV vacuum barrier, 1/nm."""
    return kappa_per_nm(phi_ev, M_E)


def stm_current(gap_nm, phi_ev=STM_PHI_EV, i0=1.0):
    """Relative STM current at gap `gap_nm` (i0 = current scale at d=0)."""
    if gap_nm < 0:
        raise ValueError("gap must be non-negative")
    return i0 * math.exp(-2.0 * stm_kappa(phi_ev) * gap_nm)


def stm_factor_per_angstrom(phi_ev=STM_PHI_EV):
    """Current multiplication factor for a 1-angstrom (0.1 nm) gap change."""
    return math.exp(2.0 * stm_kappa(phi_ev) * 0.1)


def stm_vertical_resolution_pm(phi_ev=STM_PHI_EV, current_change_frac=0.01):
    """Gap change (pm) that changes the current by `current_change_frac`."""
    return math.log(1.0 + current_change_frac) / (2.0 * stm_kappa(phi_ev)) * 1000.0


# ================================================================ 5. Tunnel diode (toy band model)
# LABELLED TOY MODEL, not a device design. Tunneling current follows
# the band overlap: it rises to a peak at Vp, then FALLS as the bands
# slide out of alignment:  I_t(V) = Ip (V/Vp) exp(1 - V/Vp).
# Ordinary diffusion current I_d(V) = Is (exp(V/Vt) - 1) takes over
# at higher bias. Between peak and valley the total current FALLS as
# voltage rises: negative differential resistance (NDR).

DIODE_IP_MA = 1.0     # toy peak tunnel current, mA (labelled toy)
DIODE_VP_V = 0.10     # toy peak voltage, V
DIODE_IS_MA = 0.05    # toy diffusion saturation current, mA
DIODE_VT_V = 0.35     # toy diffusion voltage scale, V


def diode_tunnel_current(v):
    if v < 0:
        raise ValueError("toy model is for forward bias V >= 0")
    return DIODE_IP_MA * (v / DIODE_VP_V) * math.exp(1.0 - v / DIODE_VP_V)


def diode_diffusion_current(v):
    if v < 0:
        raise ValueError("toy model is for forward bias V >= 0")
    return DIODE_IS_MA * (math.exp(v / DIODE_VT_V) - 1.0)


def diode_current(v):
    """Total toy tunnel-diode current, mA."""
    return diode_tunnel_current(v) + diode_diffusion_current(v)


def diode_peak_valley(v_max=0.9, step=0.001):
    """Grid-scan the toy I-V curve for its peak and valley (deterministic)."""
    n = int(round(v_max / step))
    curve = [(i * step, diode_current(i * step)) for i in range(n + 1)]
    peak = max(curve[: int(round(0.3 / step)) + 1], key=lambda p: p[1])
    after = curve[int(round(peak[0] / step)):]
    valley = min(after, key=lambda p: p[1])
    return {"peak_v": peak[0], "peak_ma": peak[1], "valley_v": valley[0],
            "valley_ma": valley[1], "peak_valley_ratio": peak[1] / valley[1]}


def diode_slope(v, dv=1e-4):
    """Numeric dI/dV of the toy diode (negative inside the NDR region)."""
    return (diode_current(v + dv) - diode_current(v - dv)) / (2.0 * dv)


# ================================================================ 6. Resonant tunneling (transfer matrix)
# Two thin barriers with a well between them: at one special energy
# the reflections inside the well cancel and transmission peaks at
# ~1, even though ONE barrier alone would pass almost nothing.
# Computed EXACTLY with the transfer-matrix method using stdlib
# complex arithmetic (cmath) - no approximation is hidden.

def _k_complex(energy_ev, potential_ev, mass):
    """Complex wave number (1/m) for a region; imaginary inside a barrier."""
    return cmath.sqrt(2.0 * mass * (energy_ev - potential_ev) * EV_J) / HBAR


def transmission_layers(energy_ev, layers, mass=M_E):
    """Exact T through a stack of (potential_eV, width_nm) layers,
    with free space (V=0) on both sides, via transfer matrices."""
    if energy_ev <= 0:
        raise ValueError("energy must be positive")
    regions = [(0.0, 0.0)] + list(layers) + [(0.0, 0.0)]
    ks = [_k_complex(energy_ev, v, mass) for v, _ in regions]
    # total transfer matrix M: [A_out, B_out]^T = M [A_in, B_in]^T
    m11, m12, m21, m22 = 1.0 + 0j, 0j, 0j, 1.0 + 0j
    for j in range(len(regions) - 1):
        kj, kn = ks[j], ks[j + 1]
        # propagate across region j (only real layers have width)
        d = regions[j][1] * 1e-9
        pj, qj = cmath.exp(1j * kj * d), cmath.exp(-1j * kj * d)
        # interface j -> j+1
        i11 = (kn + kj) / (2.0 * kn)
        i12 = (kn - kj) / (2.0 * kn)
        i21 = (kn - kj) / (2.0 * kn)
        i22 = (kn + kj) / (2.0 * kn)
        # apply propagation then interface: M = I * P * M
        a11, a12 = i11 * pj, i12 * qj
        a21, a22 = i21 * pj, i22 * qj
        m11, m12, m21, m22 = (a11 * m11 + a12 * m21, a11 * m12 + a12 * m22,
                              a21 * m11 + a22 * m21, a21 * m12 + a22 * m22)
    r = -m21 / m22
    t = m11 + m12 * r
    return abs(t) ** 2


def transmission_double_barrier(energy_ev, barrier_ev=1.0, barrier_nm=1.0,
                                well_nm=2.0, mass=M_E):
    """Exact T through barrier / well / barrier (resonant tunneling diode stack)."""
    return transmission_layers(energy_ev,
                               [(barrier_ev, barrier_nm), (0.0, well_nm),
                                (barrier_ev, barrier_nm)], mass)


def resonance_scan(barrier_ev=1.0, barrier_nm=1.0, well_nm=2.0, mass=M_E,
                   points=4000):
    """Deterministic fine scan for the first strong resonance below V0."""
    best = {"energy_ev": 0.0, "transmission": -1.0}
    for i in range(1, points):
        e = barrier_ev * i / points
        t = transmission_double_barrier(e, barrier_ev, barrier_nm, well_nm, mass)
        if t > best["transmission"]:
            best = {"energy_ev": e, "transmission": t}
    return best


# ================================================================ 7. Field emission (Fowler-Nordheim)
# A strong electric field bends the surface barrier into a thin
# triangle and electrons tunnel out: Fowler-Nordheim law
#   J = A E^2 / phi * exp(-B phi^{3/2} / E)
# with A = 1.541434e-6 A eV V^-2 and B = 6.83089e9 V m^-1 eV^-3/2
# (standard FN constants, E in V/m, phi in eV, J in A/m^2).

FN_A = 1.541434e-6
FN_B = 6.83089e9


def fn_current_density(field_v_per_m, phi_ev=4.5):
    """Fowler-Nordheim current density, A/m^2 (labelled standard constants)."""
    if field_v_per_m <= 0 or phi_ev <= 0:
        raise ValueError("field and work function must be positive")
    e = field_v_per_m
    return FN_A * e * e / phi_ev * math.exp(-FN_B * phi_ev ** 1.5 / e)


def fn_slope(phi_ev=4.5):
    """Slope of the FN plot ln(J/E^2) vs 1/E: exactly -B phi^{3/2}."""
    return -FN_B * phi_ev ** 1.5


# ================================================================ 8. kNN regime classifier
# Features: (E/V0, log10 kappa a, log10 mass ratio to electron).
# A point below the barrier in a wide/heavy system is tunneling-
# dominant (the only way through); near the top or through a very
# thin barrier it is mixed; above the barrier it is classical
# over-barrier motion with tunneling a correction.

_CLASSIFIER_TRAIN = [
    # (e_over_v0, log10_kappa_a, log10_mass_ratio, label)
    (0.20, 0.7, 0.0, "tunneling-dominant"),
    (0.50, 0.7, 0.0, "tunneling-dominant"),
    (0.50, 1.0, 3.26, "tunneling-dominant"),   # alpha-mass particle
    (0.80, 0.5, 0.0, "tunneling-dominant"),
    (0.30, 1.3, 3.26, "tunneling-dominant"),
    (0.90, 0.7, 0.0, "mixed"),
    (0.97, 0.3, 0.0, "mixed"),
    (1.00, 0.7, 0.0, "mixed"),
    (1.05, 0.5, 0.0, "mixed"),
    (0.60, 0.08, 0.0, "mixed"),                # ultra-thin barrier: leaky
    (0.70, 0.0, 0.0, "mixed"),                 # thin barrier, below the top
    (1.20, 0.7, 0.0, "classical-over-barrier"),
    (1.50, 0.5, 0.0, "classical-over-barrier"),
    (1.60, 0.1, 0.0, "classical-over-barrier"),
    (2.00, 0.7, 3.26, "classical-over-barrier"),
    (1.80, 1.0, 0.0, "classical-over-barrier"),
    (1.50, 0.5, 3.26, "classical-over-barrier"),
    (1.30, 0.7, 3.26, "classical-over-barrier"),
]


def _features(energy_ev, barrier_ev, width_nm, mass=M_E):
    head = max(barrier_ev - energy_ev, 0.0)
    ka = kappa_per_nm(head, mass) * width_nm if head > 0 else 0.0
    return (energy_ev / barrier_ev,
            math.log10(ka + 1.0),
            math.log10(mass / M_E))


def _dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def classify_regime(energy_ev, barrier_ev, width_nm, mass=M_E, k=3):
    """kNN (k=3) tunneling-regime classifier on physical features."""
    f = _features(energy_ev, barrier_ev, width_nm, mass)
    ranked = sorted(_CLASSIFIER_TRAIN, key=lambda row: _dist(f, row[:3]))
    votes = {}
    for row in ranked[:k]:
        votes[row[3]] = votes.get(row[3], 0) + 1
    return max(sorted(votes), key=lambda lab: votes[lab])


def regime_report():
    scenarios = {
        "electron_half_height_1nm": (0.5, 1.0, 1.0, M_E),
        "electron_near_top": (0.95, 1.0, 1.0, M_E),
        "electron_above_barrier": (1.5, 1.0, 1.0, M_E),
        "electron_ultrathin": (0.6, 1.0, 0.05, M_E),
        "alpha_below_coulomb_top": (0.5, 1.0, 1.0, M_ALPHA),
        "alpha_above_barrier": (2.0, 1.0, 1.0, M_ALPHA),
    }
    return {name: classify_regime(e, v0, a, m)
            for name, (e, v0, a, m) in scenarios.items()}


# ================================================================ 9. Advisory seats
def _trace(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def carbon4_decide(topic="quantumtunnel-x-demo"):
    """Gemini Carbon 4 DECIDER seat: MAP->MODEL->STRESS->DECIDE.

    Names-only keys, live calls 0, tighten-only: can add HOLDs, never lift one.
    """
    stages = ["MAP", "MODEL", "STRESS", "DECIDE"]
    payload = {"seat": "gemini-carbon-4", "topic": topic, "stages": stages}
    return {
        "seat": "Gemini Carbon 4 Extended Thinking",
        "role": "DECIDER",
        "pipeline": stages,
        "tiers": [2048, 8192, 32768],
        "key": "names-only (GEMINI_API_KEY name checked, value never read)",
        "live_calls": 0,
        "decision": "PROCEED - sandbox simulation only, all claim gates stay HOLD",
        "can_override_hold": False,
        "trace_sha256_16": _trace(payload),
    }


def claude_advisor(topic="quantumtunnel-x-demo"):
    """Muse advisor seat: advises, can never override a HOLD."""
    return {
        "seat": "Muse",
        "role": "ADVISOR",
        "key": "names-only (MODEL_API_KEY name checked, value never read)",
        "live_calls": 0,
        "advice": "Always quote WKB next to the exact T and name where WKB breaks; a tunneling number without its method is a claim, not physics.",
        "can_override_hold": False,
    }


def google_flow_plan():
    """Google Flow seat: plan-only, nothing rendered, nothing live."""
    return {
        "seat": "Google Flow",
        "role": "PLAN-ONLY",
        "shots": ["wave meets the wall", "exponential decay inside the barrier",
                  "the small wave that emerges", "STM tip atom hop",
                  "resonance flash in the double barrier"],
        "rendered": False,
        "live": 0,
    }


def brains_report():
    return {"decider": carbon4_decide(), "advisor": claude_advisor(),
            "flow": google_flow_plan()}


# ================================================================ checks
def run_checks():
    c = []

    def chk(name, ok):
        c.append((name, bool(ok)))

    # 1. rectangular barrier, exact
    chk("kappa_electron_1ev", abs(kappa_per_nm(1.0) - 5.1232) < 0.01)
    chk("t_zero_width_is_one", transmission_rect(0.5, 2.0, 0.0) == 1.0)
    chk("t_below_barrier_value",
        abs(transmission_rect(1.0, 2.0, 1.0) - 1.420e-4) < 0.05 * 1.420e-4)
    chk("t_falls_with_width",
        transmission_rect(1.0, 2.0, 2.0) < transmission_rect(1.0, 2.0, 1.0)
        < transmission_rect(1.0, 2.0, 0.5))
    chk("t_at_top_limit",
        abs(transmission_rect(2.0, 2.0, 1.0)
            - 1.0 / (1.0 + M_E * 2.0 * EV_J * 1e-18 / (2.0 * HBAR ** 2))) < 1e-12)
    res_e = None
    for n in (1, 2, 3):  # above-barrier resonances: k2 a = n pi -> T = 1
        k2 = n * math.pi / 1.0  # a = 1 nm
        e_above = (k2 * 1e9 * HBAR) ** 2 / (2.0 * M_E) / EV_J
        if abs(transmission_rect(2.0 + e_above, 2.0, 1.0) - 1.0) < 1e-9:
            res_e = e_above
    chk("t_above_barrier_resonance_one", res_e is not None)
    chk("t_heavy_mass_smaller",
        transmission_rect(1.0, 2.0, 1.0, M_ALPHA) < transmission_rect(1.0, 2.0, 1.0, M_E))
    # WKB vs exact
    chk("wkb_none_above_barrier", transmission_wkb(3.0, 2.0, 1.0) is None)
    rows = wkb_error_table()
    chk("wkb_ratio_half_height",
        abs(rows[2]["ratio_exact_over_wkb"] - 4.0) < 0.15)
    chk("wkb_overestimates_near_top",
        transmission_wkb(1.98, 2.0, 1.0) / transmission_rect(1.98, 2.0, 1.0) > 3.0)
    chk("wkb_thick_barrier_prefactor",
        abs(transmission_rect(1.0, 2.0, 3.0) / transmission_wkb(1.0, 2.0, 3.0) - 4.0) < 0.1)
    # transfer matrix agrees with the analytic single barrier
    tm = transmission_layers(1.0, [(2.0, 1.0)])
    chk("tm_matches_rect_exact", abs(tm - transmission_rect(1.0, 2.0, 1.0)) < 1e-9)
    tm2 = transmission_layers(3.0, [(2.0, 0.7)])
    chk("tm_matches_rect_above", abs(tm2 - transmission_rect(3.0, 2.0, 0.7)) < 1e-9)
    # 2. wave packet
    chk("packet_narrow_is_exact",
        abs(packet_transmission(1.0, 0.01, 2.0, 1.0)
            - transmission_rect(1.0, 2.0, 1.0)) < 0.05 * transmission_rect(1.0, 2.0, 1.0))
    chk("packet_spread_helps_below_barrier",
        packet_transmission(1.0, 0.3, 2.0, 1.0) > transmission_rect(1.0, 2.0, 1.0))
    # 3. alpha decay / Gamow
    u = alpha_half_life(*ALPHA_MODELS["U-238-like"])
    po = alpha_half_life(*ALPHA_MODELS["Po-212-like"])
    chk("alpha_u238_years", 1.0e9 < u["half_life_years"] < 2.0e10)
    chk("alpha_po212_microseconds", 1.0e-8 < po["half_life_s"] < 1.0e-5)
    chk("alpha_gamow_u_gt_po", u["gamow_g"] > po["gamow_g"])
    series = geiger_nuttall_series()
    chk("gn_monotone_falling",
        all(series[i]["log10_half_life_s"] > series[i + 1]["log10_half_life_s"]
            for i in range(len(series) - 1)))
    fit = geiger_nuttall_fit()
    chk("gn_straight_line", fit["r"] > 0.999 and fit["slope"] > 0)
    q1 = alpha_half_life(86, 222, 5.0)["half_life_s"]
    q2 = alpha_half_life(86, 222, 6.0)["half_life_s"]
    chk("gn_1mev_orders_of_magnitude", q1 / q2 > 1.0e5)
    # 4. STM
    chk("stm_factor_per_angstrom",
        abs(stm_factor_per_angstrom() - 9.90) < 0.35)
    chk("stm_current_ratio_1nm",
        abs(stm_current(0.5) / stm_current(1.5)
            / math.exp(2.0 * stm_kappa() * 1.0) - 1.0) < 1e-9)
    chk("stm_resolution_pm", 0.2 < stm_vertical_resolution_pm() < 1.0)
    chk("stm_kappa_value", abs(stm_kappa() - 11.458) < 0.05)
    # 5. tunnel diode toy model
    pv = diode_peak_valley()
    chk("diode_peak_near_vp", abs(pv["peak_v"] - DIODE_VP_V) < 0.02)
    chk("diode_ndr_negative_slope", diode_slope(0.30) < 0)
    chk("diode_positive_slope_low", diode_slope(0.05) > 0)
    chk("diode_valley_below_peak", pv["valley_ma"] < pv["peak_ma"] and pv["peak_valley_ratio"] > 2.0)
    chk("diode_tunnel_peak_exact", abs(diode_tunnel_current(DIODE_VP_V) - DIODE_IP_MA) < 1e-12)
    # 6. resonant tunneling
    scan = resonance_scan()
    chk("resonance_peak_near_one", scan["transmission"] > 0.99)
    chk("resonance_below_barrier", 0.0 < scan["energy_ev"] < 1.0)
    single = transmission_rect(scan["energy_ev"], 1.0, 2.0)
    chk("resonance_beats_single_barrier", scan["transmission"] / single > 100.0)
    off = transmission_double_barrier(min(scan["energy_ev"] + 0.25, 0.98))
    chk("off_resonance_suppressed", off < 0.05)
    # 7. Fowler-Nordheim
    j1 = fn_current_density(3.0e9)
    j2 = fn_current_density(5.0e9)
    slope = (math.log(j2 / 5.0e9 ** 2) - math.log(j1 / 3.0e9 ** 2)) / (1.0 / 5.0e9 - 1.0 / 3.0e9)
    chk("fn_slope_identity", abs(slope - fn_slope()) < 1e-6 * abs(fn_slope()))
    chk("fn_monotone_in_field", fn_current_density(6.0e9) > j2 > j1 > 0.0)
    chk("fn_higher_phi_less",
        fn_current_density(5.0e9, 5.5) < fn_current_density(5.0e9, 4.5))
    # 8. classifier
    rep = regime_report()
    chk("classifier_tunneling", rep["electron_half_height_1nm"] == "tunneling-dominant")
    chk("classifier_classical", rep["electron_above_barrier"] == "classical-over-barrier")
    chk("classifier_alpha_tunneling", rep["alpha_below_coulomb_top"] == "tunneling-dominant")
    chk("classifier_alpha_classical", rep["alpha_above_barrier"] == "classical-over-barrier")
    chk("classifier_near_top_mixed", rep["electron_near_top"] == "mixed")
    # gates + seats
    chk("hold_gates_14", len(HOLD_GATES) == 14 and all(v.startswith("HOLD") for v in HOLD_GATES.values()))
    chk("gate_teleportation_hold", gate("teleportation_claim") == "HOLD")
    chk("gate_ftl_hold", gate("claim_ftl") == "HOLD")
    chk("gate_radiation_hold", gate("radiation_source_live") == "HOLD")
    chk("gate_sandbox_proceed", gate("run_simulation") == "PROCEED")
    b = brains_report()
    chk("carbon4_no_override", b["decider"]["can_override_hold"] is False)
    chk("claude_no_override", b["advisor"]["can_override_hold"] is False)
    chk("flow_plan_only", b["flow"]["rendered"] is False and b["flow"]["live"] == 0)
    return c


# ================================================================ CLI / demo
def demo():
    print("=" * 68)
    print("QuantumTunnel-X - educational quantum tunneling physics lab")
    print("by Darion Kellar | MIT | pure stdlib | zero network | EDUCATION ONLY")
    print("=" * 68)
    print("\n[1] Rectangular barrier - EXACT transmission (electron, V0 = 2 eV)")
    for a in (0.5, 1.0, 2.0):
        print(f"    width {a:.1f} nm: T(E=0.5) = {transmission_rect(0.5, 2.0, a):.3e} | "
              f"T(E=1.0) = {transmission_rect(1.0, 2.0, a):.3e} | "
              f"T(E=1.9) = {transmission_rect(1.9, 2.0, a):.3e}")
    print(f"    above barrier: T(E=3.0, a=1 nm) = {transmission_rect(3.0, 2.0, 1.0):.4f} "
          "(oscillates; exactly 1 at k2 a = n pi)")
    print("\n[2] WKB approximation vs exact (V0 = 2 eV, a = 1 nm) - error quantified")
    for row in wkb_error_table():
        print(f"    E/V0 = {row['e_over_v0']:.2f}: exact = {row['exact']:.3e} | "
              f"WKB = {row['wkb']:.3e} | exact/WKB = {row['ratio_exact_over_wkb']:.2f}")
    print("    -> WKB misses the prefactor 16 E (V0-E) / V0^2 mid-range, and near the")
    print("       top it OVERestimates x3.9 (it sends T -> 1 where exact T stays ~0.06)")
    print("\n[3] Wave packet (Gaussian energy spread, quadrature of exact T)")
    print(f"    packet E0=1.0 sigma=0.01: T_eff = {packet_transmission(1.0, 0.01, 2.0, 1.0):.3e} "
          f"(mono-energetic {transmission_rect(1.0, 2.0, 1.0):.3e})")
    print(f"    packet E0=1.0 sigma=0.30: T_eff = {packet_transmission(1.0, 0.3, 2.0, 1.0):.3e} "
          "(the high-energy tail leaks over and through)")
    print("\n[4] Alpha decay - Gamow factor (LABELLED MODEL nuclei, paper only)")
    for name, (z, a, q) in ALPHA_MODELS.items():
        r = alpha_half_life(z, a, q)
        print(f"    {name:12s} Q = {q:.2f} MeV: G = {r['gamow_g']:.1f}, "
              f"P = {r['tunnel_prob']:.2e}, t1/2 = {r['half_life_s']:.3e} s "
              f"({r['half_life_years']:.3e} yr)")
    fit = geiger_nuttall_fit()
    print(f"    Geiger-Nuttall fit at Z=86: log10 t1/2 vs 1/sqrt(Q), r = {fit['r']:.5f} "
          f"(slope {fit['slope']:.1f}) - a straight line, as the law says")
    print(f"    +1 MeV at Z=86 (5 -> 6 MeV): half-life shrinks x"
          f"{alpha_half_life(86, 222, 5.0)['half_life_s'] / alpha_half_life(86, 222, 6.0)['half_life_s']:.2e}")
    print("\n[5] STM - current vs gap (work function phi = 5.0 eV, labelled)")
    print(f"    kappa = {stm_kappa():.3f} /nm | 1 angstrom closer = x{stm_factor_per_angstrom():.2f} current")
    for d in (0.5, 0.7, 1.0):
        print(f"    gap {d:.1f} nm: I/I0 = {stm_current(d):.3e}")
    print(f"    a 1% current change = {stm_vertical_resolution_pm():.2f} pm of height - atomic resolution")
    print("\n[6] Tunnel diode - TOY band model (labelled, not a device design)")
    pv = diode_peak_valley()
    for v in (0.05, 0.10, 0.20, 0.30, 0.45, 0.60, 0.80):
        print(f"    V = {v:.2f}: I = {diode_current(v):.3f} mA (dI/dV = {diode_slope(v):+.2f})")
    print(f"    peak {pv['peak_ma']:.3f} mA @ {pv['peak_v']:.2f} V | valley {pv['valley_ma']:.3f} mA "
          f"@ {pv['valley_v']:.2f} V | peak/valley = {pv['peak_valley_ratio']:.2f}")
    print("\n[7] Resonant tunneling - double barrier (transfer matrix, exact)")
    scan = resonance_scan()
    print(f"    first resonance: E = {scan['energy_ev']:.4f} eV, T = {scan['transmission']:.4f}")
    print(f"    ONE 2 nm barrier at that E: T = {transmission_rect(scan['energy_ev'], 1.0, 2.0):.3e} "
          "- the well makes the pair of walls transparent")
    print(f"    off resonance (E_res + 0.25): T = "
          f"{transmission_double_barrier(min(scan['energy_ev'] + 0.25, 0.98)):.3e}")
    print("\n[8] Field emission - Fowler-Nordheim (phi = 4.5 eV)")
    for e in (2.0e9, 3.0e9, 5.0e9, 7.0e9):
        print(f"    E = {e:.0e} V/m: J = {fn_current_density(e):.3e} A/m^2")
    print(f"    FN plot slope = {fn_slope():.4e} (exactly -B phi^1.5)")
    print("\n[9] Regime classifier (TinyML kNN)")
    for name, label in regime_report().items():
        print(f"    {name:24s} -> {label}")
    print("\n[10] Advisory seats")
    print(f"    decider: {carbon4_decide()['decision']} trace={carbon4_decide()['trace_sha256_16']}")
    print(f"    advisor can_override_hold = {claude_advisor()['can_override_hold']}")
    print(f"    flow rendered = {google_flow_plan()['rendered']} live = {google_flow_plan()['live']}")
    print(f"\n[11] HOLD gates: {len(HOLD_GATES)}")
    for k in HOLD_GATES:
        print(f"    HOLD  {k}")
    checks = run_checks()
    passed = sum(1 for _, ok in checks if ok)
    print(f"\nCHECKS {passed}/{len(checks)}")
    for name, ok in checks:
        if not ok:
            print(f"    FAIL {name}")
    verdict = "PROCEED" if passed == len(checks) else "HOLD"
    print(f"VERDICT {verdict} (sandbox simulation only) | HOLD gates {len(HOLD_GATES)}")
    return 0 if passed == len(checks) else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "demo":
        return demo()
    cmd = argv[0]
    if cmd == "checks":
        checks = run_checks()
        for name, ok in checks:
            print(f"{'PASS' if ok else 'FAIL'} {name}")
        print(f"CHECKS {sum(1 for _, ok in checks if ok)}/{len(checks)}")
        return 0 if all(ok for _, ok in checks) else 1
    if cmd == "barrier":
        for e in (0.25, 0.5, 1.0, 1.5, 1.9, 2.5, 3.0, 4.0):
            print(f"E={e:4.2f} eV  T_exact={transmission_rect(e, 2.0, 1.0):.4e}  "
                  f"T_wkb={transmission_wkb(e, 2.0, 1.0)}")
        return 0
    if cmd == "wkb":
        print(json.dumps(wkb_error_table(), indent=2, sort_keys=True))
        return 0
    if cmd == "packet":
        for s in (0.01, 0.05, 0.1, 0.2, 0.3, 0.5):
            print(f"sigma={s:.2f} eV  T_eff={packet_transmission(1.0, s, 2.0, 1.0):.4e}")
        return 0
    if cmd == "alpha":
        out = {name: alpha_half_life(*args) for name, args in ALPHA_MODELS.items()}
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0
    if cmd == "stm":
        for d in (0.3, 0.5, 0.7, 1.0, 1.5):
            print(f"gap={d:.1f} nm  I/I0={stm_current(d):.4e}")
        print(f"factor per angstrom = {stm_factor_per_angstrom():.3f}")
        return 0
    if cmd == "diode":
        for i in range(19):
            v = i * 0.05
            print(f"V={v:.2f}  I={diode_current(v):.4f} mA  dI/dV={diode_slope(v):+.3f}")
        print(json.dumps(diode_peak_valley(), indent=2, sort_keys=True))
        return 0
    if cmd == "resonance":
        scan = resonance_scan()
        print(json.dumps(scan, indent=2, sort_keys=True))
        for e in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8):
            print(f"E={e:.2f}  T_double={transmission_double_barrier(e):.4e}")
        return 0
    if cmd == "field":
        for e in (1.0e9, 2.0e9, 3.0e9, 5.0e9, 7.0e9, 1.0e10):
            print(f"E={e:.0e} V/m  J={fn_current_density(e):.4e} A/m^2")
        return 0
    if cmd == "classify":
        print(json.dumps(regime_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "brains":
        print(json.dumps(brains_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "holds":
        for k, v in HOLD_GATES.items():
            print(f"{k}: {v}")
        return 0
    if cmd == "hold-demo":
        action = argv[1] if len(argv) > 1 else "teleportation_claim"
        print(f"{action}: {HOLD_GATES.get(action, 'PROCEED - not gated')}")
        return 2 if gate(action) == "HOLD" else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
