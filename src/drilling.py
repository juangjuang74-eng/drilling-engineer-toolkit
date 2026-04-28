"""
drilling.py
===========
Core drilling engineering calculations module.

Covers:
- Well control (kick tolerance, kill mud weight, influx volume)
- Hydraulics (ECD, annular pressure loss, bit hydraulics)
- Torque & drag (soft-string model)
- Casing design (burst, collapse, tension)
- Directional drilling (survey calculations, build rates)
- Pore pressure & fracture gradient estimation
- Formation evaluation (d-exponent, ROP analysis)

References:
    Bourgoyne et al. (1986). Applied Drilling Engineering. SPE Textbook Vol. 2.
    Mitchell & Miska (2011). Fundamentals of Drilling Engineering. SPE Textbook Vol. 12.
    Rabia (2002). Well Engineering & Construction. Entrac Petroleum.
"""

import numpy as np
import math
from dataclasses import dataclass
from typing import Optional, List, Tuple


# ─── Unit conversion constants ───────────────────────────────────────────────
PPG_TO_PSI_FT   = 0.052        # 1 ppg × 0.052 = psi/ft
PSI_FT_TO_PPG   = 1 / 0.052
FT_TO_M         = 0.3048
M_TO_FT         = 3.28084
LBF_TO_KN       = 0.004448
KN_TO_LBF       = 224.809
GPM_TO_LPS      = 0.06309
BBL_TO_GAL      = 42.0
GAL_TO_BBL      = 1 / 42.0


# ─── Data classes ─────────────────────────────────────────────────────────────
@dataclass
class WellGeometry:
    """Describes well geometry for hydraulics and well control calculations."""
    tvd_ft: float               # True vertical depth (ft)
    md_ft: float                # Measured depth (ft)
    hole_size_in: float         # Open hole diameter (in)
    dp_od_in: float             # Drill pipe OD (in)
    dp_id_in: float             # Drill pipe ID (in)
    dc_od_in: float             # Drill collar OD (in)
    dc_id_in: float             # Drill collar ID (in)
    dc_length_ft: float         # Drill collar length (ft)
    casing_id_in: float         # Casing ID (in)
    casing_shoe_tvd_ft: float   # Casing shoe TVD (ft)


@dataclass
class FluidProperties:
    """Drilling fluid (mud) properties."""
    mw_ppg: float               # Mud weight (ppg)
    pv_cp: float                # Plastic viscosity (cP)
    yp_lbf100sqft: float        # Yield point (lbf/100 sq ft)
    gel_10s: float              # 10-second gel strength (lbf/100 sq ft)
    gel_10m: float              # 10-minute gel strength (lbf/100 sq ft)


@dataclass
class KickData:
    """Data captured at shut-in after a kick."""
    sidpp_psi: float            # Shut-in drill pipe pressure (psi)
    sicp_psi: float             # Shut-in casing pressure (psi)
    pit_gain_bbl: float         # Pit gain volume (bbl)
    mw_ppg: float               # Current mud weight (ppg)
    tvd_ft: float               # Well TVD at kick zone (ft)
    dp_capacity_bbl_ft: float   # Drill pipe capacity (bbl/ft)
    ann_capacity_bbl_ft: float  # Annulus capacity (bbl/ft)


# ═══════════════════════════════════════════════════════════════════════════════
# WELL CONTROL
# ═══════════════════════════════════════════════════════════════════════════════

def kill_mud_weight(mw_ppg: float, sidpp_psi: float, tvd_ft: float) -> float:
    """
    Calculate kill mud weight (Driller's Method / Wait & Weight).

    KMW = MW_current + SIDPP / (0.052 × TVD)

    Args:
        mw_ppg:   Current mud weight (ppg)
        sidpp_psi: Shut-in drill pipe pressure (psi)
        tvd_ft:   True vertical depth to kick zone (ft)

    Returns:
        Kill mud weight (ppg)

    Reference:
        Bourgoyne et al. (1986), Ch. 4.
    """
    if tvd_ft <= 0:
        raise ValueError("TVD must be positive.")
    return mw_ppg + sidpp_psi / (PPG_TO_PSI_FT * tvd_ft)


