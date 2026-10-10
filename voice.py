# -*- coding: utf-8 -*-
"""
Voice input handling for Amy assistant.
"""

import numpy as np
import subprocess
import sounddevice as sd
from scipy.io.wavfile import write
from pathlib import Path
import shutil

from config import (
    RECORDING, TRANSCRIPT, WHISPER, WHISPER_MODEL, SAMPLE_RATE, NAME,
    NON_SPEECH, CHIME_FILE, PIPER_MODEL, SPEECH_OUTPUT,
)

from log import log


def _level(block: np.ndarray) -> float:
    """Loudness of one audio block, normalized to 0..1."""
    samples = block.astype(np.float32) / 32768.0
    return float(np.sqrt(np.mean(samples ** 2)))


def record_until_silence(
    max_seconds: float = 8.0,
    no_speech_timeout: float = 7.0,
    silence_seconds: float = 1.2,
) -> Path | None:
    """Record from microphone until user stops talking.

    Keeps recording as long as the user is speaking. Stops only after
    silence_seconds of quiet following the last speech.
    """
    chunk_seconds = 0.1
    chunk_size = int(SAMPLE_RATE * chunk_seconds)
    silence_chunks = int(silence_seconds / chunk_seconds)
    max_chunks = int(max_seconds / chunk_seconds)
    wait_chunks = int(no_speech_timeout / chunk_seconds)

    blocks: list[np.ndarray] = []
    started = False
    quiet_run = 0

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
        ambient = []
        for _ in range(2):
            block, _ = stream.read(chunk_size)
            ambient.append(_level(block))
        threshold = max(0.005, float(np.median(ambient)) * 2.5)

        for i in range(max_chunks):
            block, _ = stream.read(chunk_size)
            level = _level(block)

            if not started:
                if level < threshold:
                    if i >= wait_chunks:
                        return None
                    continue
                started = True

            blocks.append(block[:, 0])
            quiet_run = 0

            # After speech started, wait for silence to end
            if level < threshold:
                quiet_run += 1
                if quiet_run >= silence_chunks:
                    break

    if not blocks:
        return None

    audio = np.concatenate(blocks)
    max_samples = int(SAMPLE_RATE * max_seconds)
    if len(audio) > max_samples:
        audio = audio[:max_samples]

    write(str(RECORDING), SAMPLE_RATE, audio)
    return RECORDING


def transcribe(path: Path) -> str:
    """Transcribe audio file using whisper-cli."""
    result = subprocess.run(
        [str(WHISPER), "-m", str(WHISPER_MODEL), "-f", str(path),
         "-t", "4", "--no-timestamps"],
        capture_output=True, text=True, timeout=120, check=True,
    )

    lines = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line and not line.startswith("["):
            lines.append(line)

    transcript = NON_SPEECH.sub(" ", " ".join(lines)).strip()
    if transcript.lower() in {"you", "thank you.", "thanks for watching!"}:
        transcript = ""

    TRANSCRIPT.write_text(transcript, encoding="utf-8")
    return transcript


def _piper_command() -> list[str]:
    """Get piper command (binary or python module)."""
    binary = shutil.which("piper")
    if binary:
        return [binary]
    import sys
    return [sys.executable, "-m", "piper"]


def speak(text: str) -> None:
    """Speak text using piper + aplay."""
    log(f"{NAME}: {text}")

    if shutil.which("aplay") is None:
        return

    subprocess.run(
        _piper_command() + ["-m", str(PIPER_MODEL),
                              "-f", str(SPEECH_OUTPUT), "--", text],
        check=True, timeout=60,
    )
    subprocess.run(["aplay", "-q", str(SPEECH_OUTPUT)],
                   check=True, timeout=60)


def ensure_chime() -> None:
    """Create listening chime if it doesn't exist."""
    if CHIME_FILE.is_file():
        return

    rate = 22050
    parts = []
    for freq, dur in ((880.0, 0.08), (1174.66, 0.11)):
        times = np.linspace(0, dur, int(rate * dur), endpoint=False)
        wave = 0.22 * np.sin(2 * np.pi * freq * times)
        fade = max(1, int(rate * 0.015))
        envelope = np.ones_like(wave)
        envelope[:fade] = np.linspace(0, 1, fade)
        envelope[-fade:] = np.linspace(1, 0, fade)
        parts.append(wave * envelope)

    audio = np.concatenate(parts)
    write(str(CHIME_FILE), rate, (audio * 32767).astype(np.int16))


def play_chime() -> None:
    """Play the listening chime."""
    if CHIME_FILE.is_file() and shutil.which("aplay") is not None:
        subprocess.run(["aplay", "-q", str(CHIME_FILE)],
                       check=False, timeout=10)
