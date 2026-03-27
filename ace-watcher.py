#!/usr/bin/env python3
"""Ace Bridge Watcher — triggers Ace AI via Ctrl+Space"""

import json
import os
import subprocess
import time
import shutil
from pathlib import Path
from datetime import datetime

REPO_PATH = Path.home() / "ace-bridge"
COMMANDS_DIR = REPO_PATH / "commands"
PROCESSED_DIR = REPO_PATH / "commands" / "processed"
RESULTS_DIR = REPO_PATH / "results"
LOGS_DIR = REPO_PATH / "logs"
POLL_INTERVAL = 5

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
    """Open Ace with Ctrl+Space, type command, press Enter"""
    try:
        script = f'''
tell application "System Events"
    key code 49 using control down
    delay 1.5
    keystroke "{command_text}"
    delay 0.5
    key code 36
end tell
'''
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return True, "Sent to Ace"
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

def push_to_github():
    try:
        subprocess.run(["git", "-C", str(REPO_PATH), "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", str(REPO_PATH), "commit", "-m", f"Results update {datetime.utcnow().isoformat()}"], capture_output=True)
        subprocess.run(["git", "-C", str(REPO_PATH), "push"], capture_output=True)
        log("Results pushed to GitHub")
    except Exception as e:
        log(f"Git error: {e}")

def process_command(cmd_file):
    try:
        with open(cmd_file) as f:
            data = json.load(f)
        
        cmd_id = data.get("id", "unknown")
        command_text = data.get("command", "")
        
        log(f"Processing command {cmd_id}: {command_text[:80]}")
        
        success, output = send_to_ace(command_text)
        
        result = {
            "id": cmd_id,
            "command": command_text,
            "timestamp": datetime.utcnow().isoformat(),
            "result": {"success": success, "output": output}
        }
        
        result_file = RESULTS_DIR / f"{cmd_id}.json"
        with open(result_file, "w") as f:
            json.dump(result, f, indent=2)
        
        # Move to processed
        dest = PROCESSED_DIR / cmd_file.name
        shutil.move(str(cmd_file), str(dest))
        log(f"Command {cmd_id} completed. Result: {success}")
        
        push_to_github()
        
    except Exception as e:
        log(f"Error processing command: {e}")

log("Ace Bridge Watcher started (Ctrl+Space trigger)")

while True:
    try:
        for cmd_file in sorted(COMMANDS_DIR.glob("*.json")):
            process_command(cmd_file)
            time.sleep(2)
        push_to_github()
    except Exception as e:
        log(f"Error: {e}")
    time.sleep(POLL_INTERVAL)
