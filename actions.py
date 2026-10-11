import shutil
import subprocess
from datetime import datetime

from speech_utils import clean_for_speech


def open_app(target):
    commands = {
        "firefox": ["firefox"],
        "vs code": ["code"],
        "vscode": ["code"],
        "terminal": ["x-terminal-emulator"],
    }

    command = commands.get(target.lower().strip())
    if not command:
        return "That application is not on my allowed list."

    if shutil.which(command[0]) is None:
        return f"I couldn't find {command[0]} on this computer."

    subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return f"Opening {target}."


def execute(data):
    # Validate every action independently of the model's claims.
    action = data.get("action", "none")
    target = str(data.get("target", ""))[:100]
    query = str(data.get("query", ""))

    if action == "open_app":
        return open_app(target)

    if action == "tell_time":
        return f"It is {datetime.now().strftime('%I:%M %p')}."

    if action == "none":
        # Do not permit an answer action to run system commands.
        reply = str(data.get("reply"))
        return clean_for_speech(reply)

    return "I didn't understand that command. Please try again."