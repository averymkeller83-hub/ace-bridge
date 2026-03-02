import pyautogui
import time
import json
import urllib.request
from datetime import datetime

FIREBASE_URL = "https://ace-bridge-commands-default-rtdb.firebaseio.com/"
COMMANDS_URL = f"{FIREBASE_URL}commands.json"

print("ACE COMMAND EXECUTOR - Firebase")
print("=" * 40)
print(f"Checking: {COMMANDS_URL}")
print("Press Ctrl+C to stop")
print("=" * 40)

last_hash = None

while True:
    try:
        with urllib.request.urlopen(COMMANDS_URL, timeout=5) as response:
            data = json.loads(response.read().decode())
            
        if data is None:
            time.sleep(1)
            continue
            
        commands = list(data.values()) if isinstance(data, dict) else data
        if not commands:
            time.sleep(1)
            continue
            
        current_hash = hash(json.dumps(commands, sort_keys=True))
        if current_hash == last_hash:
            time.sleep(1)
            continue
            
        last_hash = current_hash
        print(f"\n[{datetime.now()}] Found {len(commands)} commands")
        
        for cmd in commands:
            cmd_id = cmd.get("id", "unknown")
            command = cmd.get("command", "")
            args = cmd.get("args", [])
            
            print(f"Executing: {cmd_id} - {command}")
            
            try:
                if command == "open":
                    app = args[0] if args else ""
                    pyautogui.keyDown('win')
                    pyautogui.keyUp('win')
                    time.sleep(0.5)
                    pyautogui.typewrite(app, interval=0.05)
                    time.sleep(0.3)
                    pyautogui.keyDown('return')
                    pyautogui.keyUp('return')
                    time.sleep(2)
                    print(f"  Opened: {app}")
                    
                elif command == "type":
                    text = args[0] if args else ""
                    pyautogui.typewrite(text, interval=0.05)
                    print(f"  Typed: {text[:30]}...")
                    
                elif command == "sleep":
                    seconds = int(args[0]) if args else 1
                    time.sleep(seconds)
                    print(f"  Slept: {seconds}s")
                    
                elif command == "key":
                    for key in args:
                        pyautogui.keyDown(key)
                    for key in reversed(args):
                        pyautogui.keyUp(key)
                    print(f"  Keys: {'+'.join(args)}")
                    
            except Exception as e:
                print(f"  Error: {e}")
                
        print("Commands completed")
        
    except KeyboardInterrupt:
        print("\n\nStopped by user")
        break
    except Exception as e:
        print(f"\nError: {e}")
        time.sleep(1)
