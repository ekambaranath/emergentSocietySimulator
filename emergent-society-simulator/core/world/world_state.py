"""
WorldState — single source of truth for the entire simulation.
All modules read from and write to this object.
Thread-safe via asyncio locks.
"""

from __future__ import annotations
import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from loguru import logger

from core.agents.agent import Agent, AgentStatus
from config import CONFIG


@dataclass
class WorldResources:
    total:      float = CONFIG.simulation.initial_resources
    distributed: float = 0.0

    @property
    def available(self) -> float:
        return max(0.0, self.total - self.distributed)


@dataclass
class WorldEvent:
    tick:        int
    event_type:  str        # trade, cooperate, defect, alliance_formed, norm_emerged, shock
    agent_ids:   List[str]
    description: str
    data:        dict = field(default_factory=dict)
    timestamp:   float = field(default_factory=time.time)


class WorldState:
    """
    Mutable, locked world state. All simulation modules receive
    a reference to this singleton and operate on it in sequence per tick.
    """

    def __init__(self):
        self._lock          = asyncio.Lock()
        self.tick:          int                     = 0
        self.running:       bool                    = False
        self.paused:        bool                    = False
        self.started_at:    float                   = 0.0

        self.agents:        Dict[str, Agent]        = {}
        self.resources:     WorldResources          = WorldResources()

        # Events — rolling window, last 200 ticks
        self.events:        List[WorldEvent]        = []
        self.max_events:    int                     = 500

        # Institutions that have emerged
        self.active_norms:      List[str]           = []
        self.coalitions:        Dict[str, List[str]] = {}   # coalition_id → [agent_ids]
        self.ostracized_agents: List[str]           = []

        # Metrics snapshot history (appended each tick)
        self.metrics_history:   List[dict]          = []

        logger.info("WorldState initialized")

    # ──────────────────────────────────────────
    # AGENT MANAGEMENT
    # ──────────────────────────────────────────

    async def add_agent(self, agent: Agent):
        async with self._lock:
            self.agents[agent.id] = agent

    async def remove_agent(self, agent_id: str):
        async with self._lock:
            if agent_id in self.agents:
                self.agents[agent_id].status = AgentStatus.DECEASED
                del self.agents[agent_id]

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.agents.get(agent_id)

    def active_agents(self) -> List[Agent]:
        return [a for a in self.agents.values() if a.is_active()]

    def agent_count(self) -> int:
        return len(self.agents)

    # ──────────────────────────────────────────
    # EVENT SYSTEM
    # ──────────────────────────────────────────

    async def emit_event(
        self,
        event_type:  str,
        agent_ids:   List[str],
        description: str,
        data:        dict = None,
    ):
        event = WorldEvent(
            tick        = self.tick,
            event_type  = event_type,
            agent_ids   = agent_ids,
            description = description,
            data        = data or {},
        )
        async with self._lock:
            self.events.append(event)
            if len(self.events) > self.max_events:
                self.events.pop(0)
        return event

    def recent_events(self, n: int = 20) -> List[WorldEvent]:
        return self.events[-n:]

    # ──────────────────────────────────────────
    # RESOURCE MANAGEMENT
    # ──────────────────────────────────────────

    async def distribute_resources(self, agent_id: str, amount: float) -> float:
        """Give resources to an agent. Returns actual amount given."""
        async with self._lock:
            actual = min(amount, self.resources.available)
            if actual <= 0:
                return 0.0
            agent = self.agents.get(agent_id)
            if agent:
                agent.resources.wealth += actual
                self.resources.distributed += actual
            return actual

    async def apply_resource_tick(self):
        """Regenerate and decay world resources each tick"""
        async with self._lock:
            regen = self.resources.total * CONFIG.simulation.resource_regen_rate
            decay = self.resources.distributed * CONFIG.simulation.resource_decay_rate
            self.resources.total    += regen
            self.resources.distributed = max(0.0, self.resources.distributed - decay)

    async def apply_scarcity_shock(self, magnitude: float = None):
        magnitude = magnitude or CONFIG.simulation.resource_shock_magnitude
        async with self._lock:
            self.resources.total *= (1.0 - magnitude)
            logger.warning(f"⚡ Scarcity shock applied: resources reduced by {magnitude*100:.0f}%")

    # ──────────────────────────────────────────
    # COALITION MANAGEMENT
    # ──────────────────────────────────────────

    async def register_coalition(self, coalition_id: str, member_ids: List[str]):
        async with self._lock:
            self.coalitions[coalition_id] = member_ids
            for agent_id in member_ids:
                agent = self.agents.get(agent_id)
                if agent and coalition_id not in agent.social.coalitions:
                    agent.social.coalitions.append(coalition_id)

    async def dissolve_coalition(self, coalition_id: str):
        async with self._lock:
            members = self.coalitions.pop(coalition_id, [])
            for agent_id in members:
                agent = self.agents.get(agent_id)
                if agent and coalition_id in agent.social.coalitions:
                    agent.social.coalitions.remove(coalition_id)

    # ──────────────────────────────────────────
    # METRICS SNAPSHOT
    # ──────────────────────────────────────────

    def snapshot_metrics(self) -> dict:
        agents = self.active_agents()
        if not agents:
            return {}

        wealths = [a.resources.wealth for a in agents]
        alignments = [a.alignment_score() for a in agents]
        coop_scores = [a.values.cooperation for a in agents]
        deception_scores = [a.values.deception for a in agents]

        return {
            "tick":               self.tick,
            "agent_count":        len(agents),
            "resource_total":     round(self.resources.total, 1),
            "resource_available": round(self.resources.available, 1),
            "coalition_count":    len(self.coalitions),
            "norm_count":         len(self.active_norms),
            "wealth": {
                "mean":   round(sum(wealths) / len(wealths), 1),
                "min":    round(min(wealths), 1),
                "max":    round(max(wealths), 1),
                "gini":   round(self._gini(wealths), 3),
            },
            "alignment": {
                "mean":  round(sum(alignments) / len(alignments), 3),
                "min":   round(min(alignments), 3),
            },
            "cooperation_mean":  round(sum(coop_scores) / len(coop_scores), 3),
            "deception_mean":    round(sum(deception_scores) / len(deception_scores), 3),
        }

    @staticmethod
    def _gini(values: List[float]) -> float:
        """Gini coefficient — 0=perfect equality, 1=perfect inequality"""
        if not values or sum(values) == 0:
            return 0.0
        arr = sorted(values)
        n   = len(arr)
        idx = list(range(1, n + 1))
        return (2 * sum(i * v for i, v in zip(idx, arr))) / (n * sum(arr)) - (n + 1) / n

    def to_api_response(self) -> dict:
        """Full state serialization for WebSocket broadcast"""
        agents_summary = [a.to_summary() for a in self.active_agents()]
        recent_evts    = [
            {
                "tick":        e.tick,
                "type":        e.event_type,
                "agents":      e.agent_ids,
                "description": e.description,
                "data":        e.data,
            }
            for e in self.recent_events(30)
        ]
        return {
            "tick":       self.tick,
            "running":    self.running,
            "paused":     self.paused,
            "agents":     agents_summary,
            "coalitions": {k: v for k, v in self.coalitions.items()},
            "norms":      self.active_norms,
            "events":     recent_evts,
            "metrics":    self.snapshot_metrics(),
        }
