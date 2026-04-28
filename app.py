"""
app.py — Drilling Engineering Dashboard
========================================
Interactive Streamlit application for drilling engineering calculations.
Covers well control, hydraulics, casing design, directional drilling, and pore pressure.

Run:
    streamlit run app.py
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import drilling as drl

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Drilling Engineering Toolkit",
    page_icon="🔩",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Syne:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.main { background: #f9fafb; }
div[data-testid="stSidebar"] { background: #0f172a; }
div[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
div[data-testid="stSidebar"] label { color: #94a3b8 !important; }
div[data-testid="stSidebar"] .stMarkdown p { color: #64748b !important; font-size:11px; }
div[data-testid="stSidebar"] h2, div[data-testid="stSidebar"] h3 { color: #f1f5f9 !important; }

.module-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.15em;
    color: #64748b; border-bottom: 1px solid #e2e8f0;
    padding-bottom: 8px; margin-bottom: 14px;
}
.result-card {
    background: white; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 16px 20px; margin-bottom: 10px;
}
.result-label {
    font-size: 10px; font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: #94a3b8; margin-bottom: 4px;
}
.result-value {
    font-size: 26px; font-weight: 600;
    font-family: 'JetBrains Mono', monospace; color: #0f172a;
}
.result-unit { font-size: 13px; color: #64748b; margin-left: 4px; }
.result-ok  { color: #16a34a; }
.result-warn { color: #d97706; }
.result-bad  { color: #dc2626; }

.ref-box {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-left: 3px solid #3b82f6; border-radius: 6px;
    padding: 10px 14px; font-size: 12px; color: #475569;
    font-family: 'JetBrains Mono', monospace; margin-top: 12px;
}
</style>
""", unsafe_allow_html=True)


# ── Sidebar navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔩 Drilling Toolkit")
    st.markdown("*Petroleum Engineering Portfolio*")
    st.markdown("---")
    module = st.selectbox("Select Module", [
        "Well Control",
        "Hydraulics & ECD",
        "Casing Design",
        "Directional Drilling",
        "Pore Pressure & FG",
        "ROP & Cost Analysis",
    ])
    st.markdown("---")
    st.markdown("**Reference standards**")
    st.markdown("• Bourgoyne et al. (1986)\n• Mitchell & Miska (2011)\n• Eaton (1969)\n• API RP 65-2")


