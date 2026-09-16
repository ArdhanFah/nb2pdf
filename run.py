#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
VENV_DIR = BASE_DIR / ".venv"
VENV_PYTHON = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
VENV_PIP = VENV_DIR / ("Scripts/pip.exe" if os.name == "nt" else "bin/pip")


def setup_venv_and_run():
    print("========================================================")
    print("⚡ nb2pdf — Neobrutalism Web Application Launcher")
    print("========================================================")

    # 1. Create venv if missing
    if not VENV_DIR.exists():
        print("📦 Creating virtual environment (.venv)...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])

    # 2. Install dependencies into venv
    print("🔍 Installing/verifying dependencies in .venv...")
    subprocess.check_call([str(VENV_PIP), "install", "-q", "-e", str(BASE_DIR)])
    print("✅ Dependencies ready!")

    print("\n🚀 Starting Web Server at http://localhost:5000")
    print("========================================================\n")

    # 3. Launch app.py using venv python
    port = sys.argv[1] if len(sys.argv) > 1 else "5000"
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(BASE_DIR / "app.py"), port])


if __name__ == "__main__":
    setup_venv_and_run()
