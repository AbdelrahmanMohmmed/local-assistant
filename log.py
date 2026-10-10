# -*- coding: utf-8 -*-
"""
Logging for Amy assistant.
"""

from datetime import datetime
from pathlib import Path
import random

from config import LOG_FILE


def log(message: str) -> None:
    """Print to terminal and keep a copy in the log file."""
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
    try:
        print(line, flush=True)
    except Exception:
        pass

    try:
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > 1_000_000:
            LOG_FILE.write_text("", encoding="utf-8")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


# Idle/fallback responses
IDLE_LINES = [
    "I'm right here whenever you want to talk.",
    "I'm all ears, love. Take your time.",
    "No rush, I'm not going anywhere.",
    "I'm listening, I just couldn't hear you that time.",
]

FALLBACK_LINES = [
    "Tell me more, I'm listening.",
    "I'm not sure what you mean, but I'm happy to just talk.",
    "Say that a different way and I'll figure it out with you.",
]