def initial_circulating_pressure(
    sidpp_psi: float,
    slow_pump_pressure_psi: float
) -> float:
    """
    Initial circulating pressure (ICP) for Driller's Method kill.

    ICP = SIDPP + Slow Pump Pressure

    Args:
        sidpp_psi:              Shut-in drill pipe pressure (psi)
        slow_pump_pressure_psi: Slow circulating rate pressure (psi)

    Returns:
        ICP (psi)
    """
    return sidpp_psi + slow_pump_pressure_psi


def final_circulating_pressure(
    slow_pump_pressure_psi: float,
    kill_mw_ppg: float,
    original_mw_ppg: float
) -> float:
    """
    Final circulating pressure (FCP) when kill mud reaches the bit.

    FCP = SCR × (KMW / MW_original)

    Args:
        slow_pump_pressure_psi: Slow circulating rate pressure (psi)
        kill_mw_ppg:            Kill mud weight (ppg)
        original_mw_ppg:        Original mud weight (ppg)

    Returns:
        FCP (psi)
    """
    if original_mw_ppg <= 0:
        raise ValueError("Original mud weight must be positive.")
    return slow_pump_pressure_psi * (kill_mw_ppg / original_mw_ppg)


def formation_pressure(mw_ppg: float, tvd_ft: float, sidpp_psi: float = 0.0) -> float:
    """
    Estimate formation (pore) pressure.

    Pf = 0.052 × MW × TVD + SIDPP

    Args:
        mw_ppg:    Mud weight (ppg)
        tvd_ft:    TVD (ft)
        sidpp_psi: Shut-in drill pipe pressure (psi), default 0

    Returns:
        Formation pressure (psi)
    """
    return PPG_TO_PSI_FT * mw_ppg * tvd_ft + sidpp_psi


def kick_tolerance(
    casing_burst_psi: float,
    mw_ppg: float,
    shoe_tvd_ft: float,
    kick_influx_gradient_psi_ft: float = 0.1
) -> float:
    """
    Maximum allowable kick size before formation fractures at shoe.

    Kick Tolerance (bbl) is scenario-specific; this returns the
    maximum influx height before shoe fracture, in ft.

    Args:
        casing_burst_psi:           Casing shoe fracture pressure (psi)
        mw_ppg:                     Current mud weight (ppg)
        shoe_tvd_ft:                Casing shoe TVD (ft)
        kick_influx_gradient_psi_ft: Kick fluid gradient (psi/ft), default 0.1 gas

    Returns:
        Maximum influx column height (ft)
    """
    mud_gradient = PPG_TO_PSI_FT * mw_ppg
    delta_gradient = mud_gradient - kick_influx_gradient_psi_ft
    if delta_gradient <= 0:
        raise ValueError("Influx gradient must be less than mud gradient.")
    return casing_burst_psi / delta_gradient


def influx_type(
    mw_ppg: float,
    sicp_psi: float,
    sidpp_psi: float,
    ann_capacity_bbl_ft: float,
    pit_gain_bbl: float
) -> str:
    """
    Estimate kick fluid type from pressure and volume data.

    Args:
        mw_ppg:              Current mud weight (ppg)
        sicp_psi:            Shut-in casing pressure (psi)
        sidpp_psi:           Shut-in drill pipe pressure (psi)
        ann_capacity_bbl_ft: Annular capacity (bbl/ft)
        pit_gain_bbl:        Pit gain (bbl)

    Returns:
        String: 'gas', 'oil', or 'saltwater'
    """
    influx_height_ft = pit_gain_bbl / ann_capacity_bbl_ft
    influx_gradient = (sicp_psi - sidpp_psi) / influx_height_ft if influx_height_ft > 0 else 0
    mud_gradient = mw_ppg * PPG_TO_PSI_FT

    if influx_gradient < 0.12:
        return "gas"
    elif influx_gradient < 0.35:
        return "oil"
    else:
        return "saltwater"


