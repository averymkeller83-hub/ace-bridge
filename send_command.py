#!/usr/bin/env python3
"""
Send commands to Firebase from Jarvis
"""

import json
import urllib.request
import sys

FIREBASE_URL = "https://ace-bridge-commands-default-rtdb.firebaseio.com/"
COMMANDS_URL = f"{FIREBASE_URL}commands.json"

def send_command(commands_list):
    """Send commands to Firebase"""
    try:
        data = json.dumps(commands_list).encode()
        req = urllib.request.Request(
            COMMANDS_URL,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='PUT'  # PUT replaces entire node
        )
        response = urllib.request.urlopen(req)
        print(f"✅ Commands sent successfully!")
        print(f"Response: {response.read().decode()}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Example command
    test_commands = [
        {
            "id": "cmd-001",
            "command": "open",
            "args": ["chrome"],
            "description": "Open Chrome"
        },
        {
            "id": "cmd-002",
            "command": "sleep",
            "args": ["3"],
            "description": "Wait"
        },
        {
            "id": "cmd-003",
            "command": "type",
            "args": ["Hello from Firebase!"],
            "description": "Type message"
        }
    ]
    
    print("Sending test commands to Firebase...")
    send_command(test_commands)
