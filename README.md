# Decentralized P2P Energy Trading Simulation

This project is made by **Quantum Coders**, a team from **VSSUT Burla** (Veer Surendra Sai University of Technology, Burla).

## Team Members
- **Arsalan Ali**
- **Brahamananda Sahoo**
- **Kritika Tekriwal**

This repository contains a Python-based simulation of a decentralized peer-to-peer energy trading platform with a lightweight blockchain-like ledger and interactive dashboard.

## Features

- Local energy community with prosumers and consumers
- Hourly market cycles with stochastic renewable generation and demand
- Decentralized bid/ask matching and smart contract settlement
- Blockchain ledger with timestamped blocks, transaction hashes, and immutability checks
- Real-time interactive dashboard in Streamlit with price trends, network graphs, and ledger summaries
- Performance metrics for trading efficiency, cost savings, grid load reduction, and price stability

## Installation

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the dashboard

If `streamlit` is not found on your PATH, use Python's module invocation instead:

```bash
python -m streamlit run app.py
```

On Windows, you can also launch the app with:

```powershell
run_app.bat
```

## Project structure

- `energy_trading_sim.py`: Simulation engine, market matching, blockchain logic, and smart contract settlement
- `app.py`: Streamlit dashboard for interactive parameter adjustment and results visualization
- `requirements.txt`: Required Python packages
- `README.md`: Project overview and usage instructions
