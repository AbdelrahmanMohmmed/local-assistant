# -*- coding: utf-8 -*-
"""
LLM interaction for Amy assistant.
"""

import json
import random
import re
import requests
from datetime import datetime

from config import OLLAMA_URL, LLM_MODEL, CLASSIFY_PROMPT, CHAT_PROMPT
from log import FALLBACK_LINES

def _ollama(messages: list[dict], json_mode: bool, temperature: float, num_predict: int) -> str:
    """Call Ollama API."""
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": LLM_MODEL,
            "stream": False,
            "format": "json" if json_mode else None,
            "messages": messages,
            "options": {"temperature": temperature, "num_predict": num_predict},
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


def classify(text: str) -> dict:
    """Classify user intent. Commands are self-contained, so this stays fast."""
    content = _ollama(
        [{"role": "system", "content": CLASSIFY_PROMPT},
         {"role": "user", "content": text}],
        json_mode=True, temperature=0.1, num_predict=120,
    )

    # Try parsing the whole response as JSON first
    try:
        data = json.loads(content)
        if isinstance(data, dict) and "action" in data:
            return _clean_action(data)
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: try to extract a JSON object from the text
    match = re.search(r'\{[^{}]*"action"[^{}]*\}', content, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            if isinstance(data, dict) and "action" in data:
                return _clean_action(data)
        except (json.JSONDecodeError, ValueError):
            pass

    # Last resort: return answer for anything we can't parse
    return {"action": "answer", "target": "", "query": ""}


def _clean_action(data: dict) -> dict:
    """Ensure action dict has the right keys and types."""
    return {
        "action": str(data.get("action", "answer")).strip().lower(),
        "target": str(data.get("target", ""))[:100].strip().lower(),
        "query": str(data.get("query", ""))[:100].strip(),
    }


def chat(text: str, history: list[dict]) -> str:
    """Free-form chat with persona and memory."""
    now = datetime.now().strftime("%A, %d %B %Y, %I:%M %p")

    messages = [
        {"role": "system", "content": f"{CHAT_PROMPT}\nIt is currently {now}."},
    ]
    messages.extend(history[-20:])
    messages.append({"role": "user", "content": text})

    reply = _ollama(messages, json_mode=False, temperature=0.8, num_predict=120).strip().strip('"')
    return reply or random.choice(FALLBACK_LINES)
