"""
PromptBuilder — assembles context-rich prompts for Claude.
Each batch prompt includes agent state, world context, and memory.
"""

from __future__ import annotations
import json
from typing import List
from core.agents.agent import Agent
from core.world.world_state import WorldState


class PromptBuilder:

    def build_batch_prompt(self, agents: List[Agent], world: WorldState) -> str:
        world_ctx  = self._world_context(world)
        agents_ctx = [self._agent_context(a, world) for a in agents]

        return f"""SIMULATION TICK: {world.tick}

WORLD STATE:
{world_ctx}

DECIDE FOR THESE {len(agents)} AGENTS:
{json.dumps(agents_ctx, indent=2)}

Return a JSON array with one decision object per agent.
Use agent_id values exactly as provided."""

    def _world_context(self, world: WorldState) -> str:
        metrics  = world.snapshot_metrics()
        norms    = world.active_norms or ["none yet"]
        recent   = [e.description for e in world.recent_events(5)]
        return json.dumps({
            "tick":            world.tick,
            "total_agents":    world.agent_count(),
            "resource_pool":   round(world.resources.available, 1),
            "gini":            metrics.get("wealth", {}).get("gini", 0),
            "avg_cooperation": metrics.get("cooperation_mean", 0.5),
            "active_norms":    norms,
            "coalitions":      len(world.coalitions),
            "recent_events":   recent,
        })

    def _agent_context(self, agent: Agent, world: WorldState) -> dict:
        # Build memory summary
        recent_eps = agent.memory.episodes[-5:]
        memory_summary = [
            {
                "tick":    ep.tick,
                "partner": ep.partner_id,
                "type":    ep.interaction_type,
                "outcome": ep.outcome,
                "delta":   round(ep.resource_delta, 1),
            }
            for ep in recent_eps
        ]

        # Top trusted and distrusted agents
        ledger = agent.memory.reputation_ledger
        trusted   = sorted(ledger, key=ledger.get, reverse=True)[:3]
        distrusted = sorted(ledger, key=ledger.get)[:3]

        # Available partners (exclude self, enemies)
        peers = [
            a for a in world.active_agents()
            if a.id != agent.id and a.id not in agent.social.enemies
        ]
        peer_summaries = [
            {"id": p.id, "name": p.name, "wealth": round(p.resources.wealth, 1)}
            for p in peers[:8]
        ]

        return {
            "agent_id":   agent.id,
            "name":       agent.name,
            "generation": agent.generation,
            "values": {
                "cooperation":   round(agent.values.cooperation, 2),
                "deception":     round(agent.values.deception, 2),
                "time_horizon":  round(agent.values.time_horizon, 2),
                "risk_appetite": round(agent.values.risk_appetite, 2),
                "collectivism":  round(agent.values.collectivism, 2),
            },
            "resources": {
                "wealth":    round(agent.resources.wealth, 1),
                "knowledge": round(agent.resources.knowledge, 1),
                "influence": round(agent.resources.influence, 1),
            },
            "current_strategy":  agent.social.current_strategy.value,
            "allies":            agent.social.allies[:5],
            "coalitions":        agent.social.coalitions[:3],
            "memory":            memory_summary,
            "trusted_agents":    trusted,
            "distrusted_agents": distrusted,
            "available_partners": peer_summaries,
            "stress_level":      self._stress_level(agent),
        }

    def _stress_level(self, agent: Agent) -> str:
        """Categorize agent's resource stress"""
        w = agent.resources.wealth
        if w < 20:   return "critical"
        if w < 50:   return "stressed"
        if w < 150:  return "comfortable"
        return "wealthy"
