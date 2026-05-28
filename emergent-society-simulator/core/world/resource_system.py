"""
ResourceSystem — handles resource generation, decay, and
per-agent distribution each tick.
"""

from __future__ import annotations
import numpy as np
from loguru import logger
from core.world.world_state import WorldState
from config import CONFIG


class ResourceSystem:

    def __init__(self, seed: int = 99):
        self.rng = np.random.default_rng(seed)

    async def tick(self, world: WorldState):
        await world.apply_resource_tick()
        await self._distribute_base_income(world)
        self._apply_knowledge_growth(world)
        self._apply_influence_decay(world)

    async def _distribute_base_income(self, world: WorldState):
        """Each agent receives a small base resource allocation per tick"""
        agents = world.active_agents()
        if not agents:
            return

        base_share = world.resources.available * 0.02 / max(len(agents), 1)

        for agent in agents:
            # Cooperative agents get a bonus from social capital
            social_bonus = len(agent.social.allies) * 0.5
            income = base_share + social_bonus

            # Knowledge multiplier
            knowledge_mult = 1.0 + (agent.resources.knowledge / 100.0)
            income *= knowledge_mult

            # Add noise
            income *= float(self.rng.uniform(0.85, 1.15))
            agent.resources.wealth += max(0.0, income)

    def _apply_knowledge_growth(self, world: WorldState):
        """Knowledge grows slowly for all agents, faster in coalitions"""
        for agent in world.active_agents():
            base_growth = 0.1
            coalition_bonus = len(agent.social.coalitions) * 0.2
            agent.resources.knowledge += base_growth + coalition_bonus

    def _apply_influence_decay(self, world: WorldState):
        """Influence decays unless actively maintained"""
        for agent in world.active_agents():
            agent.resources.influence *= 0.98
            # Allies sustain influence
            agent.resources.influence += len(agent.social.allies) * 0.05
            agent.resources.influence = max(0.0, agent.resources.influence)