# ═══════════════════════════════════════════════════════════════════════════════
# HYDRAULICS
# ═══════════════════════════════════════════════════════════════════════════════

def hydrostatic_pressure(mw_ppg: float, tvd_ft: float) -> float:
    """
    Hydrostatic pressure at depth.

    P_h = 0.052 × MW × TVD

    Args:
        mw_ppg: Mud weight (ppg)
        tvd_ft: True vertical depth (ft)

    Returns:
        Hydrostatic pressure (psi)
    """
    return PPG_TO_PSI_FT * mw_ppg * tvd_ft


def annular_pressure_loss_bingham(
    mw_ppg: float,
    pv_cp: float,
    yp_lbf100sqft: float,
    flow_rate_gpm: float,
    hole_size_in: float,
    pipe_od_in: float,
    length_ft: float
) -> float:
    """
    Annular pressure loss using Bingham Plastic model.

    P_ann = (PV × v) / (300 × d_ann) + YP / (225 × d_ann)  (psi)

    where d_ann = D_h - D_p (in) and v = velocity (ft/min)

    Args:
        mw_ppg:           Mud weight (ppg)
        pv_cp:            Plastic viscosity (cP)
        yp_lbf100sqft:    Yield point (lbf/100 sq ft)
        flow_rate_gpm:    Flow rate (gpm)
        hole_size_in:     Hole diameter (in)
        pipe_od_in:       Pipe OD (in)
        length_ft:        Annular interval length (ft)

    Returns:
        Annular pressure loss (psi)

    Reference:
        Bourgoyne et al. (1986), Eq. 4.36.
    """
    d_ann = hole_size_in - pipe_od_in  # annular diameter (in)
    if d_ann <= 0:
        raise ValueError("Hole size must exceed pipe OD.")
    area_ann = math.pi / 4 * ((hole_size_in/12)**2 - (pipe_od_in/12)**2)  # ft²
    v_fps = (flow_rate_gpm * GAL_TO_BBL * 5.615) / (60 * area_ann)
    v_fpm = v_fps * 60

    p_loss_per_ft = (pv_cp * v_fpm) / (300 * d_ann) + yp_lbf100sqft / (225 * d_ann)
    return p_loss_per_ft * length_ft


def ecd(
    mw_ppg: float,
    ann_pressure_loss_psi: float,
    tvd_ft: float
) -> float:
    """
    Equivalent Circulating Density (ECD).

    ECD = MW + Ann_P_loss / (0.052 × TVD)

    Args:
        mw_ppg:               Static mud weight (ppg)
        ann_pressure_loss_psi: Total annular pressure loss (psi)
        tvd_ft:               TVD at point of interest (ft)

    Returns:
        ECD (ppg)
    """
    if tvd_ft <= 0:
        raise ValueError("TVD must be positive.")
    return mw_ppg + ann_pressure_loss_psi / (PPG_TO_PSI_FT * tvd_ft)


def bit_hydraulic_horsepower(
    flow_rate_gpm: float,
    bit_pressure_drop_psi: float
) -> float:
    """
    Bit hydraulic horsepower (HHP).

    HHP = Q × ΔP / 1714

    Args:
        flow_rate_gpm:      Flow rate (gpm)
        bit_pressure_drop_psi: Pressure drop across bit (psi)

    Returns:
        Hydraulic horsepower (HP)
    """
    return (flow_rate_gpm * bit_pressure_drop_psi) / 1714.0


def jet_velocity(
    flow_rate_gpm: float,
    nozzle_sizes_in: List[float]
) -> float:
    """
    Bit nozzle jet velocity.

    v_j = Q / (0.32 × A_n)

    Args:
        flow_rate_gpm:    Flow rate (gpm)
        nozzle_sizes_in:  List of nozzle diameters (1/32 in units)

    Returns:
        Jet velocity (ft/s)
    """
    total_area = sum((n / 32.0)**2 for n in nozzle_sizes_in) * math.pi / 4
    if total_area <= 0:
        raise ValueError("Nozzle area must be positive.")
    return flow_rate_gpm / (0.32 * total_area)


