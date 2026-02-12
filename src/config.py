"""Application configuration."""

from __future__ import annotations

import json
import os
from pathlib import Path

# Project root is the parent of `src/`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FRAMEWORKS_DIR = DATA_DIR / "frameworks"
TEMPLATES_DIR = DATA_DIR / "templates"
DB_PATH = DATA_DIR / "db" / "reports.db"
OUTPUT_DIR = PROJECT_ROOT / "output"

CONFIG_FILE = PROJECT_ROOT / ".irf_config.json"

DEFAULT_CONFIG = {
    "api_key": "",
    "model": "claude-sonnet-4-20250514",
    "output_dir": str(OUTPUT_DIR),
    "max_tokens_per_section": 4096,
    "default_format": "markdown",
}


def load_config() -> dict:
    """Load configuration from file, falling back to defaults."""
    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            stored = json.load(f)
        config.update(stored)
    # Environment variable overrides
    if api_key := os.environ.get("ANTHROPIC_API_KEY"):
        config["api_key"] = api_key
    return config


def save_config(config: dict) -> None:
    """Persist configuration to disk."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_config_value(key: str) -> str | None:
    """Get a single config value."""
    return load_config().get(key)


def set_config_value(key: str, value: str) -> None:
    """Set a single config value and persist."""
    config = load_config()
    config[key] = value
    save_config(config)
