#!/bin/bash

# Factory Inventory Management System - Install Script
# Usage: curl -fsSL https://raw.githubusercontent.com/juliareichert6/inventory-management/main/install.sh | bash
# Or locally: ./install.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Factory Inventory Management System - Installer${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Determine project root (works both when piped via curl and run locally)
if [ -n "$BASH_SOURCE" ] && [ "$BASH_SOURCE" != "" ]; then
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    PROJECT_ROOT="$SCRIPT_DIR"
else
    PROJECT_ROOT="$(pwd)"
fi

# ── Prerequisite checks ──────────────────────────────────────────────────────

check_command() {
    if ! command -v "$1" &>/dev/null; then
        echo -e "${RED}Error: '$1' is required but not installed.${NC}"
        echo -e "  ${YELLOW}$2${NC}"
        exit 1
    fi
}

echo -e "${BLUE}Checking prerequisites...${NC}"

check_command node  "Install Node.js from https://nodejs.org (v18+ recommended)"
check_command npm   "npm is bundled with Node.js"
check_command python3 "Install Python 3.11+ from https://python.org"

NODE_VERSION=$(node -e "process.stdout.write(process.versions.node)")
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

echo -e "  Node.js  : ${GREEN}${NODE_VERSION}${NC}"
echo -e "  Python   : ${GREEN}${PYTHON_VERSION}${NC}"

# Require Python 3.11+
PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; }; then
    echo -e "${RED}Error: Python 3.11 or higher is required (found ${PYTHON_VERSION}).${NC}"
    exit 1
fi

# Check for uv; offer to install if missing
if ! command -v uv &>/dev/null; then
    echo -e "\n${YELLOW}uv (Python package manager) not found.${NC}"
    echo -e "uv is recommended for fast, reproducible installs."
    read -r -p "Install uv now? [Y/n] " REPLY
    REPLY="${REPLY:-Y}"
    if [[ "$REPLY" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Installing uv...${NC}"
        curl -LsSf https://astral.sh/uv/install.sh | sh
        # Add to current shell PATH
        export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
        if ! command -v uv &>/dev/null; then
            echo -e "${YELLOW}uv installed but not in PATH. Falling back to pip.${NC}"
            USE_PIP=1
        else
            echo -e "${GREEN}uv installed successfully.${NC}"
        fi
    else
        echo -e "${YELLOW}Skipping uv; will use pip instead.${NC}"
        USE_PIP=1
    fi
fi

echo ""

# ── Backend installation ─────────────────────────────────────────────────────

echo -e "${BLUE}Installing backend dependencies...${NC}"
cd "$PROJECT_ROOT/server"

if [ -z "$USE_PIP" ]; then
    uv venv --python python3
    uv sync
else
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip -q
    pip install fastapi uvicorn pydantic -q
fi

echo -e "${GREEN}  Backend dependencies installed.${NC}"

# ── Frontend installation ────────────────────────────────────────────────────

echo -e "${BLUE}Installing frontend dependencies...${NC}"
cd "$PROJECT_ROOT/client"
npm install --silent
echo -e "${GREEN}  Frontend dependencies installed.${NC}"

# ── Environment file ─────────────────────────────────────────────────────────

cd "$PROJECT_ROOT"
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}  Created .env from .env.example.${NC}"
fi

# ── Done ─────────────────────────────────────────────────────────────────────

echo -e "\n${GREEN}Installation complete!${NC}\n"
echo -e "To start the application:"
echo -e "  ${YELLOW}./scripts/start.sh${NC}"
echo -e ""
echo -e "Or manually:"
echo -e "  Backend : ${YELLOW}cd server && uv run python main.py${NC}"
echo -e "  Frontend: ${YELLOW}cd client && npm run dev${NC}"
echo -e ""
echo -e "  Frontend : ${BLUE}http://localhost:3000${NC}"
echo -e "  API      : ${BLUE}http://localhost:8001${NC}"
echo -e "  API Docs : ${BLUE}http://localhost:8001/docs${NC}"
