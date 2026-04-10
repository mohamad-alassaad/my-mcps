#!/bin/bash
# Start Ollama in the background
ollama serve &

# Wait for the server to be ready
sleep 5

# Pull Gemma 3 models (e.g., 4b and 12b)
echo "Pulling Gemma 3 models..."
ollama pull gemma3:4b

# Keep the container running
wait