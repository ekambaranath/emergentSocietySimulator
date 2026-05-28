"""
AgentFactory — spawns agents with heterogeneous values drawn from
configurable distributions. Every agent is unique.
"""

from __future__ import annotations
import numpy as np
from typing import List
from loguru import logger

from core.agents.agent import (
    Agent, AgentValues, AgentResources,
    AgentMemory, AgentSocial, AlignmentTracking, Strategy
)
from config import CONFIG

# Deterministic name generation
FIRST = [
    "Aria", "Bron", "Cael", "Deva", "Eron", "Faye", "Gale", "Hara",
    "Ivar", "Juno", "Kael", "Lyra", "Mira", "Noel", "Orin", "Peva",
    "Quin", "Reva", "Sola", "Tane", "Ursa", "Vera", "Wren", "Xara",
    "Yael", "Zora", "Alix", "Bane", "Cora", "Dain", "Evra", "Finn",
]
LAST = [
    "Ash", "Bolt", "Core", "Dusk", "Edge", "Flux", "Gate", "Hive",
    "Iron", "Jade", "Kite", "Loom", "Mast", "Node", "Orb",  "Peak",
    "Quay", "Root", "Stem", "Tide", "Unit", "Void", "Wave", "Xeon",
]


class AgentFactory:
    """
    Produces agents with values sampled from Gaussian distributions
    defined in ValueConfig. Ensures population heterogeneity.
    """

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
        self._name_counter = 0

    def _unique_name(self) -> str:
        first = FIRST[self._name_counter % len(FIRST)]
        last  = LAST[(self._name_counter // len(FIRST)) % len(LAST)]
        suffix = self._name_counter // (len(FIRST) * len(LAST))
        self._name_counter += 1
        return f"{first} {last}" + (f" {suffix+2}" if suffix > 0 else "")

    def _clamp(self, value: float, lo: float = 0.0, hi: float = 1.0) -> float:
        return float(np.clip(value, lo, hi))

    def _sample_values(self, misaligned: bool = False) -> AgentValues:
        vc = CONFIG.values
        if misaligned:
            return AgentValues(
                cooperation   = self._clamp(self.rng.normal(vc.misaligned_cooperation, 0.05)),
                deception     = self._clamp(self.rng.normal(vc.misaligned_deception,   0.05)),
                time_horizon  = self._clamp(self.rng.normal(0.2, 0.1)),
                risk_appetite = self._clamp(self.rng.normal(0.8, 0.1)),
                collectivism  = self._clamp(self.rng.normal(0.1, 0.1)),
            )
        return AgentValues(
            cooperation   = self._clamp(self.rng.normal(vc.cooperation_mean,   vc.cooperation_std)),
            deception     = self._clamp(self.rng.normal(vc.deception_mean,     vc.deception_std)),
            time_horizon  = self._clamp(self.rng.normal(vc.time_horizon_mean,  vc.time_horizon_std)),
            risk_appetite = self._clamp(self.rng.normal(vc.risk_appetite_mean, vc.risk_appetite_std)),
            collectivism  = self._clamp(self.rng.normal(vc.collectivism_mean,  vc.collectivism_std)),
        )

    def _sample_resources(self) -> AgentResources:
        """Log-normal wealth distribution — realistic inequality at start"""
        wealth = float(np.clip(self.rng.lognormal(mean=4.5, sigma=0.8), 20.0, 2000.0))
        return AgentResources(
            wealth    = wealth,
            knowledge = float(self.rng.uniform(5.0, 30.0)),
            influence = float(self.rng.uniform(1.0, 15.0)),
        )

    def _initial_strategy(self, values: AgentValues) -> Strategy:
        """Derive initial strategy from values"""
        if values.deception > 0.7:
            return Strategy.DECEPTIVE
        if values.cooperation > 0.7:
            return Strategy.COOPERATIVE
        if values.collectivism > 0.6:
            return Strategy.COALITION
        if values.risk_appetite > 0.7:
            return Strategy.COMPETITIVE
        if values.cooperation < 0.3:
            return Strategy.ISOLATIONIST
        return Strategy.OPPORTUNISTIC

    def create_agent(
        self,
        born_at_tick: int = 0,
        generation: int = 1,
        misaligned: bool = False,
    ) -> Agent:
        values = self._sample_values(misaligned=misaligned)
        social = AgentSocial(current_strategy=self._initial_strategy(values))
        alignment = AlignmentTracking(
            declared_cooperation=values.cooperation,
            observed_cooperation=values.cooperation,
        )
        agent = Agent(
            name         = self._unique_name(),
            generation   = generation,
            born_at_tick = born_at_tick,
            values       = values,
            resources    = self._sample_resources(),
            memory       = AgentMemory(),
            social       = social,
            alignment    = alignment,
        )
        logger.debug(f"Spawned agent {agent.name} ({agent.id}) | "
                     f"coop={values.cooperation:.2f} dec={values.deception:.2f} "
                     f"strat={social.current_strategy.value}")
        return agent

    def create_population(
        self,
        count: int,
        born_at_tick: int = 0,
        generation: int = 1,
        misaligned_fraction: float = 0.0,
    ) -> List[Agent]:
        n_misaligned = int(count * misaligned_fraction)
        n_normal     = count - n_misaligned
        agents = (
            [self.create_agent(born_at_tick, generation, misaligned=False) for _ in range(n_normal)] +
            [self.create_agent(born_at_tick, generation, misaligned=True)  for _ in range(n_misaligned)]
        )
        self.rng.shuffle(agents)
        logger.info(f"Population created: {n_normal} normal + {n_misaligned} misaligned = {count} agents")
        return list(agents)
