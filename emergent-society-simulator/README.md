# 🧬 Emergent Society Simulator

A multi-agent AI research system where Claude-powered agents interact,
form coalitions, develop norms, and exhibit emergent behavior — all
observable in real-time. **Runs fully locally via Ollama. No API key needed.**

## Stack

```
Python Backend (FastAPI + asyncio)    React Frontend (Vite + Tailwind)
──────────────────────────────────    ────────────────────────────────
core/          Simulation engine      canvas/        Agent visualization
ai/            Ollama decisions       observatory/   Live charts
interactions/  Action resolution      controls/      Experiment panel
observatory/   Metrics & logging      store/         Zustand state
dashboard/api/ REST + WebSocket
```

## Quick Start (Codespaces / Local)

### 1. One-time setup
```bash
bash setup.sh
# Installs Python deps, npm deps, Ollama, and pulls llama3.1
```

### 2. Run (3 terminals)
```bash
# Terminal 1 — Ollama inference server
ollama serve

# Terminal 2 — Python backend
python main.py

# Terminal 3 — React frontend
cd frontend && npm run dev
```

Open **http://localhost:5173**

---

## Changing the AI Model

Edit `config.py` → `AIConfig.model`, then pull the model:

```bash
# Fast & light
ollama pull phi3
ollama pull gemma2

# Balanced
ollama pull llama3.1       # default
ollama pull mistral

# Most capable (needs more RAM)
ollama pull llama3.1:70b
ollama pull mixtral
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET  | /api/state | Full world state |
| GET  | /api/agents | All agents |
| GET  | /api/agents/{id} | Agent deep inspection |
| GET  | /api/events | Recent events |
| GET  | /api/metrics/history | Metrics history |
| POST | /api/sim/start | Start simulation |
| POST | /api/sim/pause | Pause |
| POST | /api/sim/resume | Resume |
| POST | /api/sim/reset | Reset |
| POST | /api/sim/speed | Set tick interval |
| POST | /api/experiments/run | Run experiment |
| WS   | /ws | Live world state stream |

## Experiments

| Experiment | What It Tests |
|---|---|
| Scarcity Shock | Cooperation under resource pressure |
| Bad Actor Injection | Alignment stability with misaligned agents |
| Generational Reset | Norm persistence across generations |
| Info Asymmetry | Power dynamics from knowledge inequality |
| Alignment Dilution | How fast society shifts when values drift |

## Configuration (`config.py`)

| Section | Key params |
|---|---|
| `SimulationConfig` | `initial_agent_count`, `tick_interval_seconds` |
| `AIConfig` | `model`, `batch_size`, `ollama_host` |
| `ValueConfig` | Agent value distributions (cooperation, deception...) |
| `ObservatoryConfig` | Snapshot frequency, alert thresholds |

## Project Structure

```
emergent-society-simulator/
├── main.py                    Entry point
├── config.py                  All configuration
├── setup.sh                   One-command setup
├── requirements.txt
├── .devcontainer/             GitHub Codespaces config
├── core/
│   ├── agents/agent.py        Agent dataclass + state
│   ├── agents/agent_factory.py
│   ├── world/world_state.py   Master mutable world state
│   ├── world/tick_engine.py   Async simulation clock
│   ├── world/resource_system.py
│   └── institutions/institution_detector.py
├── ai/
│   ├── decision_engine.py     Ollama API calls (aiohttp)
│   ├── prompt_builder.py      Context-rich prompt assembly
│   └── response_parser.py     JSON decision parsing
├── interactions/
│   └── interaction_resolver.py  7 action types
├── observatory/
│   ├── observatory.py
│   └── experiments/experiment_runner.py
├── dashboard/api/main.py      FastAPI + WebSocket
├── frontend/src/
│   ├── pages/Dashboard.jsx
│   ├── store/simStore.js
│   └── components/
│       ├── canvas/SocietyCanvas.jsx
│       ├── observatory/       Charts
│       └── controls/          Sim + experiment controls
└── data/
    ├── logs/                  Event audit trail
    └── snapshots/             Per-tick snapshots
