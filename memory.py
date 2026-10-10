# -*- coding: utf-8 -*-
"""
Memory management for Amy assistant.
"""

import json
from pathlib import Path

from config import MEMORY_FILE, MEMORY_TURNS


def load_memory() -> list[dict]:
    """Load conversation history from disk."""
    try:
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)][-MEMORY_TURNS:]


def save_memory(history: list[dict]) -> None:
    """Persist conversation history to disk."""
    try:
        MEMORY_FILE.write_text(
            json.dumps(history[-MEMORY_TURNS:], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as e:
        from log import log
        log(f"Could not save memory: {e}")
