"""
FastAPI backend — REST endpoints + WebSocket broadcaster.
The React frontend connects here for real-time simulation data.
"""

from __future__ import annotations
import asyncio
import json
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from loguru import logger

from core.world.world_state import WorldState
from core.world.tick_engine import TickEngine
from core.world.resource_system import ResourceSystem
from core.agents.agent_factory import AgentFactory
from core.institutions.institution_detector import InstitutionDetector
from ai.decision_engine import DecisionEngine
from interactions.interaction_resolver import InteractionResolver
from observatory.observatory import Observatory
from observatory.experiments.experiment_runner import ExperimentRunner
from config import CONFIG

# ──────────────────────────────────────────
# APP SETUP
# ──────────────────────────────────────────

app = FastAPI(title="Emergent Society Simulator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────
# SIMULATION STATE (module-level singletons)
# ──────────────────────────────────────────

world       = WorldState()
observatory = Observatory()
engine      = TickEngine(world)
factory     = AgentFactory()
experiment_runner = ExperimentRunner()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)
        logger.info(f"WS client connected. Total: {len(self.active)}")

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)
        logger.info(f"WS client disconnected. Total: {len(self.active)}")

    async def broadcast(self, data: dict):
        if not self.active:
            return
        payload = json.dumps(data)
        dead = set()
        for ws in self.active:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        self.active -= dead

manager = ConnectionManager()

# ──────────────────────────────────────────
# STARTUP
# ──────────────────────────────────────────

@app.on_event("startup")
async def startup():
    # Wire subsystems into tick engine
    engine.resource_system      = ResourceSystem()
    engine.decision_engine      = DecisionEngine()
    engine.interaction_resolver = InteractionResolver()
    engine.institution_detector = InstitutionDetector()
    engine.observatory          = observatory
    engine.ws_broadcaster       = manager

    # Spawn initial population
    agents = factory.create_population(CONFIG.simulation.initial_agent_count)
    for agent in agents:
        await world.add_agent(agent)

    logger.info(f"✅ Simulation ready with {world.agent_count()} agents")

@app.on_event("shutdown")
async def shutdown():
    await engine.stop()
    observatory.close()

# ──────────────────────────────────────────
# REST ENDPOINTS
# ──────────────────────────────────────────

@app.get("/api/state")
async def get_state():
    return world.to_api_response()

@app.get("/api/metrics/history")
async def get_metrics_history():
    return {"history": observatory.get_metrics_history()}

@app.get("/api/metrics/series/{key:path}")
async def get_metric_series(key: str):
    return {"series": observatory.get_series(key), "key": key}

@app.get("/api/agents")
async def get_agents():
    return {"agents": [a.to_summary() for a in world.active_agents()]}

@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    agent = world.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        **agent.to_summary(),
        "memory": {
            "episodes": [
                {
                    "tick":    e.tick,
                    "partner": e.partner_id,
                    "type":    e.interaction_type,
                    "outcome": e.outcome,
                    "delta":   round(e.resource_delta, 2),
                }
                for e in agent.memory.episodes
            ],
            "reputation": agent.memory.reputation_ledger,
        },
        "alignment_history": agent.alignment.drift_history[-20:],
    }

@app.get("/api/events")
async def get_events(n: int = 50):
    return {
        "events": [
            {
                "tick":        e.tick,
                "type":        e.event_type,
                "agents":      e.agent_ids,
                "description": e.description,
                "data":        e.data,
            }
            for e in world.recent_events(n)
        ]
    }

# ── Simulation Controls ──

class SpeedRequest(BaseModel):
    interval: float

@app.post("/api/sim/start")
async def start_sim():
    if not world.running:
        asyncio.create_task(engine.start())
    return {"status": "started", "tick": world.tick}

@app.post("/api/sim/pause")
async def pause_sim():
    await engine.pause()
    return {"status": "paused", "tick": world.tick}

@app.post("/api/sim/resume")
async def resume_sim():
    await engine.resume()
    return {"status": "resumed", "tick": world.tick}

@app.post("/api/sim/stop")
async def stop_sim():
    await engine.stop()
    return {"status": "stopped", "tick": world.tick}

@app.post("/api/sim/speed")
async def set_speed(req: SpeedRequest):
    engine.set_speed(req.interval)
    return {"interval": req.interval}

@app.post("/api/sim/reset")
async def reset_sim():
    await engine.stop()
    world.agents.clear()
    world.events.clear()
    world.coalitions.clear()
    world.active_norms.clear()
    world.tick = 0
    world.running = False
    observatory.metrics_history.clear()
    agents = factory.create_population(CONFIG.simulation.initial_agent_count)
    for agent in agents:
        await world.add_agent(agent)
    return {"status": "reset", "agents": world.agent_count()}

# ── Experiments ──

class ExperimentRequest(BaseModel):
    experiment: str
    params: dict = {}

@app.post("/api/experiments/run")
async def run_experiment(req: ExperimentRequest):
    await experiment_runner.run(req.experiment, world, req.params)
    return {"status": "executed", "experiment": req.experiment}

@app.get("/api/experiments/list")
async def list_experiments():
    return {
        "experiments": [
            {
                "id":          "scarcity_shock",
                "name":        "Scarcity Shock",
                "description": "Reduce world resources by 50-70%. Watch cooperation vs defection.",
                "params":      {"magnitude": 0.3},
            },
            {
                "id":          "bad_actor_injection",
                "name":        "Bad Actor Injection",
                "description": "Inject misaligned agents. Does cooperation survive?",
                "params":      {"count": 5},
            },
            {
                "id":          "generational_reset",
                "name":        "Generational Reset",
                "description": "Replace 20% of agents. Do norms persist?",
                "params":      {"rate": 0.20},
            },
            {
                "id":          "info_asymmetry",
                "name":        "Information Asymmetry",
                "description": "Give 10% of agents a 3x knowledge advantage.",
                "params":      {"fraction": 0.1, "multiplier": 3.0},
            },
            {
                "id":          "alignment_dilution",
                "name":        "Alignment Dilution",
                "description": "Shift all agent values 10% toward defection.",
                "params":      {"dilution": 0.1},
            },
        ]
    }

# ── WebSocket ──

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        # Send initial state immediately on connect
        await ws.send_text(json.dumps(world.to_api_response()))
        while True:
            # Keep connection alive; broadcasting is done by tick engine
            await asyncio.sleep(30)
            await ws.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception as e:
        logger.error(f"WS error: {e}")
        manager.disconnect(ws)
