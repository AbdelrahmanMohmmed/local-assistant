import subprocess

from voice import *
from llm import *
from actions import *

# ---------- Spoken response ----------

def speak(text):
    print(f"Assistant: {text}")

    subprocess.run(
        [
            "python", "-m", "piper",
            "-m", str(PIPER_MODEL),
            "-f", str(SPEECH_OUTPUT),
            "--", text,
        ],
        check=True,
    )

    subprocess.run(
        ["aplay", "-q", str(SPEECH_OUTPUT)],
        check=True,
    )


def main():
    print("Local Linux AI assistant is ready.")

    try:
        while True:
            listen()

            try:
                text = transcribe()
                if not text:
                    print("No speech detected.")
                    continue

                data = interpret(text)
                print("Interpreted request:", data)

                result = execute(data)
                speak(result)

            except Exception as error:
                print(f"Request failed: {error}")

    except KeyboardInterrupt:
        print("\nAssistant stopped.")


if __name__ == "__main__":
    main()
