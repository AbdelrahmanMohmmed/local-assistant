# -*- coding: utf-8 -*-
"""
F12 shortcut and autostart setup for Amy assistant.
"""

import ast
import shlex
import subprocess
from pathlib import Path

from config import HOME, NAME, SCRIPT_PATH
from log import log

CUSTOM_SCHEMA = "org.gnome.settings-daemon.plugins.media-keys"
KEYBINDING_PATH = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/local-assistant/"
KEYBINDING_SCHEMA = f"{CUSTOM_SCHEMA}.custom-keybinding:{KEYBINDING_PATH}"
AUTOSTART_FILE = HOME / ".config/autostart/local-assistant.desktop"


def _gsettings(*args: str) -> str | None:
    """Run a gsettings command."""
    try:
        result = subprocess.run(["gsettings", *args], capture_output=True,
                                text=True, timeout=20, check=True)
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError) as e:
        log(f"gsettings failed: {e}")
        return None


def install_shortcut() -> bool:
    """Register F12 as the assistant trigger key."""
    if shutil.which("gsettings") is None:
        log("gsettings was not found, so I can't add the F12 key automatically.")
        return False

    raw = _gsettings("get", CUSTOM_SCHEMA, "custom-keybindings") or "[]"
    raw = raw.lstrip("@as ").strip() or "[]"

    try:
        existing = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        existing = []

    if not isinstance(existing, list):
        existing = []

    if KEYBINDING_PATH not in existing:
        existing.append(KEYBINDING_PATH)

    command = f"{shlex.quote(sys.executable)} {shlex.quote(str(SCRIPT_PATH))} --trigger"
    value = "[" + ", ".join(f"'{item}'" for item in existing) + "]"

    if _gsettings("set", CUSTOM_SCHEMA, "custom-keybindings", value) is None:
        return False

    for key, setting in [
        ("name", f"{NAME} (talk to me)"),
        ("command", command),
        ("binding", "F12"),
    ]:
        if _gsettings("set", KEYBINDING_SCHEMA, key, setting) is None:
            return False

    log("F12 is now bound to the assistant.")
    return True


def install_autostart() -> None:
    """Create autostart desktop entry."""
    try:
        AUTOSTART_FILE.parent.mkdir(parents=True, exist_ok=True)
        AUTOSTART_FILE.write_text(
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={NAME} (local assistant)\n"
            f"Exec={shlex.quote(sys.executable)} {shlex.quote(str(SCRIPT_PATH))} --daemon\n"
            "Terminal=false\n"
            "X-GNOME-Autostart-enabled=true\n",
            encoding="utf-8",
        )
        log(f"Autostart written to {AUTOSTART_FILE}")
    except OSError as e:
        log(f"Could not write the autostart file: {e}")


def setup() -> None:
    """Run the full setup wizard."""
    from config import ASSISTANT_DIR
    ASSISTANT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Setting up {NAME}...\n")

    if install_shortcut():
        print("  \u2713 F12 -> talk to me")
    else:
        print("  ! Could not register F12 automatically.")
        print("    Add it by hand in Settings > Keyboard > Custom Shortcuts:")
        print(f"      Name:    {NAME}")
        print(f"      Command: {shlex.quote(sys.executable)} {shlex.quote(str(SCRIPT_PATH))} --trigger")
        print("      Shortcut: F12")

    install_autostart()
    print("  \u2713 She starts automatically when you log in")

    print("\nDone. Press F12 anywhere and start talking.")
    print(f"Her log lives in {ASSISTANT_DIR / 'assistant.log'}")
