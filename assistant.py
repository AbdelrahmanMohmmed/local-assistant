#!/usr/bin/env python3
"""
Amy - a local, always-on Linux companion with a voice.

Usage:
    python assistant.py --setup       install F12 shortcut + autostart
    python assistant.py               run in background (daemon)
    python assistant.py --status      check if she's running
    python assistant.py --trigger     what F12 does
    python assistant.py --ask "text"  skip mic, just ask
    python assistant.py --once        one interaction in this terminal
    python assistant.py --stop        stop the background daemon
"""

from __future__ import annotations
import argparse
import shutil
import sys
from pathlib import Path

from config import ASSISTANT_DIR
from setup import setup
from daemon import (
    run_daemon, send_trigger, is_running, stop_daemon,
    start_daemon,
)
from interaction import handle_interaction
from memory import load_memory
from voice import speak


def main() -> None:
    parser = argparse.ArgumentParser(description="Amy, your local companion.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--daemon", action="store_true", help="run in background")
    group.add_argument("--trigger", action="store_true", help="what F12 does")
    group.add_argument("--setup", action="store_true", help="install F12 + autostart")
    group.add_argument("--status", action="store_true", help="check if running")
    group.add_argument("--stop", action="store_true", help="stop daemon")
    group.add_argument("--once", action="store_true", help="one interaction in terminal")
    group.add_argument("--ask", metavar="TEXT", help="skip mic, just ask")

    args = parser.parse_args()
    ASSISTANT_DIR.mkdir(parents=True, exist_ok=True)

    if args.setup:
        setup()
    elif args.status:
        print(f"Amy is {'awake' if is_running() else 'not running'}.")
    elif args.stop:
        stop_daemon()
    elif args.trigger:
        send_trigger()
    elif args.ask is not None:
        history = load_memory()
        speak(_quick_respond(args.ask, history))
    elif args.once:
        handle_interaction(load_memory())
    else:
        run_daemon()


def _quick_respond(text: str, history: list[dict]) -> str:
    """Respond without microphone (for --ask)."""
    from llm import classify, chat
    from actions import execute
    from memory import save_memory, MEMORY_TURNS
    from log import log

    plan = classify(text)
    log(f"Intent: {plan}")
    result = execute(plan)
    answer = result if result is not None else chat(text, history)

    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": answer})
    del history[:-MEMORY_TURNS]
    save_memory(history)
    return answer


if __name__ == "__main__":
    main()
