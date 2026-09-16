#!/usr/bin/env bash

# Exit on error
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================================"
echo "⚡ nb2pdf — Neobrutalism Web Application Launcher"
echo "========================================================"

VENV_DIR="$SCRIPT_DIR/.venv"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment (.venv)..."
    python3 -m venv "$VENV_DIR"
fi

PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"

echo "🔍 Checking & installing dependencies in .venv..."
"$PIP_BIN" install -q -e .

echo "✅ Dependencies ready!"
echo ""
echo "🚀 Starting Web Server on http://localhost:5000..."
echo "========================================================"

# Run Web Server using venv python
"$PYTHON_BIN" app.py "$@"