# ════════════════════════════════════════════════════════════════════════════════
# MODULE 1 — WELL CONTROL
# ════════════════════════════════════════════════════════════════════════════════
if module == "Well Control":
    st.markdown("# Well Control Calculator")
    st.markdown("*Kill mud weight · Circulating pressures · Influx type identification*")
    st.markdown("---")

    col_in, col_res = st.columns([1, 1])

    with col_in:
        st.markdown('<div class="module-header">Shut-in Data</div>', unsafe_allow_html=True)
        mw = st.number_input("Current mud weight (ppg)", value=10.5, step=0.1)
        sidpp = st.number_input("SIDPP (psi)", value=350, step=10)
        sicp = st.number_input("SICP (psi)", value=580, step=10)
        tvd = st.number_input("TVD — kick zone (ft)", value=9500, step=100)
        pit_gain = st.number_input("Pit gain (bbl)", value=12.0, step=0.5)
        spp_scr = st.number_input("Slow pump pressure (psi)", value=650, step=10)
        ann_cap = st.number_input("Annular capacity (bbl/ft)", value=0.0775, step=0.001, format="%.4f")
        dp_cap  = st.number_input("Drill pipe capacity (bbl/ft)", value=0.01776, step=0.001, format="%.5f")

    with col_res:
        st.markdown('<div class="module-header">Calculated Results</div>', unsafe_allow_html=True)

        kmw = drl.kill_mud_weight(mw, sidpp, tvd)
        icp = drl.initial_circulating_pressure(sidpp, spp_scr)
        fcp = drl.final_circulating_pressure(spp_scr, kmw, mw)
        fp  = drl.formation_pressure(mw, tvd, sidpp)
        influx = drl.influx_type(mw, sicp, sidpp, ann_cap, pit_gain)
        influx_h = pit_gain / ann_cap if ann_cap > 0 else 0

        c1, c2 = st.columns(2)
        with c1:
            st.metric("Kill Mud Weight", f"{kmw:.2f} ppg", f"+{kmw-mw:.2f} ppg over current")
            st.metric("Formation Pressure", f"{fp:,.0f} psi",
                      f"{fp/tvd/0.052:.2f} ppg equivalent")
            st.metric("Influx Type", influx.upper(), f"{influx_h:.1f} ft column")
        with c2:
            st.metric("ICP (Driller's)", f"{icp:,.0f} psi")
            st.metric("FCP (W&W)", f"{fcp:,.0f} psi")
            st.metric("Pressure ramp", f"{(icp-fcp):.0f} psi", "ICP → FCP reduction")

        st.markdown('<div class="ref-box">Kill Method: Driller\'s / Wait & Weight<br>'
                    'ICP = SIDPP + SCR_pressure<br>'
                    'KMW = MW + SIDPP / (0.052 × TVD)<br>'
                    'Ref: Bourgoyne et al. (1986) Ch.4</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Drill pipe pressure schedule (Wait & Weight Method)**")

    dp_vol   = dp_cap * tvd
    strokes  = np.arange(0, int(dp_vol / 0.1) + 1, 10)
    p_sched  = np.linspace(icp, fcp, len(strokes))
    df_sched = pd.DataFrame({"Strokes": strokes, "SIDPP Target (psi)": p_sched.round(0)})

    fig_sched = go.Figure()
    fig_sched.add_trace(go.Scatter(x=strokes, y=p_sched, mode='lines+markers',
                                    line=dict(color='#1d4ed8', width=2),
                                    marker=dict(size=4), name='SIDPP target'))
    fig_sched.add_hline(y=icp, line_dash='dot', line_color='#dc2626',
                         annotation_text='ICP', annotation_position='right')
    fig_sched.add_hline(y=fcp, line_dash='dot', line_color='#16a34a',
                         annotation_text='FCP', annotation_position='right')
    fig_sched.update_layout(template='plotly_white', height=300,
                             xaxis_title='Strokes', yaxis_title='Drill Pipe Pressure (psi)',
                             margin=dict(t=20, b=40, l=60, r=60),
                             legend=dict(orientation='h', y=1.05))
    st.plotly_chart(fig_sched, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# MODULE 2 — HYDRAULICS & ECD
# ════════════════════════════════════════════════════════════════════════════════
elif module == "Hydraulics & ECD":
    st.markdown("# Hydraulics & ECD")
    st.markdown("*Annular pressure loss · ECD · Bit hydraulics · Jet velocity*")
    st.markdown("---")

    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.markdown('<div class="module-header">Fluid & Geometry</div>', unsafe_allow_html=True)
        mw_h   = st.number_input("Mud weight (ppg)", value=11.0, step=0.1)
        pv_h   = st.number_input("Plastic viscosity (cP)", value=18, step=1)
        yp_h   = st.number_input("Yield point (lbf/100 sq ft)", value=12, step=1)
        q_h    = st.number_input("Flow rate (gpm)", value=420, step=10)
        hole_h = st.number_input("Hole size (in)", value=8.5, step=0.25)
        dp_od  = st.number_input("Drill pipe OD (in)", value=5.0, step=0.125)
        dc_od  = st.number_input("Drill collar OD (in)", value=6.5, step=0.125)
        dc_len = st.number_input("Drill collar length (ft)", value=600, step=50)
        dp_len = st.number_input("Drill pipe length (ft)", value=9000, step=100)
        tvd_h  = st.number_input("TVD (ft)", value=9500, step=100)
        nozzles_str = st.text_input("Nozzle sizes (1/32 in, comma-separated)", value="12,12,13")

    with c_right:
        st.markdown('<div class="module-header">Hydraulic Results</div>', unsafe_allow_html=True)
        try:
            nozzles = [float(x.strip()) for x in nozzles_str.split(',')]
            ann_loss_dc = drl.annular_pressure_loss_bingham(mw_h, pv_h, yp_h, q_h, hole_h, dc_od, dc_len)
            ann_loss_dp = drl.annular_pressure_loss_bingham(mw_h, pv_h, yp_h, q_h, hole_h, dp_od, dp_len)
            total_ann   = ann_loss_dc + ann_loss_dp
            ecd_val     = drl.ecd(mw_h, total_ann, tvd_h)
            jv          = drl.jet_velocity(q_h, nozzles)
            bit_dp      = drl.impact_force(mw_h, q_h, jv)
            hhp         = drl.bit_hydraulic_horsepower(q_h, total_ann * 0.3)
            qcrit       = drl.critical_flow_rate(mw_h, pv_h, yp_h, hole_h, dp_od)

            c1, c2 = st.columns(2)
            with c1:
                st.metric("ECD", f"{ecd_val:.2f} ppg",
                          f"+{ecd_val-mw_h:.2f} ppg above static MW")
                st.metric("Ann. loss (total)", f"{total_ann:.0f} psi",
                          f"DC: {ann_loss_dc:.0f} | DP: {ann_loss_dp:.0f} psi")
                st.metric("Jet velocity", f"{jv:.0f} ft/s")
            with c2:
                st.metric("Bit impact force", f"{bit_dp:.0f} lbf")
                st.metric("Bit HHP", f"{hhp:.0f} HP")
                st.metric("Critical flow rate", f"{qcrit:.0f} gpm",
                          "laminar ↔ turbulent threshold")
        except Exception as e:
            st.error(f"Calculation error: {e}")

    st.markdown("---")
    st.markdown("**ECD sensitivity — flow rate vs ECD**")
    q_range = np.arange(100, 700, 20)
    ecd_curve = []
    for q_ in q_range:
        al_dc = drl.annular_pressure_loss_bingham(mw_h, pv_h, yp_h, q_, hole_h, dc_od, dc_len)
        al_dp = drl.annular_pressure_loss_bingham(mw_h, pv_h, yp_h, q_, hole_h, dp_od, dp_len)
        ecd_curve.append(drl.ecd(mw_h, al_dc + al_dp, tvd_h))

    fig_ecd = go.Figure()
    fig_ecd.add_trace(go.Scatter(x=q_range, y=ecd_curve, mode='lines',
                                  line=dict(color='#7c3aed', width=2.5), name='ECD'))
    fig_ecd.add_hline(y=mw_h, line_dash='dot', line_color='#3b82f6',
                       annotation_text=f'Static MW = {mw_h} ppg', annotation_position='right')
    fig_ecd.add_vline(x=q_h, line_dash='dash', line_color='#dc2626',
                       annotation_text=f'Q = {q_h} gpm', annotation_position='top')
    fig_ecd.update_layout(template='plotly_white', height=280,
                           xaxis_title='Flow Rate (gpm)', yaxis_title='ECD (ppg)',
                           margin=dict(t=20, b=40, l=60, r=80))
    st.plotly_chart(fig_ecd, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# MODULE 3 — CASING DESIGN
# ════════════════════════════════════════════════════════════════════════════════
elif module == "Casing Design":
    st.markdown("# Casing Design")
    st.markdown("*Burst · Collapse · Tension · Safety factors*")
    st.markdown("---")

    c_left, c_right = st.columns([1, 1])
    with c_left:
        st.markdown('<div class="module-header">Well & Casing Parameters</div>', unsafe_allow_html=True)
        tvd_c    = st.number_input("Casing shoe TVD (ft)", value=10000, step=100)
        mw_c     = st.number_input("Mud weight (ppg)", value=12.0, step=0.1)
        pore_c   = st.number_input("Formation pressure (psi)", value=5980, step=50)
        w_str    = st.number_input("Casing string air weight (lbf)", value=450000, step=5000)
        overpull = st.number_input("Overpull during running (lbf)", value=50000, step=1000)
        st.markdown("---")
        st.markdown('<div class="module-header">Rated Capacities</div>', unsafe_allow_html=True)
        burst_rated   = st.number_input("Casing burst rating (psi)", value=7200, step=100)
        collapse_rated= st.number_input("Casing collapse rating (psi)", value=5140, step=100)
        tension_rated = st.number_input("Casing tension rating (lbf)", value=1_050_000, step=10000)

    with c_right:
        st.markdown('<div class="module-header">Load & Safety Factor Analysis</div>', unsafe_allow_html=True)

        bf   = drl.buoyancy_factor(mw_c)
        p_burst   = drl.burst_pressure(pore_c, tvd_c, 0.0)   # gas kick inside = 0
        p_collapse= drl.collapse_pressure(mw_c, tvd_c, 0.0)  # evacuated inside
        p_tension = drl.tension_load(w_str, bf, overpull)

        sf_burst   = drl.safety_factor(burst_rated, p_burst)
        sf_collapse= drl.safety_factor(collapse_rated, p_collapse)
        sf_tension = drl.safety_factor(tension_rated, p_tension)

        def sf_color(sf, min_sf=1.1):
            return "result-ok" if sf >= min_sf * 1.05 else "result-warn" if sf >= min_sf else "result-bad"

        for label, applied, rated, sf, unit in [
            ("Burst",   p_burst,   burst_rated,    sf_burst,   "psi"),
            ("Collapse",p_collapse,collapse_rated, sf_collapse,"psi"),
            ("Tension", p_tension, tension_rated,  sf_tension, "lbf"),
        ]:
            cls = sf_color(sf)
            st.markdown(
                f'<div class="result-card">'
                f'<div class="result-label">{label}</div>'
                f'<div class="result-value">{applied:,.0f}<span class="result-unit">{unit}</span></div>'
                f'<div style="font-size:12px;color:#64748b;margin-top:4px">'
                f'Rated: {rated:,.0f} {unit} &nbsp;|&nbsp; '
                f'<span class="{cls}">SF = {sf:.2f}</span></div>'
                f'</div>', unsafe_allow_html=True
            )
        st.metric("Buoyancy Factor", f"{bf:.4f}", f"MW = {mw_c} ppg")

    st.markdown("---")
    st.markdown("**Pressure profile vs depth**")
    depths = np.linspace(0, tvd_c, 200)
    p_pore_prof    = pore_c * depths / tvd_c
    p_hydro_prof   = drl.hydrostatic_pressure(mw_c, depths)
    p_frac_prof    = np.array([
        drl.eaton_fracture_gradient(0.9 * pore_c / tvd_c, pore_c / tvd_c) * d
        for d in depths
    ])

    fig_pres = go.Figure()
    fig_pres.add_trace(go.Scatter(x=p_pore_prof, y=depths, name='Pore pressure',
                                   line=dict(color='#dc2626', width=2), mode='lines'))
    fig_pres.add_trace(go.Scatter(x=p_hydro_prof, y=depths, name='Hydrostatic (MW)',
                                   line=dict(color='#2563eb', width=2), mode='lines'))
    fig_pres.add_trace(go.Scatter(x=p_frac_prof, y=depths, name='Fracture gradient',
                                   line=dict(color='#16a34a', width=2, dash='dash'), mode='lines'))
    fig_pres.update_layout(template='plotly_white', height=380,
                            xaxis_title='Pressure (psi)', yaxis_title='TVD (ft)',
                            yaxis_autorange='reversed',
                            legend=dict(orientation='h', y=1.08, x=0),
                            margin=dict(t=40, b=40, l=60, r=20))
    st.plotly_chart(fig_pres, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# MODULE 4 — DIRECTIONAL DRILLING
# ════════════════════════════════════════════════════════════════════════════════
elif module == "Directional Drilling":
    st.markdown("# Directional Drilling Survey")
    st.markdown("*Minimum curvature method · Dogleg severity · 3D well trajectory*")
    st.markdown("---")

    c_left, c_right = st.columns([1, 1])
    with c_left:
        st.markdown('<div class="module-header">Survey Stations</div>', unsafe_allow_html=True)
        df_survey_input = pd.DataFrame({
            'MD (ft)':  [0, 2000, 4000, 5500, 7000, 8500, 10000, 11500],
            'Inc (°)':  [0, 0,    15,   35,   55,   75,   89,    90],
            'Azi (°)':  [0, 0,    45,   45,   45,   45,   45,    45],
        })
        df_edit = st.data_editor(df_survey_input, use_container_width=True, num_rows="dynamic")

    with c_right:
        st.markdown('<div class="module-header">Survey Results</div>', unsafe_allow_html=True)
        try:
            mds  = df_edit['MD (ft)'].values.astype(float)
            incs = df_edit['Inc (°)'].values.astype(float)
            azis = df_edit['Azi (°)'].values.astype(float)

            tvds = [0.0]; norths = [0.0]; easts = [0.0]; dls_list = [0.0]
            for i in range(1, len(mds)):
                dt, dn, de = drl.minimum_curvature(mds[i-1], mds[i], incs[i-1], azis[i-1], incs[i], azis[i])
                tvds.append(tvds[-1] + dt)
                norths.append(norths[-1] + dn)
                easts.append(easts[-1] + de)
                dls = drl.dogleg_severity(incs[i-1], azis[i-1], incs[i], azis[i], mds[i]-mds[i-1])
                dls_list.append(dls)

            df_results = pd.DataFrame({
                'MD (ft)':    mds.round(0),
                'Inc (°)':    incs.round(2),
                'Azi (°)':    azis.round(2),
                'TVD (ft)':   [round(x, 1) for x in tvds],
                'N/S (ft)':   [round(x, 1) for x in norths],
                'E/W (ft)':   [round(x, 1) for x in easts],
                'DLS (°/100ft)': [round(x, 2) for x in dls_list],
            })
            st.dataframe(df_results, use_container_width=True, hide_index=True)

            departure = math.sqrt(norths[-1]**2 + easts[-1]**2)
            c1, c2, c3 = st.columns(3)
            c1.metric("Final TVD", f"{tvds[-1]:,.0f} ft")
            c2.metric("Total departure", f"{departure:,.0f} ft")
            c3.metric("Max DLS", f"{max(dls_list):.2f} °/100ft")
        except Exception as e:
            st.error(f"Survey calculation error: {e}")

    st.markdown("---")
    st.markdown("**3D Well Trajectory**")
    try:
        fig_3d = go.Figure(data=[go.Scatter3d(
            x=easts, y=norths, z=[-t for t in tvds],
            mode='lines+markers',
            line=dict(color=[t for t in tvds], colorscale='Blues', width=5),
            marker=dict(size=4, color=[t for t in tvds], colorscale='Blues',
                        colorbar=dict(title='TVD (ft)', thickness=12, len=0.5)),
            name='Well path'
        )])
        fig_3d.update_layout(
            scene=dict(
                xaxis_title='East (ft)', yaxis_title='North (ft)', zaxis_title='TVD (ft)',
                zaxis=dict(autorange='reversed'),
                bgcolor='#f8fafc',
            ),
            height=480, margin=dict(t=20, b=10, l=0, r=0),
            paper_bgcolor='white'
        )
        st.plotly_chart(fig_3d, use_container_width=True)
    except Exception as e:
        st.error(f"Plot error: {e}")


# ════════════════════════════════════════════════════════════════════════════════
# MODULE 5 — PORE PRESSURE & FRACTURE GRADIENT
# ════════════════════════════════════════════════════════════════════════════════
elif module == "Pore Pressure & FG":
    st.markdown("# Pore Pressure & Fracture Gradient")
    st.markdown("*Eaton (1969) fracture gradient · d-exponent · Mud weight window*")
    st.markdown("---")

    c_left, c_right = st.columns([1, 1])
    with c_left:
        st.markdown('<div class="module-header">Formation Parameters</div>', unsafe_allow_html=True)
        depths_pp = np.arange(1000, 14000, 500)
        obg = st.slider("Overburden gradient (psi/ft)", 0.80, 1.10, 0.95, 0.01)
        nu  = st.slider("Poisson's ratio", 0.15, 0.45, 0.25, 0.01)
        pp_grad_normal = st.number_input("Normal pore pressure gradient (psi/ft)", value=0.433, step=0.001, format="%.3f")

        pp_grads = pp_grad_normal * np.ones_like(depths_pp, dtype=float)
        pp_grads[depths_pp > 8000] = pp_grad_normal * 1.18
        pp_grads[depths_pp > 11000] = pp_grad_normal * 1.32

        fg_grads = np.array([drl.eaton_fracture_gradient(obg, ppg, nu) for ppg in pp_grads])
        mw_window_lo = pp_grads + 0.05
        mw_window_hi = fg_grads - 0.05

    with c_right:
        st.markdown('<div class="module-header">D-Exponent Calculator</div>', unsafe_allow_html=True)
        rop_d  = st.number_input("ROP (ft/hr)", value=45.0, step=1.0)
        rpm_d  = st.number_input("RPM", value=120, step=5)
        wob_d  = st.number_input("WOB (klbf)", value=25.0, step=1.0)
        bs_d   = st.number_input("Bit size (in)", value=8.5, step=0.25)
        mw_act = st.number_input("Actual mud weight (ppg)", value=10.5, step=0.1)
        mw_norm= st.number_input("Normal mud weight (ppg)", value=8.6, step=0.1)

        dc_exp = drl.d_exponent(rop_d, rpm_d, wob_d * 1000, bs_d, mw_act, mw_norm)
        trend  = "Normal (near trend → low pore pressure)" if dc_exp > 1.5 else \
                 "Decreasing trend → ELEVATED pore pressure"
        st.metric("Corrected d-exponent", f"{dc_exp:.3f}" if not math.isnan(dc_exp) else "N/A")
        st.info(trend)

    st.markdown("---")
    st.markdown("**Pore pressure window — mud weight envelope**")
    fig_pp = go.Figure()
    fig_pp.add_trace(go.Scatter(x=pp_grads * depths_pp, y=depths_pp, name='Pore pressure',
                                 line=dict(color='#dc2626', width=2.5), mode='lines'))
    fig_pp.add_trace(go.Scatter(x=fg_grads * depths_pp, y=depths_pp, name='Fracture gradient',
                                 line=dict(color='#16a34a', width=2.5), mode='lines'))
    fig_pp.add_trace(go.Scatter(x=mw_window_lo * depths_pp, y=depths_pp, name='Min safe MW',
                                 line=dict(color='#f59e0b', width=1.5, dash='dash'), mode='lines'))
    fig_pp.add_trace(go.Scatter(x=mw_window_hi * depths_pp, y=depths_pp, name='Max safe MW',
                                 line=dict(color='#f59e0b', width=1.5, dash='dot'), mode='lines'))
    fig_pp.update_layout(template='plotly_white', height=420, yaxis_autorange='reversed',
                          xaxis_title='Pressure (psi)', yaxis_title='Depth (ft)',
                          legend=dict(orientation='h', y=1.06),
                          margin=dict(t=40, b=40, l=60, r=20))
    st.plotly_chart(fig_pp, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# MODULE 6 — ROP & COST ANALYSIS
# ════════════════════════════════════════════════════════════════════════════════
elif module == "ROP & Cost Analysis":
    st.markdown("# ROP Optimization & Cost Analysis")
    st.markdown("*Bingham ROP model · Cost per foot · Bit run optimization*")
    st.markdown("---")

    c_left, c_right = st.columns([1, 1])
    with c_left:
        st.markdown('<div class="module-header">Bit Run Parameters</div>', unsafe_allow_html=True)
        bit_cost  = st.number_input("Bit cost (USD)", value=18000, step=500)
        rig_rate  = st.number_input("Rig rate (USD/hr)", value=2500, step=100)
        trip_time = st.number_input("Trip time (hr)", value=8.0, step=0.5)
        footage   = st.number_input("Footage drilled (ft)", value=1500, step=50)
        drill_hr  = st.number_input("Drilling time (hr)", value=24.0, step=0.5)
        wob_r     = st.number_input("WOB (klbf)", value=20.0, step=1.0)
        rpm_r     = st.number_input("RPM", value=100, step=5)
        bs_r      = st.number_input("Bit size (in)", value=12.25, step=0.25)
        a1_r      = st.number_input("ROP model a1 (calibrate)", value=0.008, step=0.001, format="%.4f")
        a2_r      = st.number_input("ROP model a2 (calibrate)", value=1.2, step=0.05)

    with c_right:
        st.markdown('<div class="module-header">Economics Results</div>', unsafe_allow_html=True)
        cpf = drl.cost_per_foot(bit_cost, rig_rate, drill_hr, trip_time, footage)
        rop_pred = drl.bingham_rop_model(wob_r * 1000, rpm_r, bs_r, a1_r, a2_r)
        actual_rop = footage / drill_hr if drill_hr > 0 else 0

        st.metric("Cost per foot", f"${cpf:,.2f}/ft",
                  f"Total: ${bit_cost + rig_rate*(drill_hr+trip_time):,.0f}")
        st.metric("Predicted ROP", f"{rop_pred:.1f} ft/hr")
        st.metric("Actual ROP", f"{actual_rop:.1f} ft/hr",
                  f"{actual_rop-rop_pred:+.1f} ft/hr vs model")

    st.markdown("---")
    st.markdown("**WOB vs ROP sensitivity — Cost per foot optimization**")
    wob_range = np.arange(5, 60, 2)
    rop_curve = [drl.bingham_rop_model(w*1000, rpm_r, bs_r, a1_r, a2_r) for w in wob_range]
    cpf_curve = []
    for rop_i in rop_curve:
        dt = footage / rop_i if rop_i > 0 else 9999
        cpf_i = drl.cost_per_foot(bit_cost, rig_rate, dt, trip_time, footage)
        cpf_curve.append(cpf_i)

    best_idx = np.argmin(cpf_curve)

    fig_rop = make_subplots(specs=[[{"secondary_y": True}]])
    fig_rop.add_trace(go.Scatter(x=wob_range, y=rop_curve, mode='lines',
                                  name='ROP (ft/hr)', line=dict(color='#3b82f6', width=2)),
                      secondary_y=False)
    fig_rop.add_trace(go.Scatter(x=wob_range, y=cpf_curve, mode='lines',
                                  name='CPF ($/ft)', line=dict(color='#dc2626', width=2)),
                      secondary_y=True)
    fig_rop.add_vline(x=wob_range[best_idx], line_dash='dash', line_color='#16a34a',
                       annotation_text=f'Optimal WOB: {wob_range[best_idx]} klbf',
                       annotation_position='top')
    fig_rop.update_layout(template='plotly_white', height=320,
                           xaxis_title='WOB (klbf)',
                           legend=dict(orientation='h', y=1.08),
                           margin=dict(t=40, b=40, l=60, r=60))
    fig_rop.update_yaxes(title_text="ROP (ft/hr)", secondary_y=False)
    fig_rop.update_yaxes(title_text="Cost per foot ($/ft)", secondary_y=True)
    st.plotly_chart(fig_rop, use_container_width=True)

st.markdown("---")
st.caption("Drilling Engineering Toolkit | Portfolio | "
           "Bourgoyne et al. (1986) · Mitchell & Miska (2011) · Eaton (1969) | "
           "Built with Streamlit + Plotly + petropt")
