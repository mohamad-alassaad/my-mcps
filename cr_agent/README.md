# Meeting Minutes AI (MCP + Ollama)

This project provides an automated Meeting Minutes Generator using a custom Model Context Protocol (MCP) server and Ollama. It leverages the Gemma 3 (4b) model to process transcripts and generate structured summaries, action items, and key decisions.

The architecture is fully containerized using Docker, featuring a Python-based FastMCP server and a local LLM instance.
## Architecture

The project consists of two core services:

    Ollama Service: Runs the local inference engine and automatically pulls the gemma3:4b model.

    MCP Service: A Python-based server built with FastMCP and managed by uv. It exposes tools to process text and communicate with the Ollama container.

## Getting Started
#### Prerequisites

    Docker and Docker Compose installed.

    (Optional) NVIDIA GPU drivers installed for hardware acceleration.

#### Installation & Setup

    Clone the repository:
    Bash

    git clone <your-repo-url>
    cd <project-folder>

    Start the services:
    This command builds the custom MCP image and starts both containers. The --build flag ensures your latest main.py changes are included.
    Bash

    docker-compose up --build

    Model Initialization:
    On the first run, the Ollama container will automatically download the gemma3:4b model via the entrypoint.sh script. You can monitor the progress with:
    Bash

    docker logs -f ollama-service

## Usage
#### MCP Connection

The MCP server runs over SSE (Server-Sent Events). By default, it is accessible at:
http://localhost:9000/sse
Available Tools

Once connected to a client (like Claude Desktop or MCP Inspector), you can use the following tools:

    generate_minutes: Pass a meeting transcript to receive a formatted summary, list of participants, and action items.

Running the Model Manually

If you want to interact with the model directly via the command line inside the container:
Bash

docker exec -it ollama-service ollama run gemma3:4b

## Configuration
#### Environment Variables

You can adjust these in the docker-compose.yml file:

    MCP_PORT: The internal/external port for the MCP server (default: 9000).

    OLLAMA_HOST: The internal network address for the Ollama service (http://ollama:11434).

#### File Structure

    src/: Contains the Python source code, Dockerfile, and uv lockfiles.

    ollama/: Contains the entrypoint.sh script to automate model pulling.

    docker-compose.yml: Defines the multi-container orchestration.
