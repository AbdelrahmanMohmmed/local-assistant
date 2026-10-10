# -*- coding: utf-8 -*-
"""
Desktop actions for Amy assistant.
"""

import subprocess
import shutil
from datetime import datetime
from pathlib import Path

from config import APP_COMMANDS, FOLDERS, PROJECT_DIR, HOME

from log import log


def open_app(target: str, command_to_run: str | None = None) -> str:
    """Launch an application. If target is terminal, run a command inside it.
    If target is firefox, open a URL or search term."""
    command = APP_COMMANDS.get(target.lower().strip())
    if not command:
        return "That application is not on my allowed list."

    exe = command[0]
    if shutil.which(exe) is None:
        return f"I couldn't find {exe} on this computer."

    if target.lower().strip() == "terminal" and command_to_run:
        full_cmd = [exe, "--", "bash", "-c", command_to_run]
    elif target.lower().strip() == "firefox" and command_to_run:
        full_cmd = [exe, command_to_run]
    else:
        full_cmd = command

    subprocess.Popen(full_cmd, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)
    what = f"Running {command_to_run}" if command_to_run else f"Opening {target}"
    return f"{what} for you."



SHELL_COMMANDS = {"echo", "ls", "pwd", "date", "whoami", "cat", "grep",
                       "find", "rm", "cp", "mv", "mkdir", "touch", "nano",
                       "vim", "code", "python", "node", "npm", "git",
                       "apt", "yum", "brew", "docker", "ping", "curl",
                       "wget", "gcc", "g++", "make", "chmod", "chown"}


def _looks_like_shell_command(text: str) -> bool:
    """Check if text looks like a shell command to run."""
    first_word = text.strip().split()[0].lower().strip("\`\!\$\"\);")
    return first_word in SHELL_COMMANDS


def execute(data: dict) -> str | None:
    """Execute one action. Returns response or None for chat."""
    action = str(data.get("action", "answer")).strip().lower()
    target = str(data.get("target", ""))[:100]
    query = str(data.get("query", ""))[:100]

    if action == "open_app":
        if target == "terminal" and query and _looks_like_shell_command(query):
            return open_app(target, query)
        return open_app(target)
    if action == "tell_time":
        return f"It's {datetime.now().strftime('%I:%M %p')} right now."

    return None