def impact_force(
    mw_ppg: float,
    flow_rate_gpm: float,
    jet_velocity_fps: float
) -> float:
    """
    Bit impact force.

    F_i = MW × Q × v_j / 1930

    Args:
        mw_ppg:           Mud weight (ppg)
        flow_rate_gpm:    Flow rate (gpm)
        jet_velocity_fps: Jet velocity (ft/s)

    Returns:
        Impact force (lbf)
    """
    return (mw_ppg * flow_rate_gpm * jet_velocity_fps) / 1930.0


def critical_flow_rate(
    mw_ppg: float,
    pv_cp: float,
    yp_lbf100sqft: float,
    hole_size_in: float,
    pipe_od_in: float
) -> float:
    """
    Critical flow rate for turbulent/laminar transition in annulus.

    Uses Bingham Plastic critical velocity correlation.

    Args:
        mw_ppg:           Mud weight (ppg)
        pv_cp:            Plastic viscosity (cP)
        yp_lbf100sqft:    Yield point (lbf/100 sq ft)
        hole_size_in:     Hole diameter (in)
        pipe_od_in:       Pipe OD (in)

    Returns:
        Critical flow rate (gpm)
    """
    d_ann = hole_size_in - pipe_od_in
    vc = (97 / mw_ppg) * (pv_cp + math.sqrt(pv_cp**2 + 6.2 * yp_lbf100sqft * mw_ppg * d_ann**2))
    area_ft2 = math.pi / 4 * ((hole_size_in/12)**2 - (pipe_od_in/12)**2)
    return vc * area_ft2 * 60 / 5.615 * BBL_TO_GAL


# ═══════════════════════════════════════════════════════════════════════════════
# TORQUE & DRAG (Soft-String Model)
# ═══════════════════════════════════════════════════════════════════════════════

def hookload_vertical(
    wob_lbf: float,
    string_weight_lbf: float,
    buoyancy_factor: float
) -> float:
    """
    Hook load for vertical section (simplified).

    HL = (W_string - WOB) × BF

    Args:
        wob_lbf:           Weight on bit (lbf)
        string_weight_lbf: Total drill string air weight (lbf)
        buoyancy_factor:   Buoyancy factor (dimensionless)

    Returns:
        Hook load (lbf)
    """
    return (string_weight_lbf - wob_lbf) * buoyancy_factor


def buoyancy_factor(mw_ppg: float, steel_density_ppg: float = 65.5) -> float:
    """
    Buoyancy factor for steel drill string in drilling fluid.

    BF = 1 - (MW / ρ_steel)

    Args:
        mw_ppg:             Mud weight (ppg)
        steel_density_ppg:  Steel density (ppg), default 65.5

    Returns:
        Buoyancy factor (dimensionless)
    """
    return 1 - (mw_ppg / steel_density_ppg)


def drag_force(
    normal_force_lbf: float,
    friction_coefficient: float = 0.25
) -> float:
    """
    Axial drag force (simplified soft-string).

    F_drag = μ × N

    Args:
        normal_force_lbf:   Normal contact force (lbf)
        friction_coefficient: Friction factor μ (dimensionless), default 0.25

    Returns:
        Drag force (lbf)
    """
    return friction_coefficient * normal_force_lbf


def surface_torque(
    wob_lbf: float,
    bit_size_in: float,
    tfa_friction_coeff: float = 0.4
) -> float:
    """
    Estimated bit torque (simplified).

    T_bit ≈ (1/3) × μ × WOB × bit_radius

    Args:
        wob_lbf:            Weight on bit (lbf)
        bit_size_in:        Bit diameter (in)
        tfa_friction_coeff: Torque friction coefficient, default 0.4

    Returns:
        Approximate bit torque (ft·lbf)
    """
    bit_radius_ft = (bit_size_in / 2) / 12
    return (1 / 3) * tfa_friction_coeff * wob_lbf * bit_radius_ft


