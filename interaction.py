# -*- coding: utf-8 -*-
"""
Single interaction handling for Amy assistant.
"""

import time
import random
import json
import re

from voice import record_until_silence, transcribe, play_chime, speak
from llm import chat
from actions import execute
from memory import load_memory, save_memory, MEMORY_TURNS
from log import log, IDLE_LINES


def _extract_action(text: str) -> dict | None:
    """Try to extract a JSON action from LLM reply."""
    # Find JSON object in the reply
    match = re.search(r'\{[^{}]*"action"[^{}]*\}', text)
    if not match:
        return None
    try:
        data = json.loads(match.group())
        if isinstance(data, dict) and "action" in data:
            return data
    except json.JSONDecodeError:
        pass
    return None


def respond(text: str, history: list[dict]) -> str:
    """Send everything to Qwen. It decides action or chat."""
    from llm import classify
    plan = classify(text)
    log(f"Intent: {plan}")

    result = execute(plan)
    answer = result if result is not None else chat(text, history)

    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": answer})
    del history[:-MEMORY_TURNS]
    save_memory(history)

    return answer


def handle_interaction(history: list[dict]) -> None:
    """Full interaction cycle: chime → record → transcribe → respond → speak."""
    from voice import ensure_chime, play_chime
    ensure_chime()
    play_chime()
    time.sleep(0.35)

    # Keep recording until silence, 8 second max per chunk
    recorded = record_until_silence()
    if recorded is None:
        speak(random.choice(IDLE_LINES))
        return

    text = transcribe(recorded)
    if not text:
        speak(random.choice(IDLE_LINES))
        return

    log(f"You: {text}")
    speak(respond(text, history))
