#!/bin/bash
set -e

# Start Ollama in the background
ollama serve &
OLLAMA_PID=$!

# Wait for the server to be ready
echo "Waiting for Ollama to start..."
until curl -s http://localhost:11434/api/tags >/dev/null 2>&1; do
  sleep 1
done

# Pull the default model (override via OLLAMA_PULL_MODEL env var)
MODEL="${OLLAMA_PULL_MODEL:-gemma3:4b}"
echo "Pulling model: $MODEL"
ollama pull "$MODEL" || echo "Warning: failed to pull $MODEL"

echo "Ollama ready."
wait $OLLAMA_PID
