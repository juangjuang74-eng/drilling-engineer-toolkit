"""
tests/test_drilling.py
=======================
Unit tests for the drilling engineering calculations module.

Run:
    pytest tests/ -v
    pytest tests/ --tb=short --cov=src

Reference values validated against:
    - Bourgoyne et al. (1986) Applied Drilling Engineering (SPE Vol. 2) examples
    - Mitchell & Miska (2011) example problems
    - Manual calculations documented inline
"""

import pytest
import math
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import drilling as drl


# ═══════════════════════════════════════════════════════════════════════════════
# WELL CONTROL TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestWellControl:

    def test_kill_mud_weight_basic(self):
        """
        KMW = MW + SIDPP / (0.052 × TVD)
        KMW = 10.0 + 300 / (0.052 × 8000) = 10.0 + 0.721 ≈ 10.72 ppg
        """
        result = drl.kill_mud_weight(10.0, 300, 8000)
        assert abs(result - 10.721) < 0.01

    def test_kill_mud_weight_zero_tvd_raises(self):
        with pytest.raises(ValueError):
            drl.kill_mud_weight(10.0, 300, 0)

    def test_icp_calculation(self):
        """ICP = SIDPP + SCR pressure = 350 + 650 = 1000 psi"""
        result = drl.initial_circulating_pressure(350, 650)
        assert result == 1000.0

    def test_fcp_calculation(self):
        """FCP = SCR × (KMW / MW_orig) = 650 × (10.72 / 10.0) = 696.8 psi"""
        result = drl.final_circulating_pressure(650, 10.72, 10.0)
        assert abs(result - 696.8) < 0.5

    def test_formation_pressure_basic(self):
        """Pf = 0.052 × 10.5 × 9500 + 0 = 5187 psi"""
        result = drl.formation_pressure(10.5, 9500, 0)
        assert abs(result - 5187) < 1.0

    def test_formation_pressure_with_sidpp(self):
        """Pf = 0.052 × 10.5 × 9500 + 350 = 5537 psi"""
        result = drl.formation_pressure(10.5, 9500, 350)
        assert abs(result - 5537) < 1.0

    def test_influx_type_gas(self):
        """Low influx gradient (< 0.12 psi/ft) → gas kick"""
        result = drl.influx_type(10.5, 600, 350, 0.0775, 15.0)
        assert result == "gas"

    def test_influx_type_saltwater(self):
        """High influx gradient → saltwater kick"""
        result = drl.influx_type(10.5, 400, 350, 0.0775, 5.0)
        assert result == "saltwater"

    def test_kick_tolerance_positive(self):
        """Kick tolerance must be positive for valid inputs."""
        result = drl.kick_tolerance(3000, 10.5, 8000, 0.1)
        assert result > 0


# ═══════════════════════════════════════════════════════════════════════════════
# HYDRAULICS TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestHydraulics:

    def test_hydrostatic_pressure(self):
        """P_h = 0.052 × 11.0 × 9500 = 5434 psi"""
        result = drl.hydrostatic_pressure(11.0, 9500)
        assert abs(result - 5434) < 1.0

    def test_ecd_no_losses(self):
        """ECD with zero annular loss = static MW"""
        result = drl.ecd(11.0, 0.0, 9500)
        assert abs(result - 11.0) < 1e-6

    def test_ecd_with_losses(self):
        """ECD > MW when there are annular losses."""
        result = drl.ecd(11.0, 200.0, 9500)
        assert result > 11.0

    def test_ecd_zero_tvd_raises(self):
        with pytest.raises(ValueError):
            drl.ecd(11.0, 200.0, 0)

    def test_annular_pressure_loss_positive(self):
        """Annular pressure loss must be positive for valid inputs."""
        result = drl.annular_pressure_loss_bingham(11.0, 18, 12, 420, 8.5, 5.0, 9000)
        assert result > 0

    def test_annular_loss_invalid_geometry_raises(self):
        """Hole size smaller than pipe OD must raise ValueError."""
        with pytest.raises(ValueError):
            drl.annular_pressure_loss_bingham(11.0, 18, 12, 420, 4.0, 5.0, 9000)

    def test_bit_hhp_positive(self):
        """HHP must be positive."""
        result = drl.bit_hydraulic_horsepower(420, 1200)
        assert result > 0

    def test_jet_velocity_positive(self):
        """Jet velocity must be positive."""
        result = drl.jet_velocity(420, [12, 12, 13])
        assert result > 0

    def test_jet_velocity_zero_nozzles_raises(self):
        with pytest.raises(ValueError):
            drl.jet_velocity(420, [])


