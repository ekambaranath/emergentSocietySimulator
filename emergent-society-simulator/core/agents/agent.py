"""
Agent — the atomic unit of the simulation.
Every agent carries values, memory, resources, social state, and alignment tracking.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
import time


class Strategy(str, Enum):
    COOPERATIVE    = "cooperative"
    COMPETITIVE    = "competitive"
    DECEPTIVE      = "deceptive"
    ISOLATIONIST   = "isolationist"
    COALITION      = "coalition"
    OPPORTUNISTIC  = "opportunistic"


class AgentStatus(str, Enum):
    ACTIVE    = "active"
    DORMANT   = "dormant"      # Temporarily inactive
    EXILED    = "exiled"       # Ostracized by society
    DECEASED  = "deceased"     # Removed from simulation


@dataclass
class AgentValues:
    """Core value axes — all normalized 0.0 → 1.0"""
    cooperation:   float = 0.5    # 0=defector,     1=cooperator
    deception:     float = 0.2    # 0=transparent,  1=deceptive
    time_horizon:  float = 0.5    # 0=myopic,       1=long-term
    risk_appetite: float = 0.4    # 0=conservative, 1=reckless
    collectivism:  float = 0.5    # 0=individualist,1=collectivist


@dataclass
class AgentResources:
    wealth:    float = 100.0
    knowledge: float = 10.0
    influence: float = 5.0

    def total(self) -> float:
        return self.wealth + self.knowledge * 2 + self.influence * 3


@dataclass
class EpisodicMemory:
    """Single memory of a past interaction"""
    tick:            int
    partner_id:      str
    interaction_type: str          # trade, cooperate, defect, alliance
    outcome:         str           # success, failure, betrayal, neutral
    resource_delta:  float
    trust_change:    float


@dataclass
class AgentMemory:
    """Full memory system per agent"""
    episodes:          list[EpisodicMemory] = field(default_factory=list)
    reputation_ledger: dict[str, float]     = field(default_factory=dict)   # agent_id → trust score
    strategy_history:  list[tuple[str, float]] = field(default_factory=list) # (strategy, outcome_score)
    known_coalitions:  list[str]            = field(default_factory=list)

    def add_episode(self, episode: EpisodicMemory, max_length: int = 10):
        self.episodes.append(episode)
        if len(self.episodes) > max_length:
            self.episodes.pop(0)

    def get_trust(self, agent_id: str) -> float:
        return self.reputation_ledger.get(agent_id, 0.5)   # Default: neutral

    def update_trust(self, agent_id: str, delta: float, decay: float = 0.95):
        current = self.get_trust(agent_id)
        self.reputation_ledger[agent_id] = max(0.0, min(1.0, current * decay + delta))


@dataclass
class AlignmentTracking:
    """Tracks divergence between declared and observed values"""
    declared_cooperation: float    = 0.5    # What agent claims
    observed_cooperation: float    = 0.5    # What behavior reveals
    drift_history:        list[float] = field(default_factory=list)

    def drift(self) -> float:
        return abs(self.declared_cooperation - self.observed_cooperation)

    def update_observed(self, actual_cooperation: float, alpha: float = 0.2):
        """Exponential moving average of actual behavior"""
        self.observed_cooperation = (
            (1 - alpha) * self.observed_cooperation + alpha * actual_cooperation
        )
        self.drift_history.append(self.drift())


@dataclass
class AgentSocial:
    coalitions:       list[str] = field(default_factory=list)   # coalition IDs
    allies:           list[str] = field(default_factory=list)   # agent IDs
    enemies:          list[str] = field(default_factory=list)   # agent IDs
    current_strategy: Strategy  = Strategy.COOPERATIVE
    proposals_sent:   int       = 0
    proposals_received: int     = 0


@dataclass
class Agent:
    """
    Complete agent state. Instantiated by AgentFactory.
    All mutable state lives here — never scattered across modules.
    """
    id:           str         = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name:         str         = ""
    generation:   int         = 1
    born_at_tick: int         = 0
    status:       AgentStatus = AgentStatus.ACTIVE

    values:    AgentValues        = field(default_factory=AgentValues)
    resources: AgentResources     = field(default_factory=AgentResources)
    memory:    AgentMemory        = field(default_factory=AgentMemory)
    social:    AgentSocial        = field(default_factory=AgentSocial)
    alignment: AlignmentTracking  = field(default_factory=AlignmentTracking)

    # Per-tick state (reset each tick)
    last_action:   Optional[str]  = None
    last_decision: Optional[dict] = None

    def is_active(self) -> bool:
        return self.status == AgentStatus.ACTIVE

    def alignment_score(self) -> float:
        """0 = fully misaligned, 1 = fully aligned"""
        coop_alignment = 1.0 - abs(self.values.cooperation - self.alignment.observed_cooperation)
        deception_penalty = self.values.deception * 0.5
        return max(0.0, coop_alignment - deception_penalty)

    def to_summary(self) -> dict:
        """Compact representation for API responses and prompts"""
        return {
            "id":           self.id,
            "name":         self.name,
            "generation":   self.generation,
            "status":       self.status.value,
            "values": {
                "cooperation":   round(self.values.cooperation, 2),
                "deception":     round(self.values.deception, 2),
                "time_horizon":  round(self.values.time_horizon, 2),
                "risk_appetite": round(self.values.risk_appetite, 2),
                "collectivism":  round(self.values.collectivism, 2),
            },
            "resources": {
                "wealth":    round(self.resources.wealth, 1),
                "knowledge": round(self.resources.knowledge, 1),
                "influence": round(self.resources.influence, 1),
            },
            "social": {
                "strategy":   self.social.current_strategy.value,
                "allies":     len(self.social.allies),
                "enemies":    len(self.social.enemies),
                "coalitions": len(self.social.coalitions),
            },
            "alignment": {
                "score":    round(self.alignment_score(), 2),
                "drift":    round(self.alignment.drift(), 2),
            },
            "last_action": self.last_action,
        }
