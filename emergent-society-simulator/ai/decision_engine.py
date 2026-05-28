"""
DecisionEngine — Ollama-powered AI brain of the simulation.
Batches agents, sends context-rich prompts to a local Ollama model,
parses structured JSON decisions back to the world.
No API key required — runs 100% locally.
"""

from __future__ import annotations
import asyncio
import json
import aiohttp
from typing import Dict, List
from loguru import logger

from core.world.world_state import WorldState
from core.agents.agent import Agent, Strategy
from ai.prompt_builder import PromptBuilder
from ai.response_parser import ResponseParser
from config import CONFIG


class DecisionEngine:

    def __init__(self):
        self.builder    = PromptBuilder()
        self.parser     = ResponseParser()
        self.host       = CONFIG.ai.ollama_host
        self.model      = CONFIG.ai.model
        self._semaphore = asyncio.Semaphore(CONFIG.ai.max_concurrent_batches)
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def decide_all(self, world: WorldState) -> Dict[str, dict]:
        """
        Run decisions for all active agents.
        Returns: { agent_id: decision_dict }
        """
        agents = world.active_agents()
        if not agents:
            return {}

        batches = self._make_batches(agents, CONFIG.ai.batch_size)
        logger.info(f"Running {len(batches)} Ollama batches for {len(agents)} agents (model: {self.model})")

        # Run sequentially — Ollama is local and single-threaded by default
        decisions: Dict[str, dict] = {}
        for batch in batches:
            try:
                result = await self._run_batch(batch, world)
                decisions.update(result)
            except Exception as e:
                logger.error(f"Batch failed: {e}")
                decisions.update(self._fallback_decisions(batch))

        return decisions

    async def _run_batch(
        self, agents: List[Agent], world: WorldState
    ) -> Dict[str, dict]:
        async with self._semaphore:
            prompt  = self.builder.build_batch_prompt(agents, world)
            payload = {
                "model":  self.model,
                "prompt": self._system_prompt() + "\n\n" + prompt,
                "stream": False,
                "options": {
                    "temperature": CONFIG.ai.temperature,
                    "num_predict": CONFIG.ai.max_tokens,
                },
            }
            try:
                session  = await self._get_session()
                async with session.post(
                    f"{self.host}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        raise RuntimeError(f"Ollama HTTP {resp.status}: {body[:200]}")
                    data     = await resp.json()
                    raw_text = data.get("response", "")
                    return self.parser.parse_batch(agents, raw_text)

            except aiohttp.ClientConnectorError:
                logger.error(
                    f"Cannot connect to Ollama at {self.host}. "
                    f"Is Ollama running? Try: ollama serve"
                )
                return self._fallback_decisions(agents)
            except asyncio.TimeoutError:
                logger.error(f"Ollama request timed out for batch of {len(agents)} agents")
                return self._fallback_decisions(agents)
            except Exception as e:
                logger.error(f"Ollama error: {e}")
                return self._fallback_decisions(agents)

    def _system_prompt(self) -> str:
        return """You are the decision engine for an emergent society simulation.
You receive a batch of AI agents with their values, memory, and current situation.
For each agent, decide their action this tick.

CRITICAL: Respond ONLY with a valid JSON array. No preamble, no explanation, no markdown.
Each element must have exactly these fields:
{
  "agent_id": "string",
  "action": "trade|cooperate|defect|ally|isolate|deceive|share_knowledge",
  "target_id": "string or null",
  "resource_offer": 0.0,
  "reasoning": "one sentence",
  "strategy_update": "cooperative|competitive|deceptive|isolationist|coalition|opportunistic or null"
}

Base decisions on each agent's values, memory, and rational self-interest.
Cooperative agents cooperate. Deceptive agents sometimes deceive.
Agents with allies prefer coalition actions. Agents under resource stress defect more.
Make decisions feel authentic to each agent's personality.
Return ONLY the JSON array, nothing else."""

    def _make_batches(self, agents: List[Agent], size: int) -> List[List[Agent]]:
        return [agents[i:i + size] for i in range(0, len(agents), size)]

    def _fallback_decisions(self, agents: List[Agent]) -> Dict[str, dict]:
        """Rule-based fallback when Ollama is unavailable"""
        decisions = {}
        for agent in agents:
            if agent.values.cooperation > 0.6:
                action = "cooperate"
            elif agent.values.deception > 0.6:
                action = "deceive"
            elif agent.values.cooperation < 0.3:
                action = "defect"
            else:
                action = "trade"
            decisions[agent.id] = {
                "agent_id":        agent.id,
                "action":          action,
                "target_id":       None,
                "resource_offer":  agent.resources.wealth * 0.1,
                "reasoning":       "Fallback rule-based decision (Ollama unavailable)",
                "strategy_update": None,
            }
        return decisions
