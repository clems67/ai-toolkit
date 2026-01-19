#!/usr/bin/env bash
set -euo pipefail

# ---- Configuration ---------------------------------------------------------
REQUIRED_PACKAGES=(ffmpeg curl ca-certificates)
# ---------------------------------------------------------------------------

echo "Installing system dependencies..."
sudo apt update
sudo apt install -y "${REQUIRED_PACKAGES[@]}"

echo "Installing uv (if not already installed)..."
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
else
    echo "uv already installed"
fi

# Ensure uv is available in this shell
export PATH="$HOME/.cargo/bin:$PATH"

echo "Syncing Python dependencies..."
uv sync

echo "Bootstrap completed successfully."