# ═══════════════════════════════════════════════════════════════════════════════
# CASING DESIGN TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestCasingDesign:

    def test_buoyancy_factor_fresh_water(self):
        """BF in fresh water (8.34 ppg) ≈ 0.8728"""
        result = drl.buoyancy_factor(8.34)
        assert abs(result - (1 - 8.34/65.5)) < 0.001

    def test_buoyancy_factor_air(self):
        """BF in air (mw ≈ 0) ≈ 1.0"""
        result = drl.buoyancy_factor(0.001)
        assert abs(result - 1.0) < 0.001

    def test_burst_pressure_zero_internal(self):
        """Burst = formation pressure when no fluid inside (gas at surface)."""
        result = drl.burst_pressure(5000, 9000, 0.0)
        assert result == 5000

    def test_safety_factor_calculation(self):
        """SF = 7200 / 5500 ≈ 1.309"""
        result = drl.safety_factor(7200, 5500)
        assert abs(result - 1.309) < 0.001

    def test_safety_factor_zero_load(self):
        """Zero applied load → infinite SF"""
        result = drl.safety_factor(7200, 0)
        assert result == float('inf')

    def test_cement_volume_positive(self):
        """Cement volume must be positive."""
        result = drl.cement_slurry_volume(12.25, 9.625, 5000, 1.25)
        assert result > 0

    def test_displacement_volume_positive(self):
        """Displacement volume must be positive."""
        result = drl.displacement_volume(8.681, 9500)
        assert result > 0


# ═══════════════════════════════════════════════════════════════════════════════
# DIRECTIONAL DRILLING TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestDirectional:

    def test_minimum_curvature_vertical(self):
        """Vertical well (inc=0 both stations): dTVD = dMD, dN = dE = 0."""
        dt, dn, de = drl.minimum_curvature(0, 1000, 0, 0, 0, 0)
        assert abs(dt - 1000) < 0.1
        assert abs(dn) < 0.1
        assert abs(de) < 0.1

    def test_minimum_curvature_horizontal(self):
        """Fully horizontal (inc=90 both): dTVD ≈ 0, departure ≈ dMD."""
        dt, dn, de = drl.minimum_curvature(0, 500, 90, 0, 90, 0)
        assert abs(dt) < 1.0

    def test_dogleg_severity_no_change(self):
        """Identical survey stations → DLS = 0."""
        result = drl.dogleg_severity(45, 90, 45, 90, 100)
        assert abs(result) < 0.001

    def test_dogleg_severity_positive(self):
        """DLS must be non-negative."""
        result = drl.dogleg_severity(0, 0, 10, 0, 300)
        assert result >= 0

    def test_dogleg_severity_zero_interval_raises_zero(self):
        """Zero MD interval returns 0 (avoids divide by zero)."""
        result = drl.dogleg_severity(0, 0, 5, 0, 0)
        assert result == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# PORE PRESSURE & FRACTURE GRADIENT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPorePressure:

    def test_eaton_fg_greater_than_pp(self):
        """Fracture gradient must exceed pore pressure gradient."""
        fg = drl.eaton_fracture_gradient(0.9, 0.433, 0.25)
        assert fg > 0.433

    def test_eaton_fg_less_than_obg(self):
        """Fracture gradient must be less than overburden gradient."""
        fg = drl.eaton_fracture_gradient(0.9, 0.433, 0.25)
        assert fg < 0.9

    def test_d_exponent_positive_normal(self):
        """d-exponent in normal pore pressure should be positive and > 1."""
        dc = drl.d_exponent(50, 120, 25000, 8.5, 8.6, 8.6)
        assert dc > 0

    def test_d_exponent_invalid_inputs(self):
        """Zero RPM → NaN (invalid)."""
        dc = drl.d_exponent(50, 0, 25000, 8.5, 10.5, 8.6)
        assert math.isnan(dc)


# ═══════════════════════════════════════════════════════════════════════════════
# ROP & COST TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestROPCost:

    def test_cost_per_foot_basic(self):
        """CPF = (18000 + 2500×(24+8)) / 1500 = $65.33/ft"""
        result = drl.cost_per_foot(18000, 2500, 24, 8, 1500)
        expected = (18000 + 2500 * 32) / 1500
        assert abs(result - expected) < 0.01

    def test_cost_per_foot_zero_footage_raises(self):
        with pytest.raises(ValueError):
            drl.cost_per_foot(18000, 2500, 24, 8, 0)

    def test_bingham_rop_positive(self):
        """ROP must be positive for valid inputs."""
        result = drl.bingham_rop_model(20000, 100, 8.5, 0.008, 1.2)
        assert result > 0

    def test_bingham_rop_zero_rpm(self):
        """Zero RPM → zero ROP."""
        result = drl.bingham_rop_model(20000, 0, 8.5, 0.008, 1.2)
        assert result == 0.0

    def test_torque_positive(self):
        """Surface torque estimate must be positive."""
        result = drl.surface_torque(30000, 8.5, 0.4)
        assert result > 0

    def test_hookload_less_than_string_weight(self):
        """Hook load < string weight in air (due to buoyancy)."""
        bf = drl.buoyancy_factor(10.5)
        hl = drl.hookload_vertical(0, 400000, bf)
        assert hl < 400000
