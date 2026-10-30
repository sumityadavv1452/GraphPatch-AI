"""Centralized configuration for GraphPatch-AI.

Houses model identifiers, endpoint URLs, and operational limits.
Judges can inspect or configure settings here or via environment variables.
"""

import os
from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
BENCHMARK_CASES_DIR = PROJECT_ROOT / "benchmark_cases"

# Nebius Token Factory Configuration
NEBIUS_API_KEY = os.environ.get("NEBIUS_API_KEY", "")
NEBIUS_BASE_URL = os.environ.get(
    "NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1"
)

# NVIDIA Nemotron Model IDs (Exact strings on Nebius Token Factory)
TIER_FAST_ID = "nebius/nvidia/Nemotron-3_5-Lightning"
TIER_FAST_DISPLAY_NAME = "Nemotron-3_5-Lightning"

TIER_REASONING_ID = "nebius/nvidia/Nemotron-3-Ultra-550b-a55b"
TIER_REASONING_DISPLAY_NAME = "Nemotron-3-Ultra-550b-a55b"

# Tavily AI Search Configuration
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

# Repair Engine Limits
MAX_RETRIES = int(os.environ.get("GRAPHPATCH_MAX_RETRIES", "2"))
TIMEOUT_SECONDS = int(os.environ.get("GRAPHPATCH_TIMEOUT", "30"))
