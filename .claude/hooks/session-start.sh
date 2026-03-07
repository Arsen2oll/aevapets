#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install dependencies based on what's present in the project
cd "$CLAUDE_PROJECT_DIR"

# Node.js dependencies
if [ -f "package.json" ]; then
  npm install
fi

# Python dependencies
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
fi

if [ -f "pyproject.toml" ]; then
  pip install -e .
fi
