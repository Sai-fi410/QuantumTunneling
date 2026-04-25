import streamlit as st
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import subprocess
import os
import time
import io

import plotly.graph_objects as go

# ─────────────────────────────────────────────────────────────────────────────
#  Page config  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QuantumLab // TDSE Engine",
    page_icon="⚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  Strict project paths — DO NOT CHANGE
# ─────────────────────────────────────────────────────────────────────────────
EXE_PATH  = os.path.join("solver.exe")
POS_PATH  = os.path.join("core", "data", "output.csv")
MOM_PATH  = os.path.join("core", "data", "momentum.csv")

# ─────────────────────────────────────────────────────────────────────────────
#  Global CSS  — Cyber-Neon / Gilded-Tech aesthetic
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;900&family=Share+Tech+Mono&family=Exo+2:wght@300;400;600&display=swap');

:root {
    --void:       #010609;
    --panel:      #060d15;
    --card:       #091019;
    --card2:      #0b1420;
    --cyan:       #00f2ff;
    --cyan-dim:   rgba(0,242,255,0.12);
    --blue:       #0077ff;
    --gold:       #ffbe00;
    --gold-dim:   rgba(255,190,0,0.12);
    --crimson:    #ff2d55;
    --green:      #00ff9d;
    --text:       #d0e8f8;
    --muted:      #5a8aaa;
    --glow-c:     0 0 14px rgba(0,242,255,0.6), 0 0 40px rgba(0,242,255,0.18);
    --glow-g:     0 0 14px rgba(255,190,0,0.65), 0 0 40px rgba(255,190,0,0.2);
    --glow-r:     0 0 10px rgba(255,45,85,0.5);
}

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    background: var(--void) !important;
    color: var(--text) !important;
    font-family: 'Share Tech Mono', monospace !important;
}

[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background-image:
        linear-gradient(rgba(0,242,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,242,255,0.03) 1px, transparent 1px),
        linear-gradient(rgba(0,242,255,0.015) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,242,255,0.015) 1px, transparent 1px);
    background-size: 80px 80px, 80px 80px, 20px 20px, 20px 20px;
}

[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #040c16 0%, #020609 100%) !important;
    border-right: 1px solid rgba(0,242,255,0.1) !important;
}
[data-testid="stSidebar"]::after {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg,
        transparent 0%, var(--cyan) 30%, var(--gold) 70%, transparent 100%);
    animation: pulse-bar 5s ease-in-out infinite;
}
@keyframes pulse-bar {
    0%,100% { opacity: 0.5; }
    50%      { opacity: 1.0; }
}

.sb-logo {
    font-family: 'Orbitron', monospace;
    font-weight: 900;
    font-size: 1.1rem;
    letter-spacing: 0.14em;
    color: var(--cyan);
    text-shadow: var(--glow-c);
    text-transform: uppercase;
    padding-bottom: 1.1rem;
    border-bottom: 1px solid rgba(0,242,255,0.12);
    margin-bottom: 1.2rem;
    line-height: 1.5;
}
.sb-logo span { color: var(--gold); text-shadow: var(--glow-g); }

.sec-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.62rem;
    color: var(--muted);
    letter-spacing: 0.26em;
    text-transform: uppercase;
    border-left: 2px solid var(--gold);
    padding-left: 0.55rem;
    margin: 1.1rem 0 0.55rem 0;
}
.sec-label.cyan { border-left-color: var(--cyan); }

