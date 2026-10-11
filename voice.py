
from config import *
import sounddevice as sd
from scipy.io.wavfile import write
import subprocess
import numpy as np

def listen(seconds=None):
    input("\nPress ENTER to start recording...")
    print("Recording... Press ENTER again to stop.")

    audio_chunks = []

    def callback(indata, frames, time_info, status):
        audio_chunks.append(indata.copy())

    with sd.InputStream(
        samplerate=16000,
        channels=1,
        dtype="int16",
        callback=callback,
    ):
        input()  # Wait until you press ENTER again

    if not audio_chunks:
        print("No audio recorded.")
        return

    audio = np.concatenate(audio_chunks, axis=0)
    write(str(RECORDING), 16000, audio)

    print("Recording saved.")



def transcribe():
    result = subprocess.run(
        [
            str(WHISPER),
            "-m", str(WHISPER_MODEL),
            "-f", str(RECORDING),
            "-t", "4",
            "--no-timestamps",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )

    text = result.stdout.strip()

    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("["):
            lines.append(line)

    transcript = " ".join(lines).strip()
    TRANSCRIPT.write_text(transcript, encoding="utf-8")
    print(f"You said: {transcript}")
    return transcript
