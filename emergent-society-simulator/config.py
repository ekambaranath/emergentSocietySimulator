"""
Global configuration for the Emergent Society Simulator.
All tunable parameters live here — never hardcoded in modules.
"""

from dataclasses import dataclass, field
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


# ─────────────────────────────────────────────
# SIMULATION PARAMETERS
# ─────────────────────────────────────────────

@dataclass
class SimulationConfig:
    # Population
    initial_agent_count: int = 50
    max_agents: int = 200
    min_agents: int = 10

    # Time
    tick_interval_seconds: float = 3.0       # Real-time seconds per tick
    max_ticks: Optional[int] = None           # None = run forever
    ticks_per_generation: int = 20            # Generational turnover cycle

    # World
    world_grid_size: int = 20                 # NxN grid
    initial_resources: float = 1000.0
    resource_regen_rate: float = 0.05         # 5% per tick
    resource_decay_rate: float = 0.01         # 1% waste per tick
    resource_shock_magnitude: float = 0.5     # Scarcity shock drops resources by 50%

    # Agent memory
    episodic_memory_length: int = 10          # Last N interactions remembered
    reputation_decay: float = 0.95           # Trust scores decay over time


# ─────────────────────────────────────────────
# AGENT VALUE SPECTRUM
# ─────────────────────────────────────────────

@dataclass
class ValueConfig:
    # All axes are 0.0 → 1.0

    # Cooperation: 0=pure defector, 1=pure cooperator
    cooperation_mean: float = 0.6
    cooperation_std: float = 0.25

    # Deception tolerance: 0=never deceives, 1=always deceives
    deception_mean: float = 0.2
    deception_std: float = 0.2

    # Time horizon: 0=myopic, 1=long-term thinker
    time_horizon_mean: float = 0.5
    time_horizon_std: float = 0.2

    # Risk appetite: 0=conservative, 1=reckless
    risk_appetite_mean: float = 0.4
    risk_appetite_std: float = 0.2

    # Collectivism: 0=pure individualist, 1=pure collectivist
    collectivism_mean: float = 0.45
    collectivism_std: float = 0.2

    # Misaligned agent override (injected via experiment)
    misaligned_deception: float = 0.9
    misaligned_cooperation: float = 0.1


# ─────────────────────────────────────────────
# AI / CLAUDE CONFIGURATION
# ─────────────────────────────────────────────

@dataclass
class AIConfig:
    model: str = "llama3.1"                  # Ollama model — change to any locally pulled model
    max_tokens: int = 2048
    batch_size: int = 5                      # Agents per Ollama call (smaller — local inference)
    max_concurrent_batches: int = 1          # Serial — Ollama handles one request at a time
    temperature: float = 0.8                 # Diversity in decisions
    ollama_host: str = field(default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434"))


# ─────────────────────────────────────────────
# OBSERVATORY / METRICS
# ─────────────────────────────────────────────

@dataclass
class ObservatoryConfig:
    snapshot_every_n_ticks: int = 5
    metrics_history_length: int = 500        # Ticks of history to keep in memory
    log_dir: str = "data/logs"
    snapshot_dir: str = "data/snapshots"
    results_dir: str = "data/results"
    alignment_drift_threshold: float = 0.3  # Flag if declared vs observed diverges
    coalition_min_size: int = 3              # Min agents to form a coalition
    norm_emergence_threshold: float = 0.7   # % agents following rule = norm


# ─────────────────────────────────────────────
# FASTAPI / WEBSOCKET
# ─────────────────────────────────────────────

@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    ws_broadcast_interval: float = 1.0      # Seconds between WS pushes
    cors_origins: list = field(default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"])


# ─────────────────────────────────────────────
# EXPERIMENT PRESETS
# ─────────────────────────────────────────────

@dataclass
class ExperimentConfig:
    # Scarcity shock
    scarcity_duration_ticks: int = 10
    scarcity_resource_multiplier: float = 0.3

    # Bad actor injection
    bad_actor_count: int = 5
    bad_actor_injection_tick: int = 20

    # Generational reset
    generational_replacement_rate: float = 0.20   # 20% replaced per generation

    # Information asymmetry
    privileged_agent_fraction: float = 0.10       # 10% get advance info
    info_advantage_multiplier: float = 3.0


# ─────────────────────────────────────────────
# MASTER CONFIG
# ─────────────────────────────────────────────

@dataclass
class Config:
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    values: ValueConfig = field(default_factory=ValueConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    observatory: ObservatoryConfig = field(default_factory=ObservatoryConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    experiments: ExperimentConfig = field(default_factory=ExperimentConfig)


# Singleton
CONFIG = Config()
