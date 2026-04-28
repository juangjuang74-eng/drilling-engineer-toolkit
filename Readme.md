# Drilling Engineer Toolkit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)

A comprehensive, open-source Python toolkit for drilling engineers featuring interactive calculations for well control, hydraulics & ECD, casing design, directional drilling, pore pressure & fracture gradient, and ROP & cost analysis. Built with modern Python (dataclasses + type hints) and delivered via a clean Streamlit dashboard.

**Live Demo**: [ deploy to Streamlit Community Cloud]

## ✨ Features

- **Well Control Module**  
  Kill mud weight, initial/final circulating pressure (Wait & Weight method), formation pressure, influx type identification, kick tolerance, and pressure-ramp schedule charts.

- **Hydraulics & ECD**  
  Equivalent circulating density, pressure losses, hole cleaning, and bit hydraulics.

- **Casing Design**  
  Burst, collapse, and tensile calculations with safety factors.

- **Directional Drilling**  
  Survey calculations, dogleg severity, and trajectory planning.

- **Pore Pressure & Fracture Gradient**  
  Real-time estimation methods with reference-backed models.

- **ROP & Cost Analysis**  
  Rate of penetration prediction and drilling cost optimization.

- Modern, responsive Streamlit UI with dark theme, interactive plots (Plotly + Matplotlib), and color-coded result cards.
- Full unit-aware calculations and professional error handling.
- Extensible library (`src/drilling.py`) that can be imported into scripts or Jupyter notebooks.

- ## 📚 References
-  **Tanaka, S. (1968)**. A Study on the Effect of Hydraulics on the Penetration Rate of Rotary Drilling. *Journal of the Japanese Association for Petroleum Technology*, 33(3), 169–174. https://doi.org/10.3720/japt.33.169  
  *(Foundational work on hydraulics–ROP relationship used in the ROP & Cost Analysis module)*

- **Kawasaki, M., Umezu, S., & Yasuda, M. (2006)**. Pressure Temperature Core Sampler (PTCS). *Journal of the Japanese Association for Petroleum Technology*, 71(1), 139–147.  
  *(Pressure-preservation coring technology relevant to pore pressure and formation evaluation)*
