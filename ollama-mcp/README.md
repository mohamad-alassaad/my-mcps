# ollama-mcp — Code Review MCP powered by Ollama

An MCP server that does **code-review work** and uses a **local Ollama model** as its reasoning engine. The client (e.g. Goose, Claude Desktop) calls normal MCP tools; the MCP translates them into structured prompts against Ollama and returns JSON.

Transport: **SSE** over HTTP, so any SSE-capable MCP client can connect.

## Tools

| Tool | Purpose | Returns |
|---|---|---|
| `review_code` | Review a snippet — severity, category, suggestion, score | `{summary, overall_score, issues[]}` |
| `suggest_refactor` | Refactor toward a goal (readability / perf / testability) | `{refactored_code, rationale, breaking_changes}` |
| `generate_commit_message` | Turn a `git diff` into a Conventional-Commits message | `{subject, body, type, scope}` |
| `explain_error` | Diagnose an error/stack trace + suggest a fix | `{probable_cause, suggested_fix, confidence, references}` |
| `generate_tests` | Produce unit tests (pytest by default) | `{test_code, framework, coverage_notes}` |
| `health` | Check Ollama connectivity + list installed models | `{ok, ollama_host, default_model, available_models}` |

Each tool uses Ollama's `/api/chat` with `format: json` so the model returns structured output directly.

---

## Run natively (Windows / macOS / Linux — no Docker required)

This is the recommended path, especially on machines without CPU virtualization enabled.

### 1. Install Ollama

- Windows / macOS: https://ollama.com/download
- Linux: `curl -fsSL https://ollama.com/install.sh | sh`

After install, Ollama listens on `http://localhost:11434`. Pull the default model:

```bash
ollama pull gemma3:4b
```

Any other chat model works too — `llama3.2:3b`, `qwen2.5:7b`, `phi4`, etc. Set `OLLAMA_MODEL` to switch.

### 2. Install Python deps

From this folder:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

If PowerShell blocks activation: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

### 3. Start the MCP server

**Windows**
```powershell
.\run.ps1
```

**macOS / Linux**
```bash
chmod +x run.sh
./run.sh
```

Or run directly:
```bash
python server.py
```

The SSE endpoint is then at `http://localhost:8081/sse`.

### 4. Register it with Goose

In your Goose extensions config (or through the UI):

```yaml
extensions:
  code-review-mcp:
    type: sse
    uri: http://localhost:8081/sse
```

### Architecture (native)

```
HOST MACHINE
├── Goose Desktop  ──(SSE)──▶  ollama-mcp :8081
└── ollama-mcp  ──(HTTP)──▶  Ollama :11434  (native service)
```

---

## Run with Docker (alternative)

Requires Docker Desktop + CPU virtualization (VT-x / AMD-V). Launches Ollama **and** the MCP together.

```bash
docker compose up --build
```

- Ollama API → `http://localhost:11434`
- MCP SSE    → `http://localhost:8081/sse`

The `ollama` container auto-pulls `gemma3:4b` on first start and persists it in the `ollama_data` volume.

---

## Configuration

All via environment variables:

| Var | Default | Notes |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | `http://ollama:11434` inside the compose network |
| `OLLAMA_MODEL` | `gemma3:4b` | Any chat model installed in Ollama |
| `OLLAMA_TIMEOUT` | `300` | Seconds per request |
| `MCP_HOST` | `0.0.0.0` | Bind address for the SSE server |
| `MCP_PORT` | `8081` | Port for the SSE server |

---

## Smoke test

With the server running and Ollama up:

```bash
curl http://localhost:8081/sse
```

You should see SSE headers / an open connection. Then from Goose (or any MCP client), list the tools — `health` is a safe first call to verify Ollama is reachable.

---

## Files

- `server.py` — FastMCP server, tool definitions, Ollama client
- `requirements.txt` — `mcp`, `requests`
- `run.ps1` / `run.sh` — native launcher with env defaults
- `Dockerfile` + `docker-compose.yml` + `ollama/` — optional Docker stack
