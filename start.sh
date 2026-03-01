#!/bin/bash
# Quick start script for Ace Bridge

echo "==================================="
echo "     Ace Bridge Setup"
echo "==================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi
echo "✓ Python 3 found"

# Check Ace
if ! command -v ace &> /dev/null; then
    echo "⚠️  Ace not found in PATH. You may need to specify the full path."
else
    echo "✓ Ace found"
fi

# Check Git
if ! command -v git &> /dev/null; then
    echo "⚠️  Git not found. Auto-push will not work."
else
    echo "✓ Git found"
fi

echo ""
echo "Starting watcher..."
echo "Press Ctrl+C to stop"
echo ""

python3 ace-watcher.py "$@"