# ═══════════════════════════════════════════════════════════════════════════════
# CASING DESIGN
# ═══════════════════════════════════════════════════════════════════════════════

def burst_pressure(
    formation_pressure_psi: float,
    casing_tvd_ft: float,
    fluid_gradient_inside_psi_ft: float = 0.0
) -> float:
    """
    Net burst pressure acting on casing string.

    P_burst_net = P_formation - P_fluid_inside

    Args:
        formation_pressure_psi:       External formation pressure (psi)
        casing_tvd_ft:                TVD of point of interest (ft)
        fluid_gradient_inside_psi_ft: Internal fluid gradient (psi/ft), default 0 (gas)

    Returns:
        Net burst pressure (psi)
    """
    p_inside = fluid_gradient_inside_psi_ft * casing_tvd_ft
    return formation_pressure_psi - p_inside


def collapse_pressure(
    mud_weight_ppg: float,
    tvd_ft: float,
    fluid_inside_gradient_psi_ft: float = 0.0
) -> float:
    """
    Net collapse pressure on casing (external - internal).

    P_collapse_net = P_external - P_internal

    Args:
        mud_weight_ppg:              External mud weight (ppg)
        tvd_ft:                      TVD (ft)
        fluid_inside_gradient_psi_ft: Internal fluid gradient (psi/ft)

    Returns:
        Net collapse pressure (psi)
    """
    p_ext = PPG_TO_PSI_FT * mud_weight_ppg * tvd_ft
    p_int = fluid_inside_gradient_psi_ft * tvd_ft
    return p_ext - p_int


def tension_load(
    string_weight_lbf: float,
    buoyancy_fac: float,
    overpull_lbf: float = 0.0
) -> float:
    """
    Maximum tension load at top of casing string.

    T = W_air × BF + Overpull

    Args:
        string_weight_lbf: Air weight of casing string (lbf)
        buoyancy_fac:      Buoyancy factor
        overpull_lbf:      Overpull applied during running (lbf)

    Returns:
        Tension load (lbf)
    """
    return string_weight_lbf * buoyancy_fac + overpull_lbf


def safety_factor(rated_value: float, applied_value: float) -> float:
    """
    Design safety factor.

    SF = Rated / Applied

    Args:
        rated_value:   Rated capacity (burst, collapse, or tension)
        applied_value: Applied load

    Returns:
        Safety factor (dimensionless)
    """
    if applied_value == 0:
        return float('inf')
    return rated_value / applied_value


# ═══════════════════════════════════════════════════════════════════════════════
# DIRECTIONAL DRILLING
# ═══════════════════════════════════════════════════════════════════════════════

def minimum_curvature(
    md1_ft: float,
    md2_ft: float,
    inc1_deg: float,
    azi1_deg: float,
    inc2_deg: float,
    azi2_deg: float
) -> Tuple[float, float, float]:
    """
    Minimum Curvature Method — survey calculation.

    Computes the TVD, North, and East increments between two survey stations.

    Args:
        md1_ft, md2_ft:   Measured depths (ft)
        inc1_deg, inc2_deg: Inclinations (degrees)
        azi1_deg, azi2_deg: Azimuths (degrees)

    Returns:
        Tuple of (delta_TVD, delta_North, delta_East) in ft

    Reference:
        Bourgoyne et al. (1986), Appendix B.
    """
    delta_md = md2_ft - md1_ft
    i1, i2 = math.radians(inc1_deg), math.radians(inc2_deg)
    a1, a2 = math.radians(azi1_deg), math.radians(azi2_deg)

    dl_rad = math.acos(
        math.cos(i2 - i1) - math.sin(i1) * math.sin(i2) * (1 - math.cos(a2 - a1))
    )
    rf = (2 / dl_rad) * math.tan(dl_rad / 2) if dl_rad > 1e-6 else 1.0  # ratio factor

    delta_tvd   = (delta_md / 2) * (math.cos(i1) + math.cos(i2)) * rf
    delta_north = (delta_md / 2) * (math.sin(i1) * math.cos(a1) + math.sin(i2) * math.cos(a2)) * rf
    delta_east  = (delta_md / 2) * (math.sin(i1) * math.sin(a1) + math.sin(i2) * math.sin(a2)) * rf

    return delta_tvd, delta_north, delta_east


