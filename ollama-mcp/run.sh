#!/usr/bin/env bash
# Launch the Code Review MCP server against a local Ollama install.
# Usage:   ./run.sh
set -e

export OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-gemma3:4b}"
export MCP_HOST="${MCP_HOST:-0.0.0.0}"
export MCP_PORT="${MCP_PORT:-8081}"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$DIR/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    . "$DIR/.venv/bin/activate"
fi

echo "Ollama  : $OLLAMA_HOST (model: $OLLAMA_MODEL)"
echo "MCP SSE : http://localhost:$MCP_PORT/sse"
echo

python "$DIR/server.py"
