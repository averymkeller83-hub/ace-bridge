import pyautogui
import time
import json
import os
import subprocess
import urllib.request
from datetime import datetime

# Configuration
GITHUB_REPO = "averymkeller83-hub/ace-bridge"
COMMANDS_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/commands.json"
RESULTS_FILE = r"C:\Users\avery\ace-results.json"
POLL_INTERVAL = 30  # seconds
LAST_COMMAND_HASH = None

print("=" * 50)
print("ACE COMMAND EXECUTOR - GitHub Sync")
print("=" * 50)
print(f"Repository: {GITHUB_REPO}")
print(f"Results: {RESULTS_FILE}")
print(f"Poll interval: {POLL_INTERVAL} seconds")
print("=" * 50)

def fetch_commands():
    """Fetch commands from GitHub"""
    try:
        with urllib.request.urlopen(COMMANDS_URL, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("commands", [])
    except Exception as e:
        print(f"Error fetching commands: {e}")
        return []

def execute_command(cmd_data):
    """Execute a single command"""
    cmd_id = cmd_data.get("id", "unknown")
    command = cmd_data.get("command", "")
    args = cmd_data.get("args", [])
    
    print(f"\n[{datetime.now()}] Executing: {cmd_id}")
    print(f"Command: {command}")
    print(f"Args: {args}")
    
    try:
        if command == "open":
            app = args[0] if args else ""
            print(f"Opening: {app}")
            pyautogui.keyDown('win')
            pyautogui.keyUp('win')
            time.sleep(0.5)
            pyautogui.typewrite(app, interval=0.01)
            time.sleep(0.3)
            pyautogui.keyDown('return')
            pyautogui.keyUp('return')
            time.sleep(2)
            return {"success": True, "message": f"Opened {app}"}
            
        elif command == "type":
            text = args[0] if args else ""
            pyautogui.typewrite(text, interval=0.01)
            return {"success": True, "message": f"Typed: {text[:50]}..."}
            
        elif command == "click":
            x = int(args[0]) if len(args) > 0 else 0
            y = int(args[1]) if len(args) > 1 else 0
            pyautogui.click(x, y)
            return {"success": True, "message": f"Clicked at ({x}, {y})"}
            
        elif command == "screenshot":
            screenshot = pyautogui.screenshot()
            filename = args[0] if args else f"screenshot_{int(time.time())}.png"
            screenshot.save(filename)
            return {"success": True, "message": f"Screenshot saved: {filename}"}
            
        elif command == "sleep":
            seconds = int(args[0]) if args else 1
            time.sleep(seconds)
            return {"success": True, "message": f"Slept for {seconds} seconds"}
            
        elif command == "key":
            keys = args
            for key in keys:
                pyautogui.keyDown(key)
            for key in reversed(keys):
                pyautogui.keyUp(key)
            return {"success": True, "message": f"Pressed: {'+'.join(keys)}"}
            
        else:
            return {"success": False, "error": f"Unknown command: {command}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def process_commands():
    """Fetch and execute commands from GitHub"""
    global LAST_COMMAND_HASH
    
    commands = fetch_commands()
    if not commands:
        return
    
    # Create hash of commands to detect changes
    current_hash = hash(json.dumps(commands, sort_keys=True))
    if current_hash == LAST_COMMAND_HASH:
        return  # No changes
    
    LAST_COMMAND_HASH = current_hash
    
    results = []
    for cmd in commands:
        result = execute_command(cmd)
        results.append({
            "id": cmd.get("id"),
            "command": cmd.get("command"),
            "timestamp": datetime.now().isoformat(),
            "result": result
        })
    
    # Save results locally
    with open(RESULTS_FILE, 'w') as f:
        json.dump({"results": results, "last_update": datetime.now().isoformat()}, f, indent=2)
    
    print(f"\nExecuted {len(commands)} command(s)")
    print(f"Results saved to: {RESULTS_FILE}")

# Main loop
print("\nExecutor running. Press Ctrl+C to stop.")
print("Fetching commands from GitHub...\n")

try:
    while True:
        process_commands()
        time.sleep(POLL_INTERVAL)
        
except KeyboardInterrupt:
    print("\n\nExecutor stopped by user.")
    print("Goodbye!")
