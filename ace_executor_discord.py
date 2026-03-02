import pyautogui
import time
import json
import os
import urllib.request
from datetime import datetime

# Configuration
GITHUB_REPO = "averymkeller83-hub/ace-bridge"
COMMANDS_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/commands.json"
RESULTS_FILE = r"C:\Users\avery\ace-results.json"
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1478081972008910879/N-DlsEHCwlc8vg_mwsaZ2ao_EmTcgHi1-d9pMo1O_UksK5zTk97TQbmewSVWS2uMIdat"
POLL_INTERVAL = 10  # seconds
LAST_COMMAND_HASH = None

print("=" * 50)
print("ACE COMMAND EXECUTOR - GitHub Sync + Discord")
print("=" * 50)
print(f"Repository: {GITHUB_REPO}")
print(f"Results: {RESULTS_FILE}")
print(f"Poll interval: {POLL_INTERVAL} seconds")
print("=" * 50)

def send_discord_message(content, image_path=None):
    """Send message to Discord webhook"""
    try:
        if image_path and os.path.exists(image_path):
            # Send with image using multipart form (no external libs)
            boundary = '----WebKitFormBoundary' + str(int(time.time()))
            
            # Build multipart form data
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            body = []
            body.append(f'------{boundary}'.encode())
            body.append(f'Content-Disposition: form-data; name="content"'.encode())
            body.append(b'')
            body.append(content.encode())
            body.append(f'------{boundary}'.encode())
            body.append(f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(image_path)}"'.encode())
            body.append(b'Content-Type: image/png')
            body.append(b'')
            body.append(image_data)
            body.append(f'------{boundary}--'.encode())
            
            data = b'\r\n'.join(body)
            
            req = urllib.request.Request(
                DISCORD_WEBHOOK,
                data=data,
                headers={'Content-Type': f'multipart/form-data; boundary=----{boundary}'}
            )
            urllib.request.urlopen(req)
        else:
            # Send text only
            data = json.dumps({'content': content}).encode()
            req = urllib.request.Request(
                DISCORD_WEBHOOK,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            urllib.request.urlopen(req)
    except Exception as e:
        print(f"Discord error: {e}")

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
            return {"success": True, "message": f"Screenshot saved: {filename}", "screenshot": filename}
            
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
    
    current_hash = hash(json.dumps(commands, sort_keys=True))
    if current_hash == LAST_COMMAND_HASH:
        return
    
    LAST_COMMAND_HASH = current_hash
    
    # Notify Discord that commands were received
    send_discord_message(f"🤖 Received {len(commands)} command(s). Executing...")
    
    results = []
    for cmd in commands:
        result = execute_command(cmd)
        results.append({
            "id": cmd.get("id"),
            "command": cmd.get("command"),
            "timestamp": datetime.now().isoformat(),
            "result": result
        })
        
        # Send screenshot to Discord if available
        if "screenshot" in result:
            send_discord_message(f"📸 Screenshot from {cmd.get('id')}:", result["screenshot"])
            os.remove(result["screenshot"])  # Clean up
        
        # Send status update
        status = "✅" if result.get("success") else "❌"
        send_discord_message(f"{status} {cmd.get('id')}: {result.get('message', result.get('error', 'Unknown'))}")
    
    # Save results locally
    with open(RESULTS_FILE, 'w') as f:
        json.dump({"results": results, "last_update": datetime.now().isoformat()}, f, indent=2)
    
    # Final summary
    send_discord_message(f"✅ Completed {len(commands)} command(s). Waiting for next batch...")
    print(f"\nExecuted {len(commands)} command(s)")

# Main loop
print("\nExecutor running. Press Ctrl+C to stop.")
print("Fetching commands from GitHub...\n")

# Send startup message
send_discord_message("🚀 Ace Executor started! Monitoring GitHub for commands...")

try:
    while True:
        process_commands()
        time.sleep(POLL_INTERVAL)
        
except KeyboardInterrupt:
    send_discord_message("🛑 Executor stopped by user.")
    print("\n\nExecutor stopped.")
    print("Goodbye!")
