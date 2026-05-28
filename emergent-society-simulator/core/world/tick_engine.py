"""
TickEngine — orchestrates one simulation tick end-to-end.
Each tick: resources → AI decisions → interactions → institutions → metrics.
"""

from __future__ import annotations
import asyncio
import time
from loguru import logger

from core.world.world_state import WorldState
from config import CONFIG


class TickEngine:
    """
    Drives the simulation forward one tick at a time.
    Holds references to all subsystems and calls them in order.
    Subsystems are injected at runtime to avoid circular imports.
    """

    def __init__(self, world: WorldState):
        self.world          = world
        self.tick_interval  = CONFIG.simulation.tick_interval_seconds
        self._task: asyncio.Task | None = None

        # Injected subsystems (set by main.py after construction)
        self.resource_system      = None
        self.decision_engine      = None
        self.interaction_resolver = None
        self.institution_detector = None
        self.observatory          = None
        self.ws_broadcaster       = None

    # ──────────────────────────────────────────
    # LIFECYCLE
    # ──────────────────────────────────────────

    async def start(self):
        if self.world.running:
            logger.warning("TickEngine already running")
            return
        self.world.running   = True
        self.world.paused    = False
        self.world.started_at = time.time()
        self._task = asyncio.create_task(self._loop())
        logger.info("TickEngine started")

    async def pause(self):
        self.world.paused = True
        logger.info(f"Simulation paused at tick {self.world.tick}")

    async def resume(self):
        self.world.paused = False
        logger.info(f"Simulation resumed at tick {self.world.tick}")

    async def stop(self):
        self.world.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"TickEngine stopped at tick {self.world.tick}")

    def set_speed(self, interval: float):
        """Adjust real-time seconds per tick"""
        self.tick_interval = max(0.5, interval)
        logger.info(f"Tick interval set to {self.tick_interval}s")

    # ──────────────────────────────────────────
    # MAIN LOOP
    # ──────────────────────────────────────────

    async def _loop(self):
        while self.world.running:
            if not self.world.paused:
                tick_start = time.time()
                try:
                    await self._execute_tick()
                except Exception as e:
                    logger.error(f"Tick {self.world.tick} error: {e}", exc_info=True)

                elapsed  = time.time() - tick_start
                sleep_for = max(0.0, self.tick_interval - elapsed)
                logger.debug(f"Tick {self.world.tick} completed in {elapsed:.2f}s | sleeping {sleep_for:.2f}s")
                await asyncio.sleep(sleep_for)
            else:
                await asyncio.sleep(0.2)

    # ──────────────────────────────────────────
    # TICK EXECUTION — ordered pipeline
    # ──────────────────────────────────────────

    async def _execute_tick(self):
        self.world.tick += 1
        tick = self.world.tick
        logger.info(f"━━━ Tick {tick} | Agents: {self.world.agent_count()} ━━━")

        # 1. Resource system: regenerate, decay, redistribute
        if self.resource_system:
            await self.resource_system.tick(self.world)

        # 2. AI decision engine: batch Claude calls for all agents
        decisions = {}
        if self.decision_engine:
            decisions = await self.decision_engine.decide_all(self.world)

        # 3. Interaction resolver: execute trade/cooperate/defect/alliance
        if self.interaction_resolver and decisions:
            await self.interaction_resolver.resolve_all(self.world, decisions)

        # 4. Institution detector: scan for emergent norms & coalitions
        if self.institution_detector:
            await self.institution_detector.scan(self.world)

        # 5. Observatory: record metrics, snapshots, logs
        if self.observatory:
            await self.observatory.record_tick(self.world)

        # 6. Generational turnover check
        if tick % CONFIG.simulation.ticks_per_generation == 0:
            await self._generational_tick()

        # 7. Broadcast to WebSocket clients
        if self.ws_broadcaster:
            await self.ws_broadcaster.broadcast(self.world.to_api_response())

    async def _generational_tick(self):
        """Replace a fraction of agents each generation"""
        from core.agents.agent_factory import AgentFactory
        agents    = self.world.active_agents()
        n_replace = int(len(agents) * CONFIG.simulation.resource_regen_rate)
        if n_replace == 0:
            return

        # Sort by resources — weakest agents are replaced
        weakest = sorted(agents, key=lambda a: a.resources.total())[:n_replace]
        factory = AgentFactory()
        generation = (self.world.tick // CONFIG.simulation.ticks_per_generation) + 1

        for old_agent in weakest:
            await self.world.remove_agent(old_agent.id)
            new_agent = factory.create_agent(
                born_at_tick=self.world.tick,
                generation=generation,
            )
            await self.world.add_agent(new_agent)

        logger.info(f"Generation {generation}: replaced {n_replace} agents")
        await self.world.emit_event(
            "generational_turnover",
            [a.id for a in weakest],
            f"Generation {generation}: {n_replace} agents replaced",
            {"generation": generation, "replaced": n_replace},
        )
