# -*- coding: utf-8 -*-
"""
Background daemon management for Amy assistant.
"""

import fcntl
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
import shutil
from config import SOCKET_PATH, PID_FILE, ASSISTANT_DIR, SCRIPT_PATH, NAME
from log import log


def _daemon_lock():
    """Ensure only one daemon runs. Returns lock handle or None."""
    handle = open(PID_FILE, "a+", encoding="utf-8")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None

    handle.seek(0)
    handle.truncate()
    handle.write(str(os.getpid()))
    handle.flush()
    return handle


def _trigger_server(trigger: threading.Event, stop: threading.Event) -> None:
    """Unix socket server that listens for F12 triggers."""
    if SOCKET_PATH.exists():
        SOCKET_PATH.unlink()

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(SOCKET_PATH))
    os.chmod(SOCKET_PATH, 0o600)
    server.listen(5)
    server.settimeout(0.5)

    while not stop.is_set():
        try:
            conn, _ = server.accept()
        except socket.timeout:
            continue
        except OSError:
            break

        with conn:
            try:
                msg = conn.recv(64).decode("utf-8", "replace").strip()
                if msg == "ping":
                    conn.sendall(b"pong")
            except OSError:
                msg = ""

        if msg == "listen":
            trigger.set()

    server.close()
    if SOCKET_PATH.exists():
        SOCKET_PATH.unlink()


def run_daemon() -> None:
    """Run the background daemon loop."""
    from memory import load_memory
    from interaction import handle_interaction

    missing = [str(p) for p in (
        Path.home() / "whisper.cpp/build/bin/whisper-cli",
        Path.home() / "whisper.cpp/models/ggml-base.en.bin",
        ASSISTANT_DIR / "en_US-amy-medium.onnx",
    ) if not p.is_file()]
    if missing:
        log("Missing required files:")
        for p in missing:
            log(f"  {p}")
        return

    if shutil.which("aplay") is None:
        log("Please install alsa-utils so I can speak through aplay.")
        lock.close()
        return

    lock = _daemon_lock()
    if lock is None:
        log(f"{NAME} is already running.")
        return



    trigger = threading.Event()
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())

    thread = threading.Thread(target=_trigger_server, args=(trigger, stop), daemon=True)
    thread.start()
    time.sleep(0.3)

    if not SOCKET_PATH.exists():
        log("Could not create the trigger socket. Is another copy running?")
        return

    history = load_memory()
    log(f"{NAME} is awake and listening in the background.")
    log(f"Press F12 to talk. (socket: {SOCKET_PATH})")

    try:
        while not stop.is_set():
            if not trigger.wait(timeout=1.0):
                continue
            trigger.clear()
            try:
                handle_interaction(history)
            except Exception as e:
                log(f"Something went wrong: {e}")
                try:
                    from voice import speak
                    speak("Sorry, something went wrong on my side just then.")
                except Exception:
                    pass
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        log(f"{NAME} is going back to sleep.")
        time.sleep(0.6)
        if SOCKET_PATH.exists():
            SOCKET_PATH.unlink()
        lock.close()


def _try_send(message: str, expect_reply: bool = False) -> bool:
    """Send a message to the daemon socket."""
    if not SOCKET_PATH.exists():
        return False

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.settimeout(5.0)
        client.connect(str(SOCKET_PATH))
        client.sendall(message.encode("utf-8"))
        if expect_reply:
            return client.recv(64) == b"pong"
        return True
    except OSError:
        return False
    finally:
        client.close()


def start_daemon() -> bool:
    """Launch daemon detached and wait for socket readiness."""
    subprocess.Popen(
        [sys.executable, str(SCRIPT_PATH), "--daemon"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True, cwd=str(ASSISTANT_DIR),
    )
    for _ in range(60):
        time.sleep(0.1)
        if _try_send("ping", expect_reply=True):
            return True
    return False


def send_trigger() -> None:
    """Send a listen trigger to the daemon (what F12 does)."""
    if _try_send("listen"):
        return

    if not start_daemon():
        print("Could not reach the assistant. Run: python assistant.py")
        return
    _try_send("listen")


def is_running() -> bool:
    """Check if daemon is running."""
    return _try_send("ping", expect_reply=True)


def stop_daemon() -> None:
    """Stop the background daemon."""
    pid = None
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        pass

    if pid:
        try:
            os.kill(pid, 15)
            print(f"Stopped {NAME} (pid {pid}).")
            for _ in range(50):
                time.sleep(0.1)
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    break
        except ProcessLookupError:
            print(f"{NAME} wasn't running.")
        except PermissionError:
            print(f"I'm not allowed to stop process {pid}.")
    else:
        print(f"{NAME} wasn't running.")

    if SOCKET_PATH.exists():
        try:
            SOCKET_PATH.unlink()
        except OSError:
            pass
