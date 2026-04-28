# Drilling Engineering Toolkit

> A production-grade Python library and interactive dashboard for drilling engineering calculations.
> Built as a portfolio project targeting ExxonMobil, TotalEnergies, Pertamina, and major IOCs.

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/built%20with-Streamlit-red.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

This repository implements **six core drilling engineering modules** based on industry-standard references:

| Module | Key Calculations |
|--------|-----------------|
| Well Control | Kill mud weight, ICP/FCP, pressure schedule (W&W, Driller's) |
| Hydraulics & ECD | Annular pressure loss (Bingham), ECD, jet velocity, impact force |
| Casing Design | Burst, collapse, tension loads; safety factors; pressure profiles |
| Directional Drilling | Minimum curvature survey, DLS, 3D trajectory |
| Pore Pressure & FG | Eaton (1969) fracture gradient, d-exponent, MW window |
| ROP & Cost Analysis | Bingham ROP model, cost-per-foot optimization |

---

## Repository Structure

```
drilling_engineering/
├── src/
│   └── drilling.py          # Core calculations module (fully documented)
├── app.py                   # Streamlit  dashboard
├── notebooks/
│   └── drilling_examples.ipynb  # Worked examples with plots
├── tests/
│   └── test_drilling.py     # 30+ unit tests (pytest)
├── data/                    # Sample datasets (offset well data)
├── docs/                    # Additional documentation
├── requirements.txt
└── README.md
```

---


```

### 1. Run the dashboard

```bash
streamlit run app.py
```

### 2. Use the library directly

```python
from src.drilling import kill_mud_weight, ecd, dogleg_severity

# Well control: kill mud weight
kmw = kill_mud_weight(mw_ppg=10.5, sidpp_psi=350, tvd_ft=9500)
print(f"Kill mud weight: {kmw:.2f} ppg")

# Hydraulics: ECD
ecd_val = ecd(mw_ppg=11.0, ann_pressure_loss_psi=420, tvd_ft=9500)
print(f"ECD: {ecd_val:.3f} ppg")

# Directional: dogleg severity
dls = dogleg_severity(inc1_deg=30, azi1_deg=45, inc2_deg=45, azi2_deg=60, delta_md_ft=300)
print(f"DLS: {dls:.2f} °/100ft")
```

### 3. Run tests

```bash
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

### 4. Explore the notebook

```bash
jupyter lab notebooks/drilling_examples.ipynb
```

---

## Dashboard Modules

### Well Control
- Shut-in data analysis (SIDPP, SICP, pit gain)
- Kill mud weight (Driller's Method & Wait and Weight)
- ICP / FCP calculation
- Formation pressure identification
- Influx type estimation (gas / oil / saltwater)
- W&W pressure schedule chart

### Hydraulics & ECD
- Annular pressure loss — Bingham Plastic model (DC + DP sections)
- Equivalent Circulating Density (ECD)
- Bit hydraulic horsepower (HHP)
- Nozzle jet velocity & impact force
- Critical flow rate (laminar/turbulent transition)
- ECD sensitivity plot (flow rate sweep)

### Casing Design
- Net burst pressure (formation vs internal fluid)
- Net collapse pressure (external vs evacuated string)
- Tension load with buoyancy and overpull
- Safety factor analysis (burst SF ≥ 1.1 | collapse ≥ 1.0 | tension ≥ 1.6)
- Depth vs pressure profile (PP, hydrostatic, fracture gradient)

### Directional Drilling
- Minimum Curvature Method survey computation
- Dogleg severity (DLS) per survey interval
- 3D well trajectory visualization (interactive Plotly)
- Interactive survey editor (add/edit stations)

### Pore Pressure & Fracture Gradient
- Eaton (1969) fracture gradient model
- Normal / abnormal pore pressure profile
- Mud weight operating window (PP + margin → FG - margin)
- Corrected d-exponent calculator for pore pressure detection

### ROP & Cost Analysis
- Bingham simplified ROP model with calibration constants a1, a2
- Classic cost-per-foot (CPF) formula
- WOB sensitivity analysis — ROP vs CPF dual-axis chart
- Optimal WOB identification

---

## Engineering Methods

### Well Control
```
KMW  = MW + SIDPP / (0.052 × TVD)
ICP  = SIDPP + SCR_pressure
FCP  = SCR_pressure × (KMW / MW_original)
Pf   = 0.052 × MW × TVD + SIDPP
```

### Hydraulics (Bingham Plastic)
```
P_ann = (PV × v)/(300 × d_ann) + YP/(225 × d_ann)  [psi/ft]
ECD   = MW + P_ann / (0.052 × TVD)
v_jet = Q / (0.32 × A_nozzle)
HHP   = Q × ΔP / 1714
```

### Directional (Minimum Curvature)
```
DL = arccos[cos(I₂-I₁) - sin(I₁)·sin(I₂)·(1-cos(A₂-A₁))]
RF = (2/DL) × tan(DL/2)
ΔTVD = (ΔMD/2) × (cos I₁ + cos I₂) × RF
```

### Fracture Gradient (Eaton, 1969)
```
FG = [ν/(1-ν)] × (OBG - PP) + PP
```
