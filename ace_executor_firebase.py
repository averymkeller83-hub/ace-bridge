import pyautogui
import time
import json
import os
import urllib.request
from datetime import datetime

# Configuration
FIREBASE_URL = "https://ace-bridge-commands-default-rtdb.firebaseio.com/"
COMMANDS_URL = f"{FIREBASE_URL}commands.json"
RESULTS_URL = f"{FIREBASE_URL}results.json"
RESULTS_FILE = r"C:\Users\avery\ace-results.json"
POLL_INTERVAL = 1  # 1 second for near-instant response
LAST_COMMAND_HASH = None

print("=" * 50)
print("ACE COMMAND EXECUTOR - Firebase Realtime")
print("=" * 50)
print(f"Database: {FIREBASE_URL}")
print(f"Poll interval: {POLL_INTERVAL} second")
print("=" * 50)

def fetch_commands():
    """Fetch commands from Firebase"""
    try:
        with urllib.request.urlopen(COMMANDS_URL, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data is None:
                return []
            # Firebase returns dict, convert to list
            if isinstance(data, dict):
                return list(data.values())
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error fetching commands: {e}")
        return []

def send_result(result_data):
    """Send result to Firebase"""
    try:
        data = json.dumps(result_data).encode()
        req = urllib.request.Request(
            RESULTS_URL,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Error sending result: {e}")

def execute_command(cmd_data):
    """Execute a single command"""
    cmd_id = cmd_data.get("id", "unknown")
    command = cmd_data.get("command", "")
    args = cmd_data.get("args", [])
    
    print(f"\n[{datetime.now()}] Executing: {cmd_id}")
    print(f"Command: {command}")
    
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
            pyautogui.typewrite(text, interval=0.05)  # Slower typing
            return {"success": True, "message": f"Typed: {text[:50]}..."}
            
        elif command == "click":
            x = int(args[0]) if len(args) > 0 else 0
            y = int(args[1]) if len(args) > 1 else 0
            pyautogui.click(x, y)
            return {"success": True, "message": f"Clicked at ({x}, {y})"}
            
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
    """Fetch and execute commands from Firebase"""
    global LAST_COMMAND_HASH
    
    commands = fetch_commands()
    if not commands:
        return
    
    # Create hash to detect changes
    current_hash = hash(json.dumps(commands, sort_keys=True))
    if current_hash == LAST_COMMAND_HASH:
        return
    
    LAST_COMMAND_HASH = current_hash
    
    print(f"\n[{datetime.now()}] Found {len(commands)} command(s)")
    
    results = []
    for cmd in commands:
        result = execute_command(cmd)
        result_data = {
            "id": cmd.get("id"),
            "command": cmd.get("command"),
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
        results.append(result_data)
        send_result(result_data)
        
        status = "✅" if result.get("success") else "❌"
        print(f"{status} {cmd.get('id')}: {result.get('message', result.get('error', 'Done'))}")
    
    # Save locally too
    with open(RESULTS_FILE, 'w') as f:
        json.dump({"results": results, "last_update": datetime.now().isoformat()}, f, indent=2)
    
    print(f"Completed {len(commands)} command(s)")

# Main loop
print("\nExecutor running. Press Ctrl+C to stop.")
print("Checking Firebase every second...\n")

try:
    while True:
        process_commands()
        time.sleep(POLL_INTERVAL)
        
except KeyboardInterrupt:
    print("\n\nExecutor stopped.")
    print("Goodbye!")
