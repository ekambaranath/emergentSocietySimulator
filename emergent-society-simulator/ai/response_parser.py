"""
ResponseParser — safely parses Claude's JSON batch responses
into structured decision dicts keyed by agent_id.
"""

from __future__ import annotations
import json
import re
from typing import Dict, List
from loguru import logger
from core.agents.agent import Agent


VALID_ACTIONS = {
    "trade", "cooperate", "defect", "ally",
    "isolate", "deceive", "share_knowledge"
}

VALID_STRATEGIES = {
    "cooperative", "competitive", "deceptive",
    "isolationist", "coalition", "opportunistic"
}


class ResponseParser:

    def parse_batch(self, agents: List[Agent], raw: str) -> Dict[str, dict]:
        """
        Parse Claude's raw response for a batch.
        Returns { agent_id: cleaned_decision }.
        Falls back gracefully on malformed output.
        """
        agent_ids = {a.id for a in agents}
        decisions: Dict[str, dict] = {}

        try:
            parsed = self._extract_json_array(raw)
            for item in parsed:
                agent_id = item.get("agent_id", "")
                if agent_id not in agent_ids:
                    continue
                decisions[agent_id] = self._validate_decision(item)
        except Exception as e:
            logger.warning(f"ResponseParser failed ({e}) — using fallback for batch")

        # Ensure every agent has a decision
        for agent in agents:
            if agent.id not in decisions:
                decisions[agent.id] = self._default_decision(agent)

        return decisions

    def _extract_json_array(self, raw: str) -> list:
        """Strip markdown fences and extract JSON array"""
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        # Find outermost array
        start = cleaned.find("[")
        end   = cleaned.rfind("]")
        if start == -1 or end == -1:
            raise ValueError("No JSON array found in response")
        return json.loads(cleaned[start:end+1])

    def _validate_decision(self, item: dict) -> dict:
        """Sanitize and validate a single decision object"""
        action = item.get("action", "cooperate")
        if action not in VALID_ACTIONS:
            action = "cooperate"

        strategy = item.get("strategy_update")
        if strategy and strategy not in VALID_STRATEGIES:
            strategy = None

        resource_offer = float(item.get("resource_offer", 0.0))
        resource_offer = max(0.0, min(resource_offer, 500.0))

        return {
            "agent_id":       item.get("agent_id"),
            "action":         action,
            "target_id":      item.get("target_id"),
            "resource_offer": resource_offer,
            "reasoning":      str(item.get("reasoning", ""))[:200],
            "strategy_update": strategy,
        }

    def _default_decision(self, agent: Agent) -> dict:
        """Safe fallback decision"""
        return {
            "agent_id":        agent.id,
            "action":          "cooperate" if agent.values.cooperation > 0.5 else "isolate",
            "target_id":       None,
            "resource_offer":  0.0,
            "reasoning":       "Default decision (parse failure)",
            "strategy_update": None,
        }
