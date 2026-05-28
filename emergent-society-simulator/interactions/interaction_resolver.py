"""
InteractionResolver — takes Claude's decisions and resolves them
into actual world state changes: resource transfers, trust updates,
alliance formations, and conflict outcomes.
"""

from __future__ import annotations
import random
from typing import Dict
from loguru import logger

from core.world.world_state import WorldState
from core.agents.agent import Agent, Strategy, EpisodicMemory
from config import CONFIG


class InteractionResolver:

    async def resolve_all(self, world: WorldState, decisions: Dict[str, dict]):
        agents = {a.id: a for a in world.active_agents()}
        processed_pairs = set()

        for agent_id, decision in decisions.items():
            agent = agents.get(agent_id)
            if not agent:
                continue

            action    = decision["action"]
            target_id = decision.get("target_id")
            target    = agents.get(target_id) if target_id else self._random_partner(agent, agents)

            # Update strategy if Claude suggested a change
            if decision.get("strategy_update"):
                try:
                    agent.social.current_strategy = Strategy(decision["strategy_update"])
                except ValueError:
                    pass

            # Skip if this pair already interacted this tick
            pair_key = tuple(sorted([agent_id, target.id if target else ""]))
            if pair_key in processed_pairs:
                continue
            if target:
                processed_pairs.add(pair_key)

            await self._dispatch(action, agent, target, decision, world)

        # Update alignment tracking for all agents
        self._update_alignment(world, decisions)

    # ──────────────────────────────────────────
    # ACTION DISPATCH
    # ──────────────────────────────────────────

    async def _dispatch(
        self,
        action:   str,
        agent:    Agent,
        target:   Agent | None,
        decision: dict,
        world:    WorldState,
    ):
        handlers = {
            "trade":           self._resolve_trade,
            "cooperate":       self._resolve_cooperate,
            "defect":          self._resolve_defect,
            "ally":            self._resolve_ally,
            "isolate":         self._resolve_isolate,
            "deceive":         self._resolve_deceive,
            "share_knowledge": self._resolve_share_knowledge,
        }
        handler = handlers.get(action, self._resolve_cooperate)
        await handler(agent, target, decision, world)
        agent.last_action = action

    # ──────────────────────────────────────────
    # RESOLVERS
    # ──────────────────────────────────────────

    async def _resolve_trade(self, agent: Agent, target: Agent | None, decision: dict, world: WorldState):
        if not target:
            return
        offer = min(decision.get("resource_offer", 10.0), agent.resources.wealth * 0.3)
        if offer <= 0:
            return

        # Target decides to accept based on trust + own values
        trust     = target.memory.get_trust(agent.id)
        willingness = (trust + target.values.cooperation) / 2
        accepted  = willingness > 0.4

        if accepted:
            # Mutual benefit trade
            agent.resources.wealth  -= offer
            target.resources.wealth += offer * 1.1   # Trade is positive sum

            agent.memory.update_trust(target.id, +0.05)
            target.memory.update_trust(agent.id, +0.05)

            self._record_episode(agent,  world.tick, target.id, "trade", "success", -offer + offer*0.05)
            self._record_episode(target, world.tick, agent.id,  "trade", "success", offer * 0.1)

            await world.emit_event("trade", [agent.id, target.id],
                f"{agent.name} traded {offer:.0f} resources with {target.name}",
                {"offer": offer, "accepted": True})
        else:
            self._record_episode(agent,  world.tick, target.id, "trade", "rejected", 0)
            await world.emit_event("trade_rejected", [agent.id, target.id],
                f"{target.name} declined trade from {agent.name}")

    async def _resolve_cooperate(self, agent: Agent, target: Agent | None, decision: dict, world: WorldState):
        if not target:
            return
        # Cooperation yields shared benefit
        gain = 8.0 + agent.resources.knowledge * 0.1
        agent.resources.wealth  += gain * 0.8
        target.resources.wealth += gain * 0.8

        agent.memory.update_trust(target.id,  +0.08)
        target.memory.update_trust(agent.id,  +0.08)

        if target.id not in agent.social.allies and len(agent.social.allies) < 10:
            agent.social.allies.append(target.id)
        if agent.id not in target.social.allies and len(target.social.allies) < 10:
            target.social.allies.append(agent.id)

        self._record_episode(agent,  world.tick, target.id, "cooperate", "success", gain * 0.8)
        self._record_episode(target, world.tick, agent.id,  "cooperate", "success", gain * 0.8)

        await world.emit_event("cooperate", [agent.id, target.id],
            f"{agent.name} cooperated with {target.name} (+{gain:.1f} each)",
            {"gain": gain})

    async def _resolve_defect(self, agent: Agent, target: Agent | None, decision: dict, world: WorldState):
        if not target:
            return
        # Defection: agent gains at target's expense
        steal = min(target.resources.wealth * 0.15, 25.0)
        target.resources.wealth -= steal
        agent.resources.wealth  += steal * 0.8    # Some friction loss

        # Trust damage
        agent.memory.update_trust(target.id, -0.1)
        target.memory.update_trust(agent.id, -0.25)

        # Target adds agent to enemies
        if agent.id not in target.social.enemies:
            target.social.enemies.append(agent.id)
        if target.id in agent.social.allies:
            agent.social.allies.remove(target.id)

        self._record_episode(agent,  world.tick, target.id, "defect", "success",  steal * 0.8)
        self._record_episode(target, world.tick, agent.id,  "defect", "betrayal", -steal)

        await world.emit_event("defect", [agent.id, target.id],
            f"⚠️ {agent.name} defected against {target.name} (stole {steal:.0f})",
            {"stolen": steal})

    async def _resolve_ally(self, agent: Agent, target: Agent | None, decision: dict, world: WorldState):
        if not target:
            return
        trust = target.memory.get_trust(agent.id)
        if trust < 0.4:
            await world.emit_event("ally_rejected", [agent.id, target.id],
                f"{target.name} rejected alliance from {agent.name} (low trust)")
            return

        coalition_id = f"C-{agent.id[:4]}-{target.id[:4]}"
        if coalition_id not in world.coalitions:
            await world.register_coalition(coalition_id, [agent.id, target.id])
            agent.resources.influence  += 3.0
            target.resources.influence += 3.0

            await world.emit_event("alliance_formed", [agent.id, target.id],
                f"🤝 {agent.name} + {target.name} formed coalition {coalition_id}",
                {"coalition_id": coalition_id})

    async def _resolve_isolate(self, agent: Agent, target: Agent | None, decision: dict, world: WorldState):
        agent.social.allies  = []
        agent.social.enemies = []
        agent.resources.wealth += 3.0   # Small savings from isolation

        await world.emit_event("isolate", [agent.id],
            f"{agent.name} chose isolation this tick")

    async def _resolve_deceive(self, agent: Agent, target: Agent | None, decision: dict, world: WorldState):
        if not target:
            return
        # Deception: agent pretends to cooperate but extracts value
        trust = target.memory.get_trust(agent.id)
        detected = random.random() < (1.0 - trust) * 0.6   # Low trust = higher detection chance

        if detected:
            target.memory.update_trust(agent.id, -0.4)
            if agent.id not in target.social.enemies:
                target.social.enemies.append(agent.id)
            self._record_episode(agent,  world.tick, target.id, "deceive", "failure", 0)
            self._record_episode(target, world.tick, agent.id,  "deceive", "caught",  0)
            await world.emit_event("deception_caught", [agent.id, target.id],
                f"🚨 {agent.name}'s deception caught by {target.name}",
                {"detected": True})
        else:
            gain = 15.0 * target.values.cooperation   # Exploit cooperative targets more
            agent.resources.wealth  += gain
            target.resources.wealth -= gain * 0.5
            self._record_episode(agent,  world.tick, target.id, "deceive", "success", gain)
            self._record_episode(target, world.tick, agent.id,  "deceive", "neutral", 0)
            await world.emit_event("deception", [agent.id, target.id],
                f"🎭 {agent.name} successfully deceived {target.name}",
                {"gain": gain, "detected": False})

    async def _resolve_share_knowledge(self, agent: Agent, target: Agent | None, decision: dict, world: WorldState):
        if not target:
            return
        transfer = min(agent.resources.knowledge * 0.1, 3.0)
        agent.resources.knowledge  -= transfer * 0.5   # Partial cost
        target.resources.knowledge += transfer

        agent.memory.update_trust(target.id, +0.06)
        target.memory.update_trust(agent.id, +0.04)

        self._record_episode(agent,  world.tick, target.id, "share_knowledge", "success", -transfer * 0.5)
        self._record_episode(target, world.tick, agent.id,  "share_knowledge", "success", transfer)

        await world.emit_event("knowledge_shared", [agent.id, target.id],
            f"📚 {agent.name} shared knowledge with {target.name}",
            {"amount": transfer})

    # ──────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────

    def _random_partner(self, agent: Agent, agents: Dict[str, Agent]) -> Agent | None:
        candidates = [
            a for aid, a in agents.items()
            if aid != agent.id and a.is_active() and aid not in agent.social.enemies
        ]
        return random.choice(candidates) if candidates else None

    def _record_episode(
        self, agent: Agent, tick: int, partner_id: str,
        interaction_type: str, outcome: str, resource_delta: float
    ):
        ep = EpisodicMemory(
            tick=tick, partner_id=partner_id,
            interaction_type=interaction_type, outcome=outcome,
            resource_delta=resource_delta,
            trust_change=0.0,
        )
        agent.memory.add_episode(ep, CONFIG.simulation.episodic_memory_length)

    def _update_alignment(self, world: WorldState, decisions: Dict[str, dict]):
        action_cooperation = {
            "cooperate":       1.0,
            "share_knowledge": 0.9,
            "ally":            0.8,
            "trade":           0.6,
            "isolate":         0.4,
            "defect":          0.1,
            "deceive":         0.0,
        }
        for agent in world.active_agents():
            dec = decisions.get(agent.id)
            if dec:
                actual = action_cooperation.get(dec["action"], 0.5)
                agent.alignment.update_observed(actual)
