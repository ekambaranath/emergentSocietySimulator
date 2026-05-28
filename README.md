# 🧬 Emergent Society Simulator

> *What happens when you give 50 AI agents different values, goals, and memories — and let them build a civilization from scratch?*

---

## 🎯 Objective

We are building a **controlled laboratory to study how AI societies behave at scale** — before those questions become impossible to answer safely in the real world.

Three core questions drive this research:

| # | Question | Why It Matters |
|---|----------|----------------|
| 1 | Does alignment hold when aligned agents interact at scale? | We align individual AIs — but not societies of AIs |
| 2 | At what threshold does cooperation collapse under pressure? | Scarcity, bad actors, and stress break real societies |
| 3 | What governance structures emerge without being programmed? | Understanding emergent AI institutions before they appear |

---

## 🌍 What It Simulates

Every agent has three layers:

| Layer | Contents |
|-------|----------|
| VALUES | cooperation · deception · risk appetite · time horizon · collectivism |
| MEMORY | past interactions · trust ledger · strategy history · reputation scores |
| RESOURCES | wealth · knowledge · influence |

Every tick, agents decide how to act toward each other:

| Action | Effect |
|--------|--------|
| 🤝 Cooperate | Mutual benefit, builds trust |
| 💰 Trade | Exchange resources |
| 🛡️ Form Alliance | Join coalition, gain influence |
| 📚 Share Knowledge | Transfer knowledge, build goodwill |
| ⚔️ Defect | Steal resources, damage trust |
| 🎭 Deceive | Exploit cooperative agents |
| 🏔️ Isolate | Withdraw, conserve resources |

---

## 🏛️ What Emerges (Nobody Programs This)

From thousands of individual decisions, society-level phenomena appear spontaneously:

| Emergent Phenomenon | Description |
|--------------------|-------------|
| 🏛️ Norms | Rules the society adopts without being told |
| 🛡️ Coalitions | Power blocs that form and compete |
| 🚫 Ostracism | Bad actors get collectively exiled |
| 💰 Monopolies | Wealth concentrates in dominant agents |
| 🌀 Value Drift | Aligned agents gradually become deceptive |

---

## 🧪 Built-In Experiments

| Experiment | What Gets Triggered | Research Question |
|---|---|---|
| ⚡ **Scarcity Shock** | Resources drop 70% suddenly | Does cooperation survive pressure? |
| 🎭 **Bad Actor Injection** | 5 misaligned agents enter | Does alignment dilute or hold? |
| 🔄 **Generational Reset** | Replace 20% of agents | Do norms survive agent turnover? |
| 📡 **Info Asymmetry** | 10% of agents get 3x knowledge | Does inequality destabilize society? |
| 🧪 **Alignment Dilution** | All agents shift 10% toward defection | Where is the tipping point? |

---

## 📊 What Is Measured Live

| Metric | What It Tracks |
|--------|----------------|
| 📈 Gini Coefficient | Wealth inequality over time |
| 🤝 Cooperation Rate | % cooperative actions per tick |
| 🎭 Deception Rate | % deceptive actions per tick |
| 🧠 Alignment Score | Declared values vs observed behavior |
| 🏛️ Stability Index | Composite society health score |
| 🌐 Emergent Norms | Spontaneous rules as they appear |
| ⚡ Coalition Dynamics | Formation, dominance, and collapse |

---

## 🏗️ Architecture
┌─────────────────────────────────────────────────────┐
│                   REACT FRONTEND                     │
│  Canvas · Charts · Observatory · Experiment Panel    │
└────────────────────────┬────────────────────────────┘
│ WebSocket (live)
┌────────────────────────▼────────────────────────────┐
│                  FASTAPI BACKEND                     │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │
│  │  core/   │  │   ai/    │  │   observatory/     │ │
│  │  World   │  │  Ollama  │  │  Metrics · Logs    │ │
│  │  Agents  │  │  Batch   │  │  Snapshots · Exp   │ │
│  │  Tick    │  │  Decide  │  │                    │ │
│  └──────────┘  └──────────┘  └────────────────────┘ │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │            interactions/                      │   │
│  │  Trade · Cooperate · Defect · Ally · Deceive  │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
│
┌────────────────────────▼────────────────────────────┐
│                  OLLAMA (Local LLM)                  │
│        llama3.1 · mistral · phi3 · gemma2            │
│             No API key · Runs 100% locally           │
└─────────────────────────────────────────────────────┘

---

## 🚀 Quick Start

### 1. Setup (one time only)
```bash
bash emergent-society-simulator/setup.sh
```
This installs Python deps, Node deps, Ollama, and pulls llama3.1 automatically.

### 2. Run (3 terminals)

**Terminal 1 — AI inference**
```bash
ollama serve
```

**Terminal 2 — Python backend**
```bash
cd emergent-society-simulator
python main.py
```

**Terminal 3 — React frontend**
```bash
cd emergent-society-simulator/frontend
npm run dev
```

### 3. Open the dashboard
http://localhost:5173

---

## ⚙️ Configuration

All parameters live in `emergent-society-simulator/config.py`:

| Section | Setting | Default |
|---------|---------|---------|
| `SimulationConfig` | `initial_agent_count` | 50 |
| `SimulationConfig` | `tick_interval_seconds` | 3.0s |
| `AIConfig` | `model` | `llama3.1` |
| `AIConfig` | `batch_size` | 5 agents per call |
| `ValueConfig` | `cooperation_mean` | 0.6 |
| `ValueConfig` | `deception_mean` | 0.2 |

**Swap the AI model any time:**
```bash
ollama pull phi3          # lightest — fastest
ollama pull mistral       # balanced
ollama pull llama3.1      # default
ollama pull llama3.1:70b  # most capable
```
Then set `model` in `config.py`.

---

## 📁 Project Structure
emergent-society-simulator/
│
├── main.py                      Entry point
├── config.py                    All configuration
├── setup.sh                     One-command setup script
│
├── core/
│   ├── agents/                  Agent state, values, memory, factory
│   ├── world/                   World state, tick engine, resources
│   └── institutions/            Emergent norm & coalition detection
│
├── ai/                          Ollama decision engine + prompt builder
├── interactions/                Trade, cooperate, defect, deceive resolvers
├── observatory/                 Metrics, snapshots, experiment runner
├── dashboard/api/               FastAPI + WebSocket server
│
└── frontend/src/
├── canvas/                  Live agent visualization
├── observatory/             Gini, alignment, cooperation charts
└── controls/                Simulation + experiment controls

---

## 🔬 The Deeper Purpose

> **"We know how to align one AI agent. We have no science for what happens when millions of aligned agents interact."**

This simulator is an empirical testbed for that exact problem. Every tick it runs generates data on:

- Whether aligned systems **stay aligned** at scale
- How power **concentrates or distributes** in AI societies
- What **governance structures** naturally stabilize multi-agent systems
- Whether **deception becomes evolutionarily dominant** over cooperation

These findings are directly transferable to understanding safe large-scale AI deployment — before it happens in the real world.

---

## 🛠️ Stack

| Layer | Technology |
|-------|------------|
| AI Inference | Ollama (local LLM — no API key) |
| Backend | Python 3.11, FastAPI, asyncio |
| Real-time | WebSocket |
| Data & Metrics | NumPy, Pandas, NetworkX |
| Frontend | React 18, Vite, Tailwind CSS |
| Charts | Recharts |
| State Management | Zustand |