def dogleg_severity(
    inc1_deg: float, azi1_deg: float,
    inc2_deg: float, azi2_deg: float,
    delta_md_ft: float
) -> float:
    """
    Dogleg severity (DLS) in degrees per 100 ft.

    DLS = arccos[cos(I2-I1) - sin(I1)·sin(I2)·(1-cos(A2-A1))] / ΔMD × 100

    Args:
        inc1_deg, azi1_deg: Survey station 1 (degrees)
        inc2_deg, azi2_deg: Survey station 2 (degrees)
        delta_md_ft:        MD interval (ft)

    Returns:
        DLS (°/100 ft)
    """
    if delta_md_ft <= 0:
        return 0.0
    i1, i2 = math.radians(inc1_deg), math.radians(inc2_deg)
    a1, a2 = math.radians(azi1_deg), math.radians(azi2_deg)
    cos_dl = math.cos(i2 - i1) - math.sin(i1) * math.sin(i2) * (1 - math.cos(a2 - a1))
    cos_dl = max(-1.0, min(1.0, cos_dl))
    dl_deg = math.degrees(math.acos(cos_dl))
    return dl_deg / delta_md_ft * 100


def build_rate_required(
    kick_off_depth_ft: float,
    target_tvd_ft: float,
    target_departure_ft: float,
    target_inclination_deg: float
) -> float:
    """
    Required build rate to reach target with a simple 2D build-and-hold profile.

    Args:
        kick_off_depth_ft:    KOP depth (ft TVD)
        target_tvd_ft:        Target TVD (ft)
        target_departure_ft:  Target horizontal departure (ft)
        target_inclination_deg: Target inclination at EOB (degrees)

    Returns:
        Build rate (°/100 ft)
    """
    inc_rad = math.radians(target_inclination_deg)
    radius = target_departure_ft / (1 - math.cos(inc_rad)) if inc_rad > 1e-4 else float('inf')
    build_depth = kick_off_depth_ft + radius * math.sin(inc_rad)
    md_build = radius * inc_rad
    if md_build <= 0:
        return 0.0
    return target_inclination_deg / md_build * 100


# ═══════════════════════════════════════════════════════════════════════════════
# PORE PRESSURE & FRACTURE GRADIENT
# ═══════════════════════════════════════════════════════════════════════════════

def eaton_fracture_gradient(
    overburden_gradient_psi_ft: float,
    pore_pressure_gradient_psi_ft: float,
    poisson_ratio: float = 0.25
) -> float:
    """
    Eaton (1969) fracture gradient correlation.

    FG = (ν/(1-ν)) × (OB - PP) + PP

    where OB = overburden gradient, PP = pore pressure gradient.

    Args:
        overburden_gradient_psi_ft:  Overburden gradient (psi/ft)
        pore_pressure_gradient_psi_ft: Pore pressure gradient (psi/ft)
        poisson_ratio:               Poisson's ratio (0.2–0.5), default 0.25

    Returns:
        Fracture gradient (psi/ft)

    Reference:
        Eaton, B.A. (1969). Fracture Gradient Prediction. JPT.
    """
    ratio = poisson_ratio / (1 - poisson_ratio)
    return ratio * (overburden_gradient_psi_ft - pore_pressure_gradient_psi_ft) + pore_pressure_gradient_psi_ft


