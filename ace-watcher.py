#!/usr/bin/env python3
"""
Ace Bridge Watcher
Runs on your local computer, watches for commands from Jarvis
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Configuration
REPO_PATH = Path.home() / "ace-bridge"  # Change this to your repo path
COMMANDS_DIR = REPO_PATH / "commands"
RESULTS_DIR = REPO_PATH / "results"
LOGS_DIR = REPO_PATH / "logs"
POLL_INTERVAL = 5  # seconds

def setup():
    """Ensure directories exist"""
    for dir_path in [COMMANDS_DIR, RESULTS_DIR, LOGS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

def log(message):
    """Log to file and console"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    
    log_file = LOGS_DIR / f"watcher-{datetime.now().strftime('%Y-%m-%d')}.log"
    with open(log_file, "a") as f:
        f.write(log_entry + "\n")

def execute_ace(command, args=None):
    """Execute Ace with given command"""
    try:
        # Build Ace command
        ace_cmd = ["ace"]
        if command:
            ace_cmd.append(command)
        if args:
            ace_cmd.extend(args)
        
        log(f"Executing: {' '.join(ace_cmd)}")
        
        # Run Ace
        result = subprocess.run(
            ace_cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def process_command(command_file):
    """Process a single command file"""
    try:
        with open(command_file, "r") as f:
            command_data = json.load(f)
        
        command_id = command_data.get("id", "unknown")
        ace_command = command_data.get("command", "")
        ace_args = command_data.get("args", [])
        
        log(f"Processing command {command_id}: {ace_command}")
        
        # Execute via Ace
        result = execute_ace(ace_command, ace_args)
        
        # Write result
        result_file = RESULTS_DIR / f"{command_id}.json"
        result_data = {
            "id": command_id,
            "command": ace_command,
            "args": ace_args,
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
        
        with open(result_file, "w") as f:
            json.dump(result_data, f, indent=2)
        
        # Archive processed command
        archive_dir = COMMANDS_DIR / "processed"
        archive_dir.mkdir(exist_ok=True)
        command_file.rename(archive_dir / command_file.name)
        
        log(f"Command {command_id} completed. Result: {result['success']}")
        
    except Exception as e:
        log(f"Error processing command: {e}")

def watch():
    """Main watch loop"""
    log("Ace Bridge Watcher started")
    log(f"Watching: {COMMANDS_DIR}")
    log(f"Results: {RESULTS_DIR}")
    log("Press Ctrl+C to stop")
    
    try:
        while True:
            # Check for new command files
            command_files = sorted(COMMANDS_DIR.glob("*.json"))
            
            for cmd_file in command_files:
                if cmd_file.is_file():
                    process_command(cmd_file)
            
            # Push results to GitHub (optional - requires git setup)
            push_results()
            
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        log("Watcher stopped by user")

def push_results():
    """Push results to GitHub (if git is configured)"""
    try:
        os.chdir(REPO_PATH)
        
        # Check if there are changes
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True
        )
        
        if status.stdout.strip():
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(
                ["git", "commit", "-m", f"Results update {datetime.now().isoformat()}"],
                check=True
            )
            subprocess.run(["git", "push"], check=True)
            log("Results pushed to GitHub")
            
    except Exception as e:
        # Silently fail - not critical
        pass

if __name__ == "__main__":
    setup()
    
    # Allow custom repo path via argument
    if len(sys.argv) > 1:
        REPO_PATH = Path(sys.argv[1])
        COMMANDS_DIR = REPO_PATH / "commands"
        RESULTS_DIR = REPO_PATH / "results"
        LOGS_DIR = REPO_PATH / "logs"
        setup()
    
    watch()
