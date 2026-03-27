# Setup script for my-mcps
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$mcpsRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = "$env:USERPROFILE\.config\goose\config.yaml"

Write-Host "Step 1: Creating Python virtual environment..." -ForegroundColor Cyan
Set-Location $mcpsRoot
python -m venv .venv
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to create venv"; exit 1 }

Write-Host "Step 2: Installing dependencies..." -ForegroundColor Cyan
& "$mcpsRoot\.venv\Scripts\pip.exe" install mcp
if ($LASTEXITCODE -ne 0) { Write-Error "pip install failed"; exit 1 }

Write-Host "Step 3: Registering MCPs in Goose config..." -ForegroundColor Cyan

# Create config dir if it doesn't exist
$configDir = Split-Path -Parent $configPath
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir | Out-Null
}

# Create config file if it doesn't exist
if (-not (Test-Path $configPath)) {
    New-Item -ItemType File -Path $configPath | Out-Null
}

$pythonPath = "$mcpsRoot\.venv\Scripts\python.exe"
$helloMcpPath = "$mcpsRoot\hello-mcp\hello_mcp.py"

$mcpEntry = @"

extensions:
  hello-mcp:
    name: hello-mcp
    type: stdio
    cmd: $pythonPath
    args:
      - $helloMcpPath
    enabled: true
"@

# Only add if not already present
$configContent = Get-Content $configPath -Raw -ErrorAction SilentlyContinue
if ($configContent -notmatch "hello-mcp") {
    Add-Content -Path $configPath -Value $mcpEntry
    Write-Host "hello-mcp added to Goose config." -ForegroundColor Green
} else {
    Write-Host "hello-mcp already in config, skipping." -ForegroundColor Yellow
}

Write-Host "Done! Restart Goose and enable hello-mcp from Extensions." -ForegroundColor Green
