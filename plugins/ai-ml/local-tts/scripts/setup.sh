#!/usr/bin/env bash
# Setup script for local-tts plugin — creates Python venv and installs dependencies.
# Idempotent: safe to run multiple times.
set -euo pipefail

VENV_DIR="${LOCAL_TTS_VENV:-$HOME/.local-tts/venv}"
PYTHON="${LOCAL_TTS_PYTHON:-python3}"

# Find a suitable Python (3.10+)
find_python() {
    for candidate in python3.12 python3.11 python3.10 python3; do
        if command -v "$candidate" &>/dev/null; then
            version=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
            major=$(echo "$version" | cut -d. -f1)
            minor=$(echo "$version" | cut -d. -f2)
            if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
                echo "$candidate"
                return 0
            fi
        fi
    done
    return 1
}

echo "[local-tts] Setting up environment..."

if [ -f "$VENV_DIR/bin/python" ]; then
    # Check if voxcpm is installed
    if "$VENV_DIR/bin/python" -c "import voxcpm" 2>/dev/null; then
        echo "[local-tts] Environment already set up at $VENV_DIR"
        exit 0
    fi
fi

PYTHON=$(find_python) || {
    echo "ERROR: Python 3.10+ required but not found. Install Python 3.10+ and try again." >&2
    exit 1
}

echo "[local-tts] Using $PYTHON ($(${PYTHON} --version 2>&1))"
echo "[local-tts] Creating venv at $VENV_DIR..."
mkdir -p "$(dirname "$VENV_DIR")"
"$PYTHON" -m venv "$VENV_DIR"

echo "[local-tts] Installing dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install voxcpm -q

echo "[local-tts] Setup complete!"
echo "[local-tts] Venv: $VENV_DIR"
echo "[local-tts] First generation will download ~10 GB model weights to ~/.cache/huggingface/"
