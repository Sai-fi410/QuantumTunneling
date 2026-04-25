# QuantumLab — Quantum Tunneling Simulator

> **TDSE Engine v3.0** — Time-Dependent Schrödinger Equation solver with live wavefunction and momentum dynamics.


---

## Overview

QuantumLab is a physics simulation dashboard that numerically solves the **1D Time-Dependent Schrödinger Equation (TDSE)** using the **Crank-Nicolson finite difference method** with **Complexly Absorbing Potential (CAP) boundaries**. It visualizes quantum tunneling in real time — showing how a Gaussian wave packet behaves when it encounters a potential barrier.

Built as a personal project at the intersection of computational physics and software engineering.

---

## Features

- **Crank-Nicolson solver** — unconditionally stable, unitary time evolution
- **CAP boundaries** — absorb outgoing waves, prevent artificial reflections
- **Single and double barrier modes** — standard tunneling and resonant tunneling
- **Live wavefunction animation** — |ψ(x,t)|², Re(ψ), Im(ψ) in position space
- **Momentum space panel** — |φ(k,t)|² spectrum with optional log scale
- **Phase portrait** — Re/Im components overlaid on probability density
- **Energy level overlay** — E_kin and V₀ reference lines on chart
- **Transmission T(t), Reflection R(t), Norm decay** — sparkline charts
- **Live metric cards** — E_kin/V₀ ratio and kinetic energy update without re-running solver
- **Regime detection** — TUNNELING vs OVER-BARRIER label updates in real time

---

## Tech Stack

| Layer | Technology |
|---|---|
| Solver | C++17, Crank-Nicolson, CAP |
| Dashboard | Python, Streamlit |
| Visualization | Plotly |
| Data I/O | CSV (position + momentum output) |
| Compilation | g++ -O2 -std=c++17 |

---

## Project Structure

```
quantum-tunneling-simulator/
├── quantum_python.py       # Streamlit dashboard
├── quantum_c++.cpp         # C++ Crank-Nicolson solver
├── solver.exe              # Compiled binary (Windows)
├── assets/
│   └── screenshot.png      # Dashboard preview
└── core/
    └── data/
        ├── output.csv      # Position-space simulation output
        └── momentum.csv    # Momentum-space spectrum output
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- g++ with C++17 support
- Streamlit, Plotly, Pandas, NumPy

```powershell
pip install streamlit plotly pandas numpy
```

### Compile the Solver

```powershell
g++ -O2 -std=c++17 -o solver.exe quantum_c++.cpp
```

### Run the Dashboard

```powershell
cd "path/to/quantum-tunneling-simulator"
python -m streamlit run quantum_python.py
```

---

## Physics Background

The simulator solves:

$$i\hbar \frac{\partial \psi}{\partial t} = \left[ -\frac{\hbar^2}{2m} \frac{\partial^2}{\partial x^2} + V(x) \right] \psi(x,t)$$

with ℏ = 1, m = ½ (atomic units). The initial state is a Gaussian wave packet:

$$\psi(x, 0) = \frac{1}{(2\pi\sigma^2)^{1/4}} \exp\left(-\frac{(x-x_0)^2}{4\sigma^2}\right) e^{ik_0 x}$$

**Tunneling regime:** E_kin < V₀ — wave packet partially penetrates classically forbidden region.  
**Over-barrier regime:** E_kin > V₀ — wave packet transmits with partial reflection.  
**Resonant tunneling (double barrier):** at specific energies, transmission approaches 100% due to constructive interference in the inter-barrier cavity.

---

## Parameters

| Parameter | Description | Default |
|---|---|---|
| V₀ | Barrier potential height | 150 |
| Δx (barrier width) | Width of potential barrier | 5.0 |
| k₀ | Wave-vector (controls energy) | 4.50 |
| σ | Gaussian packet width | 4.0 |
| Time steps | Solver iterations | 500 |
| Barrier mode | Single / Double (resonant) | Single |

---

## Authors

- **Sai Dhapte** — [@Sai-fi410](https://github.com/Sai-fi410) — Solver architecture, dashboard, visualization
- Collaborated with teammates on physics validation and testing

---

## License

MIT License — free to use, modify, and distribute with attribution.