[data-testid="stSlider"] > div > div > div {
    background: var(--cyan) !important;
}
[data-testid="stSlider"] label {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.75rem !important;
    color: var(--gold) !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

[data-testid="stRadio"] label {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.72rem !important;
    color: var(--text) !important;
}
[data-testid="stRadio"] > div > div {
    gap: 0.4rem !important;
}
[data-testid="stRadio"] > div > label {
    background: var(--card2) !important;
    border: 1px solid rgba(0,242,255,0.1) !important;
    border-radius: 2px !important;
    padding: 0.35rem 0.7rem !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.68rem !important;
    color: var(--muted) !important;
    letter-spacing: 0.06em !important;
    transition: all 0.15s !important;
}
[data-testid="stRadio"] > div > label:hover {
    border-color: rgba(0,242,255,0.3) !important;
    color: var(--cyan) !important;
}
[data-testid="stRadio"] > div > label[data-checked="true"] {
    border-color: var(--cyan) !important;
    color: var(--cyan) !important;
    background: rgba(0,242,255,0.06) !important;
}

.stButton > button {
    font-family: 'Orbitron', monospace !important;
    font-weight: 700 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    color: #000 !important;
    background: linear-gradient(135deg, var(--cyan) 0%, var(--blue) 100%) !important;
    border: none !important;
    border-radius: 2px !important;
    padding: 0.7rem 1.2rem !important;
    width: 100% !important;
    box-shadow: var(--glow-c) !important;
    transition: all 0.2s !important;
    position: relative; overflow: hidden;
}
.stButton > button:hover {
    box-shadow: 0 0 28px rgba(0,242,255,0.9), 0 0 70px rgba(0,242,255,0.35) !important;
    transform: translateY(-1px) !important;
}

.page-title {
    font-family: 'Orbitron', monospace;
    font-weight: 900;
    font-size: clamp(1.3rem, 2.8vw, 2.2rem);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--cyan);
    text-shadow: var(--glow-c);
    margin-bottom: 0.1rem;
}
.page-sub {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.68rem;
    color: #6a9abb;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    margin-bottom: 0.9rem;
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 0.5rem;
    margin-bottom: 0.9rem;
}
@media (max-width: 1100px) {
    .metric-grid { grid-template-columns: repeat(3, 1fr); }
}
.mc {
    background: var(--card);
    border: 1px solid rgba(0,242,255,0.1);
    border-top: 2px solid var(--cyan);
    padding: 0.38rem 0.65rem;
    position: relative;
    overflow: hidden;
}
.mc::after {
    content: '';
    position: absolute; top: 0; right: 0;
    width: 36px; height: 36px;
    background: radial-gradient(circle at top right, rgba(0,242,255,0.1), transparent 70%);
}
.mc.gold  { border-top-color: var(--gold); }
.mc.gold::after  { background: radial-gradient(circle at top right, rgba(255,190,0,0.1), transparent 70%); }
.mc.red   { border-top-color: var(--crimson); }
.mc.red::after   { background: radial-gradient(circle at top right, rgba(255,45,85,0.1), transparent 70%); }
.mc.green { border-top-color: var(--green); }
.mc.green::after { background: radial-gradient(circle at top right, rgba(0,255,157,0.1), transparent 70%); }

.mc-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.58rem;
    color: #6a9abb;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 0.12rem;
}
.mc-val {
    font-family: 'Orbitron', monospace;
    font-weight: 700;
    font-size: 1.05rem;
    color: var(--cyan);
    text-shadow: var(--glow-c);
    line-height: 1;
    letter-spacing: 0.02em;
}
.mc.gold  .mc-val { color: var(--gold);    text-shadow: var(--glow-g); }
.mc.red   .mc-val { color: var(--crimson); text-shadow: var(--glow-r); }
.mc.green .mc-val { color: var(--green); }
.mc-unit {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.56rem;
    color: var(--muted);
    margin-top: 0.06rem;
    letter-spacing: 0.1em;
}

.status { font-family: 'Share Tech Mono', monospace; font-size: 0.68rem;
    color: var(--cyan); background: rgba(0,242,255,0.04);
    border: 1px solid rgba(0,242,255,0.12); border-left: 3px solid var(--cyan);
    padding: 0.45rem 0.9rem; margin-bottom: 0.9rem; letter-spacing: 0.06em; }
.status.err  { color: var(--crimson); border-color: rgba(255,45,85,0.2);
    border-left-color: var(--crimson); background: rgba(255,45,85,0.04); }
