#!/usr/bin/env python3
"""Ace Bridge Watcher — longer delay after opening Ace"""

import json, os, subprocess, time, shutil
from pathlib import Path
from datetime import datetime

REPO_PATH = Path.home() / "ace-bridge"
COMMANDS_DIR = REPO_PATH / "commands"
PROCESSED_DIR = REPO_PATH / "commands" / "processed"
RESULTS_DIR = REPO_PATH / "results"
LOGS_DIR = REPO_PATH / "logs"
POLL_INTERVAL = 5
DELAY_BETWEEN_COMMANDS = 60

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    log_file = LOGS_DIR / f"watcher-{datetime.now().strftime('%Y-%m-%d')}.log"
    with open(log_file, "a") as f:
        f.write(line + "\n")

def send_to_ace(command_text):
    try:
        safe = command_text.replace('\\', '\\\\').replace('"', '\\"')
        script = f'''
tell application "System Events"
    key code 49 using {{control down}}
    delay 6
    keystroke "{safe}"
    delay 1
    key code 36
end tell
'''
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stderr or "OK"
    except Exception as e:
        return False, str(e)

def push_to_github():
    try:
        subprocess.run(["git", "-C", str(REPO_PATH), "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", str(REPO_PATH), "commit", "-m", f"Results {datetime.now().isoformat()}"], capture_output=True)
        subprocess.run(["git", "-C", str(REPO_PATH), "push"], capture_output=True)
        log("Pushed")
    except: pass

def process_command(cmd_file):
    try:
        with open(cmd_file) as f:
            data = json.load(f)
        cmd_id = data.get("id", "unknown")
        command_text = data.get("command", "")
        log(f"Sending to Ace: {command_text[:80]}")
        success, output = send_to_ace(command_text)
        with open(RESULTS_DIR / f"{cmd_id}.json", "w") as f:
            json.dump({"id": cmd_id, "command": command_text, "timestamp": datetime.now().isoformat(), "result": {"success": success}}, f, indent=2)
        shutil.move(str(cmd_file), str(PROCESSED_DIR / cmd_file.name))
        log(f"Sent. Waiting {DELAY_BETWEEN_COMMANDS}s...")
        push_to_github()
        time.sleep(DELAY_BETWEEN_COMMANDS)
    except Exception as e:
        log(f"Error: {e}")

log("Ace Watcher — 6s delay after Ctrl+Space before typing")

while True:
    try:
        for cmd_file in sorted(COMMANDS_DIR.glob("*.json")):
            process_command(cmd_file)
        push_to_github()
    except Exception as e:
        log(f"Error: {e}")
    time.sleep(POLL_INTERVAL)
