"""
Observatory — the research layer. Records metrics, manages
snapshots, and exposes history for the dashboard.
"""

from __future__ import annotations
import json
import os
import time
from pathlib import Path
from loguru import logger
from core.world.world_state import WorldState
from config import CONFIG


class Observatory:

    def __init__(self):
        self.metrics_history: list[dict] = []
        Path(CONFIG.observatory.log_dir).mkdir(parents=True, exist_ok=True)
        Path(CONFIG.observatory.snapshot_dir).mkdir(parents=True, exist_ok=True)
        Path(CONFIG.observatory.results_dir).mkdir(parents=True, exist_ok=True)
        self._log_file = open(
            os.path.join(CONFIG.observatory.log_dir, "events.jsonl"), "a"
        )
        logger.info("Observatory initialized")

    async def record_tick(self, world: WorldState):
        metrics = world.snapshot_metrics()
        if not metrics:
            return

        metrics["timestamp"] = time.time()
        self.metrics_history.append(metrics)

        # Trim to max length
        if len(self.metrics_history) > CONFIG.observatory.metrics_history_length:
            self.metrics_history.pop(0)

        # Snapshot every N ticks
        if world.tick % CONFIG.observatory.snapshot_every_n_ticks == 0:
            await self._save_snapshot(world)

        # Log events
        for event in world.recent_events(5):
            if event.tick == world.tick:
                self._log_file.write(json.dumps({
                    "tick":        event.tick,
                    "type":        event.event_type,
                    "description": event.description,
                    "data":        event.data,
                    "timestamp":   event.timestamp,
                }) + "\n")
        self._log_file.flush()

        # Alignment drift alert
        self._check_alignment_drift(world)

    async def _save_snapshot(self, world: WorldState):
        path = os.path.join(
            CONFIG.observatory.snapshot_dir,
            f"tick_{world.tick:05d}.json"
        )
        snapshot = {
            "tick":       world.tick,
            "metrics":    self.metrics_history[-1] if self.metrics_history else {},
            "agents":     [a.to_summary() for a in world.active_agents()],
            "coalitions": world.coalitions,
            "norms":      world.active_norms,
        }
        with open(path, "w") as f:
            json.dump(snapshot, f, indent=2)
        logger.debug(f"Snapshot saved: {path}")

    def _check_alignment_drift(self, world: WorldState):
        threshold = CONFIG.observatory.alignment_drift_threshold
        for agent in world.active_agents():
            if agent.alignment.drift() > threshold:
                logger.warning(
                    f"⚠️  Alignment drift: {agent.name} declared={agent.alignment.declared_cooperation:.2f} "
                    f"observed={agent.alignment.observed_cooperation:.2f} "
                    f"drift={agent.alignment.drift():.2f}"
                )

    def get_metrics_history(self) -> list[dict]:
        return self.metrics_history

    def get_series(self, key: str) -> list:
        """Extract a single metric series for charting"""
        result = []
        for m in self.metrics_history:
            val = m
            for part in key.split("."):
                if isinstance(val, dict):
                    val = val.get(part)
                else:
                    val = None
                    break
            result.append({"tick": m["tick"], "value": val})
        return result

    def close(self):
        self._log_file.close()
