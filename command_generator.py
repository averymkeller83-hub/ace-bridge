# Ace Bridge Command Generator
# This script is used by Jarvis to create commands

import json
import uuid
from datetime import datetime
from pathlib import Path

def create_command(command, args=None, description=""):
    """Create a new Ace command file"""
    
    cmd_id = str(uuid.uuid4())[:8]
    
    command_data = {
        "id": cmd_id,
        "command": command,
        "args": args or [],
        "timestamp": datetime.now().isoformat(),
        "description": description
    }
    
    # Save to commands directory
    cmd_file = Path("commands") / f"{cmd_id}.json"
    with open(cmd_file, "w") as f:
        json.dump(command_data, f, indent=2)
    
    return cmd_id, cmd_file

# Example commands for Google Sheets automation

def create_google_sheet(name="New Sheet"):
    """Command to create a new Google Sheet"""
    return create_command(
        command="browser",
        args=["open", f"https://sheets.new"],
        description=f"Create new Google Sheet: {name}"
    )

def open_url(url):
    """Command to open any URL"""
    return create_command(
        command="browser",
        args=["open", url],
        description=f"Open URL: {url}"
    )

def type_text(text):
    """Command to type text"""
    return create_command(
        command="input",
        args=["type", text],
        description=f"Type text: {text[:50]}..."
    )

def click_element(x, y):
    """Command to click at coordinates"""
    return create_command(
        command="input",
        args=["click", str(x), str(y)],
        description=f"Click at ({x}, {y})"
    )

if __name__ == "__main__":
    # Test: Create a command to open Google Sheets
    cmd_id, cmd_file = create_google_sheet("ClawWork Dashboard")
    print(f"Created command: {cmd_id}")
    print(f"File: {cmd_file}")
