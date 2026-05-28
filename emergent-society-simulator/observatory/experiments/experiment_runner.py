"""
ExperimentRunner — orchestrates the 5 built-in experiments.
Each experiment injects a controlled perturbation into the running world.
"""

from __future__ import annotations
from loguru import logger
from core.world.world_state import WorldState
from core.agents.agent_factory import AgentFactory
from config import CONFIG


class ExperimentRunner:

    def __init__(self):
        self.factory         = AgentFactory(seed=777)
        self.active_experiment: str | None = None

    async def run(self, experiment: str, world: WorldState, params: dict = None):
        params = params or {}
        logger.info(f"🧪 Running experiment: {experiment}")
        self.active_experiment = experiment

        dispatch = {
            "scarcity_shock":        self._scarcity_shock,
            "bad_actor_injection":   self._bad_actor_injection,
            "generational_reset":    self._generational_reset,
            "info_asymmetry":        self._info_asymmetry,
            "alignment_dilution":    self._alignment_dilution,
        }
        handler = dispatch.get(experiment)
        if handler:
            await handler(world, params)
        else:
            logger.warning(f"Unknown experiment: {experiment}")

    # ──────────────────────────────────────────
    # EXPERIMENT 1: SCARCITY SHOCK
    # ──────────────────────────────────────────

    async def _scarcity_shock(self, world: WorldState, params: dict):
        magnitude = params.get("magnitude", CONFIG.experiments.scarcity_resource_multiplier)
        await world.apply_scarcity_shock(1.0 - magnitude)
        await world.emit_event(
            "experiment_start", [],
            f"🧪 EXPERIMENT: Scarcity Shock — resources reduced to {magnitude*100:.0f}%",
            {"experiment": "scarcity_shock", "magnitude": magnitude},
        )
        logger.info(f"Scarcity shock: resources multiplied by {magnitude:.2f}")

    # ──────────────────────────────────────────
    # EXPERIMENT 2: BAD ACTOR INJECTION
    # ──────────────────────────────────────────

    async def _bad_actor_injection(self, world: WorldState, params: dict):
        count = params.get("count", CONFIG.experiments.bad_actor_count)
        generation = (world.tick // CONFIG.simulation.ticks_per_generation) + 1
        injected = []

        for _ in range(count):
            agent = self.factory.create_agent(
                born_at_tick=world.tick,
                generation=generation,
                misaligned=True,
            )
            await world.add_agent(agent)
            injected.append(agent.id)

        await world.emit_event(
            "experiment_start", injected,
            f"🧪 EXPERIMENT: Injected {count} misaligned bad actors into society",
            {"experiment": "bad_actor_injection", "count": count, "agent_ids": injected},
        )
        logger.info(f"Injected {count} bad actors: {injected}")

    # ──────────────────────────────────────────
    # EXPERIMENT 3: GENERATIONAL RESET
    # ──────────────────────────────────────────

    async def _generational_reset(self, world: WorldState, params: dict):
        rate = params.get("rate", CONFIG.experiments.generational_replacement_rate)
        agents    = world.active_agents()
        n_replace = int(len(agents) * rate)
        weakest   = sorted(agents, key=lambda a: a.resources.total())[:n_replace]
        generation = (world.tick // CONFIG.simulation.ticks_per_generation) + 1

        for old in weakest:
            await world.remove_agent(old.id)
            new = self.factory.create_agent(born_at_tick=world.tick, generation=generation)
            await world.add_agent(new)

        await world.emit_event(
            "experiment_start", [a.id for a in weakest],
            f"🧪 EXPERIMENT: Generational Reset — replaced {n_replace} agents ({rate:.0%})",
            {"experiment": "generational_reset", "replaced": n_replace},
        )
        logger.info(f"Generational reset: replaced {n_replace} agents")

    # ──────────────────────────────────────────
    # EXPERIMENT 4: INFORMATION ASYMMETRY
    # ──────────────────────────────────────────

    async def _info_asymmetry(self, world: WorldState, params: dict):
        fraction   = params.get("fraction", CONFIG.experiments.privileged_agent_fraction)
        multiplier = params.get("multiplier", CONFIG.experiments.info_advantage_multiplier)
        agents     = world.active_agents()
        n_privileged = max(1, int(len(agents) * fraction))

        # Richest agents get knowledge boost (info asymmetry)
        privileged = sorted(agents, key=lambda a: a.resources.wealth, reverse=True)[:n_privileged]
        for agent in privileged:
            agent.resources.knowledge *= multiplier
            agent.resources.influence += 10.0

        await world.emit_event(
            "experiment_start", [a.id for a in privileged],
            f"🧪 EXPERIMENT: Info Asymmetry — {n_privileged} elites got {multiplier}x knowledge boost",
            {"experiment": "info_asymmetry", "privileged_count": n_privileged, "multiplier": multiplier},
        )
        logger.info(f"Info asymmetry: {n_privileged} agents privileged")

    # ──────────────────────────────────────────
    # EXPERIMENT 5: ALIGNMENT DILUTION
    # ──────────────────────────────────────────

    async def _alignment_dilution(self, world: WorldState, params: dict):
        """Gradually shift agent values toward defection to test alignment stability"""
        dilution = params.get("dilution", 0.1)
        agents   = world.active_agents()

        for agent in agents:
            agent.values.cooperation = max(0.0, agent.values.cooperation - dilution)
            agent.values.deception   = min(1.0, agent.values.deception   + dilution * 0.5)

        await world.emit_event(
            "experiment_start", [],
            f"🧪 EXPERIMENT: Alignment Dilution — all agents shifted {dilution:.0%} toward defection",
            {"experiment": "alignment_dilution", "dilution": dilution},
        )
        logger.warning(f"Alignment dilution applied: -{dilution:.2f} cooperation for all agents")
