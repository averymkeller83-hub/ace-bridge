#!/usr/bin/env python3
"""Ace Bridge Watcher — Smart wrapper with screenshot context + screen recording + Telegram"""

import json, os, subprocess, time, shutil, threading, requests, glob
from pathlib import Path
from datetime import datetime

REPO_PATH = Path.home() / "ace-bridge"
COMMANDS_DIR = REPO_PATH / "commands"
PROCESSED_DIR = REPO_PATH / "commands" / "processed"
RESULTS_DIR = REPO_PATH / "results"
LOGS_DIR = REPO_PATH / "logs"
RECORDINGS_DIR = Path("/tmp/jarvis-recordings")
POLL_INTERVAL = 5
WAIT_AFTER_COMMAND = 60

# Telegram config
TELEGRAM_BOT_TOKEN = "8677077283:AAEDTXwV-m9TKl_GNk7cjwJMPBz1ECaWL3E"
TELEGRAM_CHAT_ID = "7902061632"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    log_file = LOGS_DIR / f"watcher-{datetime.now().strftime('%Y-%m-%d')}.log"
    with open(log_file, "a") as f:
        f.write(line + "\n")

def take_screenshot(output_path: str) -> bool:
    """Take a screenshot using screencapture."""
    try:
        result = subprocess.run(
            ["/usr/sbin/screencapture", "-x", "-t", "png", output_path],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        log(f"Screenshot failed: {e}")
        return False

def start_screen_recording(output_path: str) -> subprocess.Popen:
    """Start screen recording using ffmpeg with AVFoundation."""
    try:
        proc = subprocess.Popen(
            [
                "/opt/homebrew/bin/ffmpeg",
                "-y",
                "-f", "avfoundation",
                "-capture_cursor", "1",
                "-capture_mouse_clicks", "1",
                "-framerate", "15",
                "-i", "1:",  # Screen 1, no audio
                "-vcodec", "libx264",
                "-preset", "ultrafast",
                "-crf", "30",
                output_path
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        log(f"Recording started → {output_path}")
        return proc
    except Exception as e:
        log(f"Recording start failed: {e}")
        return None

def stop_screen_recording(proc: subprocess.Popen) -> bool:
    """Stop screen recording gracefully."""
    if proc is None:
        return False
    try:
        proc.stdin.write(b"q")
        proc.stdin.flush()
        proc.wait(timeout=10)
        log("Recording stopped.")
        return True
    except Exception:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        return True

def send_to_telegram_video(video_path: str, caption: str = "") -> bool:
    """Send a video file to Telegram."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
        with open(video_path, "rb") as vf:
            resp = requests.post(
                url,
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1024]},
                files={"video": vf},
                timeout=60
            )
        if resp.ok:
            log(f"Video sent to Telegram: {video_path}")
            return True
        else:
            log(f"Telegram video send failed: {resp.text[:200]}")
            return False
    except Exception as e:
        log(f"Telegram video error: {e}")
        return False

def send_to_telegram_photo(photo_path: str, caption: str = "") -> bool:
    """Send a photo to Telegram."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        with open(photo_path, "rb") as pf:
            resp = requests.post(
                url,
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1024]},
                files={"photo": pf},
                timeout=30
            )
        return resp.ok
    except Exception as e:
        log(f"Telegram photo error: {e}")
        return False

def send_to_telegram_message(text: str) -> bool:
    """Send a text message to Telegram."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text[:4096]},
            timeout=15
        )
        return resp.ok
    except Exception as e:
        log(f"Telegram message error: {e}")
        return False

def send_to_ace(command_text: str, screenshot_path: str = None):
    """Send command to Ace via AppleScript, with optional screenshot context."""
    try:
        # Build command with screenshot context if available
        context_note = ""
        if screenshot_path and os.path.exists(screenshot_path):
            context_note = " [Screenshot taken before this command — check screen state]"

        full_command = command_text + context_note
        safe = full_command.replace('\\', '\\\\').replace('"', '\\"')

        script = f'''
tell application "Ace" to activate
delay 3
tell application "System Events"
    tell process "Ace"
        keystroke "{safe}"
        delay 1
        key code 36
    end tell
end tell
'''
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0, result.stderr or "OK"
    except Exception as e:
        return False, str(e)

def push_to_github():
    try:
        subprocess.run(["git", "-C", str(REPO_PATH), "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", str(REPO_PATH), "commit", "-m", f"Results {datetime.now().isoformat()}"], capture_output=True)
        subprocess.run(["git", "-C", str(REPO_PATH), "push"], capture_output=True)
        log("Pushed")
    except:
        pass

def process_command(cmd_file: Path):
    processing_file = COMMANDS_DIR / f"_processing_{cmd_file.name}"
    try:
        cmd_file.rename(processing_file)
    except:
        return

    try:
        with open(processing_file) as f:
            data = json.load(f)
        cmd_id = data.get("id", "unknown")
        command_text = data.get("command", "")
        log(f"Processing command: {command_text[:80]}")

        # 1. Take screenshot before sending
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = str(RECORDINGS_DIR / f"pre-{cmd_id}-{ts}.png")
        if take_screenshot(screenshot_path):
            log(f"Screenshot captured: {screenshot_path}")
            send_to_telegram_photo(
                screenshot_path,
                caption=f"📸 Pre-command screenshot\n🆔 {cmd_id}\n💬 {command_text[:200]}"
            )
        else:
            screenshot_path = None

        # 2. Start screen recording
        recording_path = str(RECORDINGS_DIR / f"rec-{cmd_id}-{ts}.mp4")
        recorder = start_screen_recording(recording_path)
        if recorder:
            time.sleep(2)  # Let ffmpeg init

        # 3. Send command to Ace
        log(f"Sending to Ace: {command_text[:80]}")
        success, output = send_to_ace(command_text, screenshot_path)
        log(f"Sent. Waiting {WAIT_AFTER_COMMAND}s...")

        # 4. Wait for Ace to process
        time.sleep(WAIT_AFTER_COMMAND)

        # 5. Stop recording
        if recorder:
            stop_screen_recording(recorder)
            time.sleep(1)
            # Send recording to Telegram
            if os.path.exists(recording_path) and os.path.getsize(recording_path) > 1000:
                send_to_telegram_video(
                    recording_path,
                    caption=f"🎬 Ace session recording\n🆔 {cmd_id}\n✅ Success: {success}\n💬 {command_text[:150]}"
                )
            else:
                log(f"Recording too small or missing: {recording_path}")
                send_to_telegram_message(
                    f"⚠️ Recording unavailable for cmd {cmd_id}\n✅ Success: {success}\n💬 {command_text[:200]}"
                )

        # 6. Save result
        with open(RESULTS_DIR / f"{cmd_id}.json", "w") as f:
            json.dump({
                "id": cmd_id,
                "command": command_text,
                "timestamp": datetime.now().isoformat(),
                "screenshot": screenshot_path,
                "recording": recording_path,
                "result": {"success": success, "output": output}
            }, f, indent=2)

        shutil.move(str(processing_file), str(PROCESSED_DIR / cmd_file.name))
        push_to_github()

    except Exception as e:
        log(f"Error processing command: {e}")
        try:
            shutil.move(str(processing_file), str(cmd_file))
        except:
            pass

log("Ace Watcher — Smart mode (screenshot + recording + Telegram)")

while True:
    try:
        cmd_files = sorted(COMMANDS_DIR.glob("*.json"))
        if cmd_files:
            process_command(cmd_files[0])
        push_to_github()
    except Exception as e:
        log(f"Loop error: {e}")
    time.sleep(POLL_INTERVAL)
