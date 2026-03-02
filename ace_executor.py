import pyautogui
import time
import json
import os
import subprocess
from datetime import datetime

# Configuration
COMMANDS_FILE = r"C:\Users\avery\ace-commands.json"
RESULTS_FILE = r"C:\Users\avery\ace-results.json"
POLL_INTERVAL = 30  # seconds

print("=" * 50)
print("ACE COMMAND EXECUTOR - Starting...")
print("=" * 50)
print(f"Watching: {COMMANDS_FILE}")
print(f"Results: {RESULTS_FILE}")
print(f"Poll interval: {POLL_INTERVAL} seconds")
print("=" * 50)

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
            # Open application or URL
            app = args[0] if args else ""
            print(f"Opening: {app}")
            
            # Open Run dialog
            pyautogui.keyDown('win')
            pyautogui.keyUp('win')
            time.sleep(0.5)
            
            # Type application
            pyautogui.typewrite(app, interval=0.01)
            time.sleep(0.3)
            
            # Press Enter
            pyautogui.keyDown('return')
            pyautogui.keyUp('return')
            time.sleep(2)
            
            return {"success": True, "message": f"Opened {app}"}
            
        elif command == "type":
            # Type text
            text = args[0] if args else ""
            pyautogui.typewrite(text, interval=0.01)
            return {"success": True, "message": f"Typed: {text[:50]}..."}
            
        elif command == "click":
            # Click at coordinates
            x = int(args[0]) if len(args) > 0 else 0
            y = int(args[1]) if len(args) > 1 else 0
            pyautogui.click(x, y)
            return {"success": True, "message": f"Clicked at ({x}, {y})"}
            
        elif command == "screenshot":
            # Take screenshot
            screenshot = pyautogui.screenshot()
            filename = args[0] if args else f"screenshot_{int(time.time())}.png"
            screenshot.save(filename)
            return {"success": True, "message": f"Screenshot saved: {filename}"}
            
        elif command == "sleep":
            # Wait
            seconds = int(args[0]) if args else 1
            time.sleep(seconds)
            return {"success": True, "message": f"Slept for {seconds} seconds"}
            
        elif command == "key":
            # Press key combination
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
    """Check for and execute commands"""
    if not os.path.exists(COMMANDS_FILE):
        return
    
    try:
        with open(COMMANDS_FILE, 'r') as f:
            data = json.load(f)
        
        commands = data.get("commands", [])
        if not commands:
            return
        
        results = []
        
        for cmd in commands:
            result = execute_command(cmd)
            results.append({
                "id": cmd.get("id"),
                "command": cmd.get("command"),
                "timestamp": datetime.now().isoformat(),
                "result": result
            })
        
        # Save results
        with open(RESULTS_FILE, 'w') as f:
            json.dump({"results": results}, f, indent=2)
        
        # Clear commands
        with open(COMMANDS_FILE, 'w') as f:
            json.dump({"commands": []}, f)
        
        print(f"\nExecuted {len(commands)} command(s)")
        print(f"Results saved to: {RESULTS_FILE}")
        
    except Exception as e:
        print(f"Error processing commands: {e}")

# Main loop
print("\nExecutor running. Press Ctrl+C to stop.")
print("Waiting for commands...\n")

try:
    while True:
        process_commands()
        time.sleep(POLL_INTERVAL)
        
except KeyboardInterrupt:
    print("\n\nExecutor stopped by user.")
    print("Goodbye!")
