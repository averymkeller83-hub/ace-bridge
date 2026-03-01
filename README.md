# Ace Bridge

Bridge system to allow Jarvis (cloud) to command Ace (local)

## How It Works

1. Jarvis writes command files to `commands/` directory
2. Your local computer runs `ace-watcher.py` which watches for new commands
3. Watcher executes Ace with the command
4. Results are written to `results/` directory
5. (Optional) Results are pushed back to GitHub for Jarvis to read

## Setup

### 1. Clone/Push This Repo to GitHub

```bash
# Create new repo on GitHub: ace-bridge
git init
git add .
git commit -m "Initial Ace bridge"
git remote add origin https://github.com/YOUR_USERNAME/ace-bridge.git
git push -u origin main
```

### 2. Clone to Your Local Computer

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/ace-bridge.git
```

### 3. Install Python Dependencies

```bash
pip install watchdog requests
```

### 4. Start the Watcher

```bash
cd ~/ace-bridge
python3 ace-watcher.py
```

Or with custom path:
```bash
python3 ace-watcher.py /path/to/ace-bridge
```

## Command Format

Commands are JSON files in `commands/`:

```json
{
  "id": "unique-id-001",
  "command": "browser",
  "args": ["open", "https://sheets.google.com"],
  "timestamp": "2026-03-02T02:00:00Z",
  "description": "Open Google Sheets"
}
```

## Result Format

Results appear in `results/`:

```json
{
  "id": "unique-id-001",
  "command": "browser",
  "args": ["open", "https://sheets.google.com"],
  "timestamp": "2026-03-02T02:00:05Z",
  "result": {
    "success": true,
    "stdout": "...",
    "stderr": "",
    "returncode": 0
  }
}
```

## Workflow

1. **You tell Jarvis:** "Create a Google Sheet for project X"
2. **Jarvis creates:** `commands/create-sheet-001.json`
3. **Watcher detects:** New command file
4. **Ace executes:** Opens Chrome, creates sheet
5. **Result saved:** `results/create-sheet-001.json`
6. **Jarvis reads:** Result and reports back to you

## Security

- Only you can push commands (GitHub auth)
- Watcher only executes from `commands/` directory
- Processed commands are archived, not deleted

## Troubleshooting

**Watcher not detecting commands:**
- Check file permissions
- Ensure JSON is valid
- Check logs in `logs/`

**Ace not found:**
- Ensure Ace is in your PATH
- Or modify `ace-watcher.py` to use full path to Ace binary

**Git push failing:**
- Ensure git is configured with your credentials
- Or run watcher without push (results stay local)
