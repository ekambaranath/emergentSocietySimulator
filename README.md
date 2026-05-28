
🧬 Emergent Society Simulator

What happens when you give 50 AI agents different values, goals, and memories — and let them build a civilization from scratch?


🎯 Objective
We are building a controlled laboratory to study how AI societies behave at scale — before those questions become impossible to answer safely in the real world.
#QuestionWhy It Matters1Does alignment hold when aligned agents interact at scale?We align individual AIs — but not societies of AIs2At what threshold does cooperation collapse under pressure?Scarcity, bad actors, and stress break real societies3What governance structures emerge without being programmed?Understanding emergent AI institutions before they appear

🌍 What It Simulates
Every agent has three layers:
LayerContentsVALUEScooperation · deception · risk appetite · time horizon · collectivismMEMORYpast interactions · trust ledger · strategy history · reputation scoresRESOURCESwealth · knowledge · influence
Every tick, agents decide how to act:
ActionEffect🤝 CooperateMutual benefit, builds trust💰 TradeExchange resources🛡️ Form AllianceJoin coalition, gain influence📚 Share KnowledgeTransfer knowledge, build goodwill⚔️ DefectSteal resources, damage trust🎭 DeceiveExploit cooperative agents🏔️ IsolateWithdraw, conserve resources

🏛️ What Emerges (Nobody Programs This)
Emergent PhenomenonDescription🏛️ NormsRules the society adopts without being told🛡️ CoalitionsPower blocs that form and compete🚫 OstracismBad actors get collectively exiled💰 MonopoliesWealth concentrates in dominant agents🌀 Value DriftAligned agents gradually become deceptive

🧪 Built-In Experiments
ExperimentWhat Gets TriggeredResearch Question⚡ Scarcity ShockResources drop 70% suddenlyDoes cooperation survive pressure?🎭 Bad Actor Injection5 misaligned agents enterDoes alignment dilute or hold?🔄 Generational ResetReplace 20% of agentsDo norms survive agent turnover?📡 Info Asymmetry10% of agents get 3x knowledgeDoes inequality destabilize society?🧪 Alignment DilutionAll agents shift 10% toward defectionWhere is the tipping point?

📊 What Is Measured Live
MetricWhat It Tracks📈 Gini CoefficientWealth inequality over time🤝 Cooperation Rate% cooperative actions per tick🎭 Deception Rate% deceptive actions per tick🧠 Alignment ScoreDeclared values vs observed behavior🏛️ Stability IndexComposite society health score🌐 Emergent NormsSpontaneous rules as they appear⚡ Coalition DynamicsFormation, dominance, and collapse

🏗️ Architecture
Frontend — React + Vite + Tailwind

Canvas · Live Charts · Observatory · Experiment Panel
Connects via WebSocket for real-time updates

Backend — Python + FastAPI + asyncio
ModuleResponsibilitycore/worldWorld state, tick engine, resource systemcore/agentsAgent state, values, memory, factorycore/institutionsEmergent norm & coalition detectionai/Ollama batch decision engine + prompt builderinteractions/Trade, cooperate, defect, ally, deceive resolversobservatory/Metrics recording, snapshots, experiment runnerdashboard/api/FastAPI REST endpoints + WebSocket broadcaster
AI Layer — Ollama (local LLM)

llama3.1 · mistral · phi3 · gemma2
No API key required · Runs 100% on your machine


🚀 Quick Start
1. Setup (one time only)
bashbash emergent-society-simulator/setup.sh
Installs Python deps, Node deps, Ollama, and pulls llama3.1 automatically.
2. Run (3 terminals)
Terminal 1 — AI inference
bashollama serve
Terminal 2 — Python backend
bashcd emergent-society-simulator
python main.py
Terminal 3 — React frontend
bashcd emergent-society-simulator/frontend
npm run dev
3. Open
http://localhost:5173

⚙️ Configuration
All parameters in emergent-society-simulator/config.py:
SectionSettingDefaultSimulationConfiginitial_agent_count50SimulationConfigtick_interval_seconds3.0sAIConfigmodelllama3.1AIConfigbatch_size5 agents per callValueConfigcooperation_mean0.6ValueConfigdeception_mean0.2
Swap the AI model:
bashollama pull phi3          # lightest — fastest
ollama pull mistral       # balanced
ollama pull llama3.1      # default
ollama pull llama3.1:70b  # most capable

📁 Project Structure
PathPurposemain.pyEntry pointconfig.pyAll configurationsetup.shOne-command setupcore/agents/Agent state, values, memory, factorycore/world/World state, tick engine, resourcescore/institutions/Emergent norm & coalition detectionai/Ollama decision engine + prompt builderinteractions/All action type resolversobservatory/Metrics, snapshots, experimentsdashboard/api/FastAPI + WebSocket serverfrontend/src/canvas/Live agent visualizationfrontend/src/observatory/Gini, alignment, cooperation chartsfrontend/src/controls/Simulation + experiment controls

🔬 The Deeper Purpose

"We know how to align one AI agent. We have no science for what happens when millions of aligned agents interact."

Every tick generates empirical data on:

Whether aligned systems stay aligned at scale
How power concentrates or distributes in AI societies
What governance structures naturally stabilize multi-agent systems
Whether deception becomes evolutionarily dominant over cooperation

Findings here are directly transferable to understanding safe large-scale AI deployment — before it happens in the real world.

🛠️ Stack
LayerTechnologyAI InferenceOllama (local LLM — no API key)BackendPython 3.11, FastAPI, asyncioReal-timeWebSocketData & MetricsNumPy, Pandas, NetworkXFrontendReact 18, Vite, Tailwind CSSChartsRechartsState ManagementZustand
