#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color (reset)

color_echo() {
    local color="$1"
    local message="$2"

    # Validate color
    case "$color" in
        red)    echo -e "${RED}${message}${NC}" ;;
        green)  echo -e "${GREEN}${message}${NC}" ;;
        yellow) echo -e "${YELLOW}${message}${NC}" ;;
        blue)   echo -e "${BLUE}${message}${NC}" ;;
        *)      echo "$message" ;; # Default: no color
    esac
}

# ---- Configuration ---------------------------------------------------------
REQUIRED_PACKAGES=(ffmpeg curl ca-certificates)
# ---------------------------------------------------------------------------

color_echo blue "Installing system dependencies..."
sudo apt update
sudo apt install -y "${REQUIRED_PACKAGES[@]}"

color_echo blue "Installing uv (if not already installed)..."
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
else
    color_echo green "uv already installed"
fi

# Ensure uv is available in this shell
export PATH="$HOME/.cargo/bin:$PATH"

color_echo blue "Syncing remaining Python dependencies..."
uv sync