.status.gold { color: var(--gold);    border-color: rgba(255,190,0,0.2);
    border-left-color: var(--gold);   background: rgba(255,190,0,0.04); }
.status.ok   { color: var(--green);   border-color: rgba(0,255,157,0.2);
    border-left-color: var(--green);  background: rgba(0,255,157,0.04); }

.log-box {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.66rem;
    color: var(--muted);
    background: var(--card);
    border: 1px solid rgba(0,242,255,0.08);
    padding: 0.7rem 1rem;
    white-space: pre-wrap;
    max-height: 120px;
    overflow-y: auto;
    line-height: 1.6;
}

.chart-wrap {
    background: var(--card);
    border: 1px solid rgba(0,242,255,0.14);
    padding: 0.5rem;
    margin-bottom: 0.9rem;
}

.idle {
    border: 1px dashed rgba(0,242,255,0.12);
    background: rgba(0,242,255,0.018);
    padding: 4rem 2rem;
    text-align: center;
    margin-top: 1rem;
}
.idle-title {
    font-family: 'Orbitron', monospace;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.25em;
    color: rgba(0,242,255,0.28);
    text-transform: uppercase;
    margin-bottom: 0.7rem;
}
.idle-sub {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.68rem;
    color: #1e3a50;
    letter-spacing: 0.1em;
}

[data-testid="stDownloadButton"] button {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.1em !important;
    color: var(--gold) !important;
    background: transparent !important;
    border: 1px solid rgba(255,190,0,0.3) !important;
    border-radius: 2px !important;
    padding: 0.4rem 0.9rem !important;
}

#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] {
    background: transparent !important;
}
[data-testid="collapsedControl"] {
    visibility: visible !important;
    display: flex !important;
}
[data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Helper: Plotly base layout  (shared across all charts)
# ─────────────────────────────────────────────────────────────────────────────
PLOTLY_BASE = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(6,13,21,0.0)",
    plot_bgcolor="rgba(4,10,18,0.95)",
    font=dict(family="Share Tech Mono", color="#3a5a78", size=10),
)