def d_exponent(
    rop_ft_hr: float,
    rpm: float,
    wob_lbf: float,
    bit_size_in: float,
    mud_weight_ppg: float,
    normal_mw_ppg: float = 8.6
) -> float:
    """
    Corrected d-exponent for pore pressure detection.

    dc = d × (MW_normal / MW_actual)

    where d = log(ROP/60/RPM) / log(12×WOB / 1000×bit_size)

    Args:
        rop_ft_hr:      Rate of penetration (ft/hr)
        rpm:            Rotary speed (rpm)
        wob_lbf:        Weight on bit (lbf)
        bit_size_in:    Bit size (in)
        mud_weight_ppg: Actual mud weight (ppg)
        normal_mw_ppg:  Normal mud weight (ppg), default 8.6

    Returns:
        Corrected d-exponent (dimensionless)

    Reference:
        Rehm & McClendon (1971). Measurement of Formation Pressure from Drilling Data. IADC.
    """
    if rpm <= 0 or wob_lbf <= 0 or bit_size_in <= 0 or rop_ft_hr <= 0:
        return float('nan')
    numerator   = math.log10((rop_ft_hr / 60) / rpm)
    denominator = math.log10((12 * wob_lbf) / (1000 * bit_size_in))
    if abs(denominator) < 1e-9:
        return float('nan')
    d = numerator / denominator
    dc = d * (normal_mw_ppg / mud_weight_ppg)
    return dc


# ═══════════════════════════════════════════════════════════════════════════════
# CEMENTING
# ═══════════════════════════════════════════════════════════════════════════════

def cement_slurry_volume(
    hole_size_in: float,
    casing_od_in: float,
    interval_ft: float,
    excess_factor: float = 1.25
) -> float:
    """
    Cement slurry volume required to fill annular interval.

    V = (π/4) × (D_hole² - D_casing²) × length × excess

    Args:
        hole_size_in:   Hole diameter (in)
        casing_od_in:   Casing OD (in)
        interval_ft:    Interval to cement (ft)
        excess_factor:  Volume excess multiplier, default 1.25 (25% excess)

    Returns:
        Cement volume (bbl)
    """
    area_ft2 = math.pi / 4 * ((hole_size_in/12)**2 - (casing_od_in/12)**2)
    vol_ft3  = area_ft2 * interval_ft
    return vol_ft3 / 5.615 * excess_factor  # ft³ → bbl


def displacement_volume(casing_id_in: float, casing_length_ft: float) -> float:
    """
    Displacement volume to pump cement down casing.

    Args:
        casing_id_in:    Casing ID (in)
        casing_length_ft: Total casing length (ft)

    Returns:
        Displacement volume (bbl)
    """
    area_ft2 = math.pi / 4 * (casing_id_in / 12)**2
    return area_ft2 * casing_length_ft / 5.615


# ═══════════════════════════════════════════════════════════════════════════════
# ROP OPTIMIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def bingham_rop_model(
    wob_lbf: float,
    rpm: float,
    bit_size_in: float,
    a1: float = 1.0,
    a2: float = 1.0
) -> float:
    """
    Simplified Bingham ROP model.

    ROP = a1 × (WOB / bit_size)^a2 × RPM

    Args:
        wob_lbf:    Weight on bit (lbf)
        rpm:        Rotary speed (RPM)
        bit_size_in: Bit diameter (in)
        a1, a2:     Empirical constants (calibrate from offset wells)

    Returns:
        ROP (ft/hr)
    """
    if bit_size_in <= 0 or rpm <= 0 or wob_lbf <= 0:
        return 0.0
    return a1 * (wob_lbf / bit_size_in)**a2 * rpm


def cost_per_foot(
    bit_cost_usd: float,
    rig_rate_usd_hr: float,
    drill_time_hr: float,
    trip_time_hr: float,
    footage_ft: float
) -> float:
    """
    Drilling cost per foot (classic CPF formula).

    CPF = (Bit_cost + Rig_rate × (drill_time + trip_time)) / footage

    Args:
        bit_cost_usd:    Bit purchase cost (USD)
        rig_rate_usd_hr: Rig day rate per hour (USD/hr)
        drill_time_hr:   Time spent drilling (hr)
        trip_time_hr:    Trip time (hr)
        footage_ft:      Footage drilled (ft)

    Returns:
        Cost per foot (USD/ft)
    """
    if footage_ft <= 0:
        raise ValueError("Footage must be positive.")
    total_cost = bit_cost_usd + rig_rate_usd_hr * (drill_time_hr + trip_time_hr)
    return total_cost / footage_ft
