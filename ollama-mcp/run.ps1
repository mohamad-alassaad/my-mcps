# Launch the Code Review MCP server against a local (native) Ollama install.
# Usage:   .\run.ps1
# Prereq:  Ollama for Windows running on http://localhost:11434 and the model pulled.

$ErrorActionPreference = "Stop"

$env:OLLAMA_HOST  = if ($env:OLLAMA_HOST)  { $env:OLLAMA_HOST }  else { "http://localhost:11434" }
$env:OLLAMA_MODEL = if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "gemma3:4b" }
$env:MCP_HOST     = if ($env:MCP_HOST)     { $env:MCP_HOST }     else { "0.0.0.0" }
$env:MCP_PORT     = if ($env:MCP_PORT)     { $env:MCP_PORT }     else { "8081" }

# Activate venv if present, otherwise assume deps are installed globally.
$venvActivate = Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    . $venvActivate
}

Write-Host "Ollama  : $($env:OLLAMA_HOST) (model: $($env:OLLAMA_MODEL))"
Write-Host "MCP SSE : http://localhost:$($env:MCP_PORT)/sse"
Write-Host ""

python "$PSScriptRoot\server.py"