def axis_style(title="", color="#3a5a78", tick_color="#3a5a78"):
    return dict(
        title=dict(text=title, font=dict(color=color, size=10)),
        gridcolor="rgba(0,119,255,0.1)",
        gridwidth=1,
        griddash="dot",
        zerolinecolor="rgba(0,242,255,0.18)",
        zerolinewidth=1,
        tickfont=dict(color=tick_color),
        showgrid=True,
        minor=dict(
            showgrid=True,
            gridcolor="rgba(0,119,255,0.04)",
            gridwidth=1,
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div class="sb-logo">
            ⚛ Quantum<span>Lab</span><br>
            <span style="font-size:0.52rem;font-weight:400;color:#2a4a68;
                         letter-spacing:0.3em;">TDSE ENGINE v3.0</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sec-label">Barrier Parameters</div>',
                unsafe_allow_html=True)
    v0    = st.slider("Potential height  V₀",  50.0,  800.0, 150.0, 5.0)
    bw    = st.slider("Barrier width  Δx",      0.5,   12.0,   5.0, 0.25)

    st.markdown('<div class="sec-label">Barrier Mode</div>',
                unsafe_allow_html=True)
    barrier_mode = st.radio(
        "Mode",
        options=[1, 2],
        format_func=lambda x: "Single barrier" if x == 1 else "Double barrier (resonant)",
        horizontal=False,
        label_visibility="collapsed",
    )

    st.markdown('<div class="sec-label cyan">Wave Packet</div>',
                unsafe_allow_html=True)
    k0    = st.slider("Wave-vector  k₀",  1.0,  12.0,  4.5, 0.25)
    sigma = st.slider("Packet width  σ",  1.0,  10.0,  4.0, 0.5)

    st.markdown('<div class="sec-label cyan">Solver</div>',
                unsafe_allow_html=True)
    n_steps = st.slider("Time steps", 100, 2000, 500, 100)

    st.markdown('<div class="sec-label cyan">Display Options</div>',
                unsafe_allow_html=True)
    show_phase    = st.checkbox("Phase portrait  Re/Im(ψ)",  value=True)
    show_energy   = st.checkbox("Energy level overlay",      value=True)
    show_momentum = st.checkbox("Momentum-space panel",      value=True)
    show_norm     = st.checkbox("Norm decay chart",          value=True)
    mom_log_scale = st.checkbox("Log scale  |φ(k)|²",       value=False)

    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("▶  RUN SIMULATION")
    params_key = (v0, bw, k0, sigma, n_steps, barrier_mode)
    if "last_run_params" not in st.session_state:
        st.session_state.last_run_params = None

    if run_btn:
        st.session_state.last_run_params = params_key

    stale = (st.session_state.last_run_params is not None and 
             st.session_state.last_run_params != params_key)

    st.markdown("""
        <div style="position:absolute;bottom:1rem;left:1.2rem;right:1.2rem;
                    font-family:'Share Tech Mono',monospace;font-size:0.55rem;
                    color:#1a3448;letter-spacing:0.12em;text-align:center;
                    border-top:1px solid #0a1e2e;padding-top:0.6rem;">
            CRANK–NICOLSON  //  CAP BOUNDARIES  //  ℏ=1  m=½
        </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
    <div class="page-title">Quantum Tunneling Simulator</div>
    <div class="page-sub">
        ▸ Time-Dependent Schrödinger Equation  //
        Crank–Nicolson + CAP  //
        Live Wavefunction &amp; Momentum Dynamics
    </div>
""", unsafe_allow_html=True)

if stale:
    st.markdown('<div class="status gold">⚠  PARAMETERS CHANGED — re-run to update results</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  RUN SOLVER
# ─────────────────────────────────────────────────────────────────────────────
solver_log = ""

if run_btn:
    if not os.path.exists(EXE_PATH):
        st.markdown(
            f'<div class="status err">⚠ SOLVER NOT FOUND — expected at {EXE_PATH}</div>',
            unsafe_allow_html=True)
        st.stop()

    os.makedirs(os.path.join("core", "data"), exist_ok=True)

    st.write(f"DEBUG barrier_mode={barrier_mode} type={type(barrier_mode)}")

    st.markdown('<div class="status gold">◈  INITIALISING SOLVER…</div>',
                unsafe_allow_html=True)

    t_start = time.perf_counter()
    try:
        proc = subprocess.run(
            [EXE_PATH,
             str(v0), str(bw), str(k0), str(sigma),
             str(n_steps), str(barrier_mode)],
            check=True,
            capture_output=True,
            text=True,
        )
        elapsed     = time.perf_counter() - t_start
        solver_log  = proc.stdout.strip()
        last_line   = solver_log.splitlines()[-1] if solver_log else "done"
        st.markdown(
            f'<div class="status ok">✓  SOLVER COMPLETE — {elapsed:.3f} s  //  {last_line}</div>',
            unsafe_allow_html=True)
    except subprocess.CalledProcessError as e:
        st.markdown(
            f'<div class="status err">✗  SOLVER ERROR (exit {e.returncode}): '
            f'{e.stderr[:300]}</div>',
            unsafe_allow_html=True)
        st.stop()

    time.sleep(0.15)


# ─────────────────────────────────────────────────────────────────────────────
#  LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────

e_kin_live = 0.5 * k0 * k0
e_ratio_live = e_kin_live / v0 if v0 > 0 else 0.0
regime = "TUNNELING" if e_kin_live < v0 else "OVER-BARRIER"
regime_color = "color:var(--cyan)" if e_kin_live < v0 else "color:var(--gold)"

if os.path.exists(POS_PATH):
    df   = pd.read_csv(POS_PATH)
    steps = sorted(df["step"].unique())

    last        = df[df["step"] == steps[-1]]
    T_pct       = float(last["trans_prob"].iloc[0])   * 100.0
    R_pct       = float(last["refl_prob"].iloc[0])    * 100.0  \
                  if "refl_prob" in df.columns else 0.0
    norm_final  = float(last["norm_total"].iloc[0])   \
                  if "norm_total" in df.columns else 1.0
    absorbed    = max(0.0, (1.0 - norm_final) * 100.0)
    e_kin       = 0.5 * k0 * k0
    e_ratio     = e_kin / v0 if v0 > 0 else 0.0

    xBS  = float(df["barrier_start"].iloc[0]) if "barrier_start" in df.columns else 60.0
    xBE  = float(df["barrier_end"].iloc[0])   if "barrier_end"   in df.columns else 60.0 + bw
    xBS2 = float(df["barrier_start2"].iloc[0]) if "barrier_start2" in df.columns else 0.0
    xBE2 = float(df["barrier_end2"].iloc[0])   if "barrier_end2"   in df.columns else 0.0
    V0_d = float(df["V0"].iloc[0])             if "V0" in df.columns else v0
    xMax = float(df["x"].max())

    df_mom = None
    if show_momentum and os.path.exists(MOM_PATH):
        df_mom = pd.read_csv(MOM_PATH)

    # ─────────────────────────────────────────────────────────────────────────
    #  METRIC DASHBOARD
    # ─────────────────────────────────────────────────────────────────────────
   
    st.markdown(f"""
    <div class="metric-grid">
        <div class="mc">
            <div class="mc-label">Transmission  T</div>
            <div class="mc-val">{T_pct:.3f}</div>
            <div class="mc-unit">%</div>
        </div>
        <div class="mc gold">
            <div class="mc-label">Reflection  R</div>
            <div class="mc-val">{R_pct:.3f}</div>
            <div class="mc-unit">%</div>
        </div>
        <div class="mc red">
            <div class="mc-label">CAP Absorbed</div>
            <div class="mc-val">{absorbed:.2f}</div>
            <div class="mc-unit">%</div>
        </div>
        <div class="mc green">
            <div class="mc-label">E_kin / V₀</div>
            <div class="mc-val">{e_ratio_live:.3f}</div>
            <div class="mc-unit" style="{regime_color}">{regime}  live ✱</div>
        </div>
        <div class="mc">
            <div class="mc-label">Kinetic Energy</div>
            <div class="mc-val">{e_kin_live:.3f}</div>
            <div class="mc-unit">k₀²/2  live ✱</div>
        </div>
        <div class="mc gold">
            <div class="mc-label">Frames</div>
            <div class="mc-val">{len(steps)}</div>
            <div class="mc-unit">exported steps</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    #  HELPER FUNCTIONS
    # ─────────────────────────────────────────────────────────────────────────
    def add_barriers(fig, row=1, col=1):
        """Add red shaded barrier region(s) with V₀ label on top."""
        fig.add_vrect(
            x0=xBS, x1=xBE,
            fillcolor="rgba(255,45,85,0.13)", opacity=1,
            line=dict(color="rgba(255,45,85,0.7)", width=1.5),
            row=row, col=col,
        )
        fig.add_annotation(
            x=(xBS+xBE)/2,
            y=0,
            yref="paper",
            yanchor="bottom",
            text=f"V₀={V0_d:.0f}",
            showarrow=False,
            font=dict(family="Share Tech Mono", size=11, color="#ff2d55"),
            bgcolor="rgba(0,0,0,0.5)",
            borderpad=3,
            row=row,
            col=col,
        )
        if xBS2 > 0 and xBE2 > xBS2:
            fig.add_vrect(
                x0=xBS2, x1=xBE2,
                fillcolor="rgba(255,45,85,0.13)", opacity=1,
                line=dict(color="rgba(255,45,85,0.7)", width=1.5),
                row=row, col=col,
            )
            fig.add_annotation(
                x=(xBS2+xBE2)/2,
                y=0.92,
                yref="paper",
                yanchor="top",
                text=f"V₀={V0_d:.0f}",
                showarrow=False,
                font=dict(family="Share Tech Mono", size=11, color="#ff2d55"),
                bgcolor="rgba(0,0,0,0.5)",
                borderpad=3,
                row=row,
                col=col,
            )

    def add_energy_line(fig, row=1, col=1):
        """Draw horizontal E_kin line across the chart."""
        if not show_energy:
            return
        prob_max = df["prob"].max()
        e_norm   = min(e_kin / V0_d * prob_max * 0.6, prob_max * 0.9)
        fig.add_hline(
            y=e_norm,
            line=dict(color="rgba(0,255,157,0.45)", width=1, dash="dot"),
            annotation_text=f"E={e_kin:.2f}",
            annotation_font=dict(family="Share Tech Mono", size=8, color="#00ff9d"),
            row=row, col=col,
        )
        v_norm = prob_max * 0.92
        fig.add_hline(
            y=v_norm,
            line=dict(color="rgba(255,190,0,0.3)", width=1, dash="dot"),
            annotation_text=f"V₀={V0_d:.0f}",
            annotation_font=dict(family="Share Tech Mono", size=8, color="#ffbe00"),
            row=row, col=col,
        )

    # ─────────────────────────────────────────────────────────────────────────
    #  MAIN ANIMATION
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown('<div class="sec-label cyan">Wavefunction Dynamics  |ψ(x,t)|²</div>',
                unsafe_allow_html=True)

    prob_max = float(df["prob"].max()) * 1.25

    if show_momentum and df_mom is not None:
        fig_main = make_subplots(
            rows=1, cols=2,
            column_widths=[0.62, 0.38],
            horizontal_spacing=0.06,
            subplot_titles=["Position space  |ψ(x,t)|²", "Momentum space  |φ(k,t)|²"],
        )
        for ann in fig_main.layout.annotations:
            ann.font = dict(family="Share Tech Mono", size=10, color="#3a5a78")
    else:
        fig_main = make_subplots(rows=1, cols=1)

    d0 = df[df["step"] == steps[0]]

    fig_main.add_trace(
        go.Scatter(
            x=d0["x"], y=d0["prob"],
            mode="lines", fill="tozeroy",
            fillcolor="rgba(0,242,255,0.07)",
            line=dict(color="#00f2ff", width=2),
            name="|ψ|²",
        ), row=1, col=1
    )

    if show_phase and "prob" in d0.columns:
        x_arr = d0["x"].values
        amp   = np.sqrt(d0["prob"].values)
        re_approx = amp * np.cos(k0 * x_arr * 0.1)
        im_approx = amp * np.sin(k0 * x_arr * 0.1)

        fig_main.add_trace(
            go.Scatter(
                x=d0["x"], y=re_approx * 0.5,
                mode="lines",
                line=dict(color="rgba(0,119,255,0.5)", width=1, dash="dot"),
                name="Re(ψ) ~",
            ), row=1, col=1
        )
        fig_main.add_trace(
            go.Scatter(
                x=d0["x"], y=im_approx * 0.5,
                mode="lines",
                line=dict(color="rgba(255,45,85,0.4)", width=1, dash="dash"),
                name="Im(ψ) ~",
            ), row=1, col=1
        )

    mom_col = 2 if (show_momentum and df_mom is not None) else None
    if mom_col:
        dm0 = df_mom[df_mom["step"] == steps[0]]
        fig_main.add_trace(
            go.Scatter(
                x=dm0["k"], y=dm0["mom_prob"],
                mode="lines", fill="tozeroy",
                fillcolor="rgba(255,190,0,0.07)",
                line=dict(color="#ffbe00", width=1.8),
                name="|φ(k)|²",
            ), row=1, col=mom_col
        )

    frames = []
    for s in steps:
        ds      = df[df["step"] == s]
        x_arr   = ds["x"].values
        amp     = np.sqrt(ds["prob"].values)
        re_ap   = amp * np.cos(k0 * x_arr * 0.1) * 0.5
        im_ap   = amp * np.sin(k0 * x_arr * 0.1) * 0.5

        frame_data = [
            go.Scatter(x=ds["x"], y=ds["prob"],
                       fill="tozeroy", fillcolor="rgba(0,242,255,0.07)",
                       line=dict(color="#00f2ff", width=2)),
        ]
        if show_phase:
            frame_data += [
                go.Scatter(x=ds["x"], y=re_ap,
                           line=dict(color="rgba(0,119,255,0.5)", width=1, dash="dot")),
                go.Scatter(x=ds["x"], y=im_ap,
                           line=dict(color="rgba(255,45,85,0.4)", width=1, dash="dash")),
            ]
        if mom_col:
            dm = df_mom[df_mom["step"] == s] if df_mom is not None else None
            if dm is not None and not dm.empty:
                frame_data.append(
                    go.Scatter(x=dm["k"], y=dm["mom_prob"],
                               fill="tozeroy", fillcolor="rgba(255,190,0,0.07)",
                               line=dict(color="#ffbe00", width=1.8))
                )

        frames.append(go.Frame(data=frame_data, name=str(s)))

    fig_main.frames = frames

    fig_main.update_layout(
        **PLOTLY_BASE,
        height=580,
        margin=dict(l=52, r=52, t=36, b=48),
        legend=dict(
            font=dict(family="Share Tech Mono", size=9, color="#3a5a78"),
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,242,255,0.1)",
            x=0.01, y=0.98,
        ),
        updatemenus=[dict(
            type="buttons", showactive=False,
            x=0.01, y=0.99, xanchor="left", yanchor="top",
            bgcolor="rgba(4,10,18,0.85)", bordercolor="rgba(0,242,255,0.4)",
            font=dict(family="Orbitron", size=12, color="#00f2ff"),
            buttons=[
                dict(label="▶", method="animate",
                     args=[None, dict(frame=dict(duration=28, redraw=True),
                                      fromcurrent=True,
                                      transition=dict(duration=0))]),
                dict(label="⏸", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False),
                                        mode="immediate",
                                        transition=dict(duration=0))]),
            ],
        )],
        sliders=[dict(
            active=0,
            currentvalue=dict(prefix="STEP: ",
                              font=dict(family="Share Tech Mono", size=9, color="#3a5a78"),
                              xanchor="left"),
            pad=dict(t=8, b=4),
            bgcolor="#060d15", bordercolor="#091828",
            tickcolor="#091828",
            font=dict(family="Share Tech Mono", size=7, color="#1e3a50"),
            steps=[dict(method="animate", label=str(s),
                        args=[[str(s)], dict(frame=dict(duration=0, redraw=True),
                                             mode="immediate",
                                             transition=dict(duration=0))])
                   for s in steps],
        )],
    )

    fig_main.update_xaxes(
        **axis_style("x", "#3a5a78", "#3a5a78"),
        range=[0, xMax], row=1, col=1,
    )
    fig_main.update_yaxes(
        **axis_style("|ψ|²", "#00f2ff", "#00f2ff"),
        range=[-0.005, prob_max * 0.75], row=1, col=1,
    )

    if mom_col and df_mom is not None:
        kmax = float(df_mom["k"].abs().max()) * 1.05
        pmax = float(df_mom["mom_prob"].max()) * 1.25
        fig_main.update_xaxes(
            **axis_style("k", "#3a5a78", "#3a5a78"),
            range=[-kmax, kmax], row=1, col=mom_col,
        )
        mom_yaxis = axis_style("|φ(k)|²", "#ffbe00", "#ffbe00")
        if mom_log_scale:
            mom_yaxis["type"] = "log"
            mom_yaxis.pop("range", None)
        else:
            mom_yaxis["range"] = [0, max(pmax, 1e-10)]
        fig_main.update_yaxes(**mom_yaxis, row=1, col=mom_col)

    add_barriers(fig_main, row=1, col=1)
    add_energy_line(fig_main, row=1, col=1)

    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig_main, use_container_width=True, config={
        "displayModeBar": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": ["select2d", "lasso2d"],
    })
    st.markdown('</div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    #  SPARKLINE CHARTS
    # ─────────────────────────────────────────────────────────────────────────
    tr_series = df.groupby("step").agg(
        T=("trans_prob", "first"),
        R=("refl_prob",  "first") if "refl_prob"  in df.columns else ("trans_prob", "first"),
        N=("norm_total", "first") if "norm_total" in df.columns else ("trans_prob", "first"),
    ).reset_index()

    spark_cols = [1]
    if "refl_prob"  in df.columns: spark_cols.append(2)
    if show_norm and "norm_total" in df.columns: spark_cols.append(3)
    n_spark = len(spark_cols)

    col_objs = st.columns(n_spark)

    def sparkline(col_obj, x, y, label, color, fill_color, y_label, y_range=None, label_override=None):
        fig = go.Figure()
        tiny_range = [0, 1] if float(np.max(np.abs(y))) < 1e-6 else None
        effective_range = y_range if y_range else tiny_range
        fig.add_trace(go.Scatter(
            x=x, y=y * 100,
            mode="lines", fill="tozeroy", fillcolor=fill_color,
            line=dict(color=color, width=1.8),
        ))
        fig.update_layout(
            **PLOTLY_BASE,
            height=170,
            margin=dict(l=44, r=16, t=18, b=32),
            showlegend=False,
            xaxis=axis_style("Step"),
            yaxis={**axis_style(y_label, color, color),
                     "tickformat": ".2f",
                     "rangemode": "tozero",
                     "exponentformat": "e",
                     "showexponent": "all",
                     **({"range": effective_range} if effective_range else {})},
        )
        if label_override is not None:
            fig.add_annotation(
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                text=label_override,
                showarrow=False,
                font=dict(family="Share Tech Mono", size=11, color="#ffbe00"),
                opacity=0.7,
            )
        with col_obj:
            st.markdown(f'<div class="sec-label">{label}</div>', unsafe_allow_html=True)
            st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True,
                            config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

    sparkline(col_objs[0],
              tr_series["step"].values,
              tr_series["T"].values,
              "Transmission T(t)",
              "#00f2ff", "rgba(0,242,255,0.06)",
              "T (%)")

    if "refl_prob" in df.columns and len(col_objs) > 1:
        sparkline(col_objs[1],
                  tr_series["step"].values,
                  tr_series["R"].values,
                  "Reflection R(t)",
                  "#ffbe00", "rgba(255,190,0,0.06)",
                  "R (%)",
                  label_override="FULLY REFLECTED" if tr_series["R"].max() > 0.98 else None)

    if show_norm and "norm_total" in df.columns and len(col_objs) > 2:
        sparkline(col_objs[2],
                  tr_series["step"].values,
                  tr_series["N"].values,
                  "Norm decay (CAP absorption)",
                  "#ff2d55", "rgba(255,45,85,0.06)",
                  "Norm (%)")

    # ─────────────────────────────────────────────────────────────────────────
    #  SOLVER LOG
    # ─────────────────────────────────────────────────────────────────────────
    if solver_log:
        st.markdown('<div class="sec-label">Solver Output</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="log-box">{solver_log}</div>',
                    unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    #  CSV EXPORT
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    dl_col1, dl_col2, _ = st.columns([1, 1, 4])

    with dl_col1:
        st.download_button(
            label="⬇  position data CSV",
            data=df.to_csv(index=False).encode(),
            file_name="output.csv",
            mime="text/csv",
        )

    if df_mom is not None:
        with dl_col2:
            st.download_button(
                label="⬇  momentum data CSV",
                data=df_mom.to_csv(index=False).encode(),
                file_name="momentum.csv",
                mime="text/csv",
            )

# ─────────────────────────────────────────────────────────────────────────────
#  IDLE STATE
# ─────────────────────────────────────────────────────────────────────────────
else:
    st.markdown("""
        <div class="idle">
            <div class="idle-title">◈  Awaiting Simulation Data</div>
            <div class="idle-sub">
                Configure parameters in the sidebar and click ▶ RUN SIMULATION
            </div>
        </div>
    """, unsafe_allow_html=True)