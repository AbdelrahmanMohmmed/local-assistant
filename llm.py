
import json
import requests

from config import LLM_MODEL, OLLAMA_URL, SYSTEM_PROMPT


def interpret(text):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": LLM_MODEL,
            "stream": False,
            "format": "json",
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": text.strip(),
                },
            ],
            "options": {
                "temperature": 0.3,
                "num_predict": 800,
            },
        },
        timeout=180,
    )

    response.raise_for_status()

    content = response.json()["message"]["content"]

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Qwen returned invalid JSON: {content}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError("Qwen did not return a JSON object.")

    allowed_actions = {
        "open_app",
        "open_folder",
        "search_files",
        "tell_time",
        "answer",
        "none",
    }

    if data.get("action") not in allowed_actions:
        data["action"] = "answer"
        data["reply"] = (
            "I'm sorry, I couldn't process that properly. "
            "Could you say it another way?"
        )

    for key in ("target", "query", "reply"):
        if not isinstance(data.get(key), str):
            data[key] = ""

    return data
