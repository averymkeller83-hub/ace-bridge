import pyautogui
import time
import json
import urllib.request
from datetime import datetime
import sys

# Safety settings
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.1  # Small pause between actions

FIREBASE_URL = "https://ace-bridge-commands-default-rtdb.firebaseio.com/"
COMMANDS_URL = f"{FIREBASE_URL}commands.json"
RESULTS_URL = f"{FIREBASE_URL}results.json"

def safe_type(text):
    """Type text with error handling and key release"""
    try:
        # Type with slower speed for safety
        pyautogui.typewrite(text, interval=0.1)
        return True
    except Exception as e:
        print(f"Typing error: {e}")
        # Release all modifier keys
        for key in ['ctrl', 'alt', 'shift', 'win']:
            try:
                pyautogui.keyUp(key)
            except:
                pass
        return False

def safe_key(keys):
    """Press keys with error handling"""
    try:
        for key in keys:
            pyautogui.keyDown(key)
        time.sleep(0.1)
        for key in reversed(keys):
            pyautogui.keyUp(key)
        return True
    except Exception as e:
        print(f"Key error: {e}")
        # Release all keys
        for key in ['ctrl', 'alt', 'shift', 'win']:
            try:
                pyautogui.keyUp(key)
            except:
                pass
        return False

def fetch_commands():
    """Fetch commands from Firebase"""
    try:
        with urllib.request.urlopen(COMMANDS_URL, timeout=5) as response:
            data = json.loads(response.read().decode())
        if data is None:
            return []
        return list(data.values()) if isinstance(data, dict) else data
    except Exception as e:
        print(f"Fetch error: {e}")
        return []

def send_result(result):
    """Send result to Firebase"""
    try:
        data = json.dumps(result).encode()
        req = urllib.request.Request(
            RESULTS_URL,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Send error: {e}")

def execute_command(cmd):
    """Execute command with full error handling"""
    cmd_id = cmd.get("id", "unknown")
    command = cmd.get("command", "")
    args = cmd.get("args", [])
    
    print(f"[{datetime.now()}] {cmd_id}: {command}")
    
    try:
        if command == "open":
            app = args[0] if args else ""
            pyautogui.keyDown('win')
            pyautogui.keyUp('win')
            time.sleep(0.5)
            if not safe_type(app):
                return {"success": False, "error": "Typing failed"}
            time.sleep(0.3)
            if not safe_key(['return']):
                return {"success": False, "error": "Key failed"}
            time.sleep(2)
            return {"success": True, "message": f"Opened {app}"}
            
        elif command == "type":
            text = args[0] if args else ""
            if safe_type(text):
                return {"success": True, "message": f"Typed: {text[:30]}..."}
            else:
                return {"success": False, "error": "Typing failed"}
            
        elif command == "sleep":
            seconds = int(args[0]) if args else 1
            time.sleep(seconds)
            return {"success": True, "message": f"Slept {seconds}s"}
            
        elif command == "key":
            if safe_key(args):
                return {"success": True, "message": f"Keys: {args}"}
            else:
                return {"success": False, "error": "Key failed"}
                
        else:
            return {"success": False, "error": f"Unknown: {command}"}
            
    except Exception as e:
        # Emergency key release
        for key in ['ctrl', 'alt', 'shift', 'win']:
            try:
                pyautogui.keyUp(key)
            except:
                pass
        return {"success": False, "error": str(e)}

# Main loop
print("=" * 50)
print("SAFE EXECUTOR - Firebase")
print("=" * 50)
print("Press Ctrl+C to stop")
print("Move mouse to top-left corner to emergency stop")
print("=" * 50)

last_hash = None

try:
    while True:
        try:
            commands = fetch_commands()
            if not commands:
                time.sleep(1)
                continue
                
            current_hash = hash(json.dumps(commands, sort_keys=True))
            if current_hash == last_hash:
                time.sleep(1)
                continue
                
            last_hash = current_hash
            print(f"\nFound {len(commands)} commands")
            
            for cmd in commands:
                result = execute_command(cmd)
                send_result({
                    "id": cmd.get("id"),
                    "timestamp": datetime.now().isoformat(),
                    "result": result
                })
                status = "✅" if result["success"] else "❌"
                print(f"  {status} {cmd.get('id')}")
                
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(1)
            
except KeyboardInterrupt:
    print("\n\nStopped safely")
    # Final key release
    for key in ['ctrl', 'alt', 'shift', 'win']:
        try:
            pyautogui.keyUp(key)
        except:
            pass
    print("All keys released")
