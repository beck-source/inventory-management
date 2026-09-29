#!/bin/bash
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install Python backend dependencies (includes dev deps for pytest)
cd "$CLAUDE_PROJECT_DIR/server"
uv sync

# Install Node frontend dependencies
cd "$CLAUDE_PROJECT_DIR/client"
npm install
