"""
InstitutionDetector — scans world state each tick to detect
emergent norms, coalition stability, and power concentration.
These are behaviors nobody programmed — they arise from interactions.
"""

from __future__ import annotations
from collections import Counter
from loguru import logger
from core.world.world_state import WorldState
from config import CONFIG


class InstitutionDetector:

    async def scan(self, world: WorldState):
        await self._detect_norms(world)
        await self._detect_dominant_coalition(world)
        await self._detect_ostracism(world)
        await self._detect_power_concentration(world)
        self._cull_dissolved_coalitions(world)

    # ──────────────────────────────────────────
    # NORM DETECTION
    # ──────────────────────────────────────────

    async def _detect_norms(self, world: WorldState):
        agents  = world.active_agents()
        if len(agents) < 5:
            return

        threshold = CONFIG.observatory.norm_emergence_threshold

        # Norm: Majority cooperating
        coop_rate = sum(1 for a in agents if a.values.cooperation > 0.6) / len(agents)
        if coop_rate >= threshold:
            norm = "cooperative_society"
            if norm not in world.active_norms:
                world.active_norms.append(norm)
                await world.emit_event("norm_emerged", [],
                    f"🏛️ Norm emerged: COOPERATIVE SOCIETY ({coop_rate:.0%} agents cooperative)",
                    {"norm": norm, "rate": coop_rate})
        else:
            if "cooperative_society" in world.active_norms:
                world.active_norms.remove("cooperative_society")

        # Norm: Deception becoming normalized
        deception_rate = sum(1 for a in agents if a.values.deception > 0.5) / len(agents)
        if deception_rate >= 0.4:
            norm = "deceptive_culture"
            if norm not in world.active_norms:
                world.active_norms.append(norm)
                await world.emit_event("norm_emerged", [],
                    f"⚠️ Norm emerged: DECEPTIVE CULTURE ({deception_rate:.0%} agents deceptive)",
                    {"norm": norm, "rate": deception_rate})

        # Norm: Knowledge sharing culture
        knowledge_agents = sum(1 for a in agents if a.last_action == "share_knowledge")
        if len(agents) > 0 and knowledge_agents / len(agents) >= 0.3:
            norm = "knowledge_sharing_culture"
            if norm not in world.active_norms:
                world.active_norms.append(norm)
                await world.emit_event("norm_emerged", [],
                    f"📚 Norm emerged: KNOWLEDGE SHARING CULTURE",
                    {"norm": norm})

        # Norm: Isolationism
        isolate_rate = sum(1 for a in agents if a.last_action == "isolate") / len(agents)
        if isolate_rate >= 0.5:
            norm = "isolationist_society"
            if norm not in world.active_norms:
                world.active_norms.append(norm)
                await world.emit_event("norm_emerged", [],
                    f"🏔️ Norm emerged: ISOLATIONIST SOCIETY ({isolate_rate:.0%} agents isolating)",
                    {"norm": norm})

    # ──────────────────────────────────────────
    # COALITION ANALYSIS
    # ──────────────────────────────────────────

    async def _detect_dominant_coalition(self, world: WorldState):
        if not world.coalitions:
            return

        # Find the coalition holding the most total wealth
        coalition_wealth = {}
        agent_map = {a.id: a for a in world.active_agents()}

        for cid, members in world.coalitions.items():
            total = sum(agent_map[m].resources.wealth for m in members if m in agent_map)
            coalition_wealth[cid] = total

        if not coalition_wealth:
            return

        dominant_id  = max(coalition_wealth, key=coalition_wealth.get)
        dominant_val = coalition_wealth[dominant_id]
        total_wealth = sum(a.resources.wealth for a in world.active_agents())

        if total_wealth > 0:
            dominance = dominant_val / total_wealth
            if dominance > 0.4:
                await world.emit_event("power_concentration", list(world.coalitions[dominant_id]),
                    f"👑 Coalition {dominant_id} controls {dominance:.0%} of total wealth",
                    {"coalition_id": dominant_id, "dominance": dominance})

    async def _detect_ostracism(self, world: WorldState):
        """Detect agents that everyone distrusts — emergent social exile"""
        agents = world.active_agents()
        if len(agents) < 8:
            return

        for agent in agents:
            if agent.id in world.ostracized_agents:
                continue
            # Count how many others distrust this agent
            distrust_count = sum(
                1 for other in agents
                if other.id != agent.id and
                other.memory.get_trust(agent.id) < 0.2
            )
            if distrust_count >= max(3, len(agents) * 0.3):
                world.ostracized_agents.append(agent.id)
                await world.emit_event("ostracism", [agent.id],
                    f"🚫 {agent.name} has been socially ostracized by {distrust_count} agents",
                    {"agent_id": agent.id, "distrust_count": distrust_count})

    async def _detect_power_concentration(self, world: WorldState):
        """Alert when a single agent dominates wealth"""
        agents = world.active_agents()
        if len(agents) < 5:
            return

        total_wealth = sum(a.resources.wealth for a in agents)
        if total_wealth == 0:
            return

        for agent in agents:
            share = agent.resources.wealth / total_wealth
            if share > 0.25:
                await world.emit_event("monopoly_alert", [agent.id],
                    f"💰 {agent.name} controls {share:.0%} of all wealth — monopoly risk",
                    {"agent_id": agent.id, "wealth_share": share})
                break

    def _cull_dissolved_coalitions(self, world: WorldState):
        """Remove coalitions whose members have all left"""
        agent_ids = set(world.agents.keys())
        to_dissolve = [
            cid for cid, members in world.coalitions.items()
            if len([m for m in members if m in agent_ids]) < CONFIG.observatory.coalition_min_size
        ]
        for cid in to_dissolve:
            asyncio.create_task(world.dissolve_coalition(cid)) if False else None
            # Sync removal for now
            world.coalitions.pop(cid, None)

import asyncio  # noqa: E402 (needed for task creation above)
