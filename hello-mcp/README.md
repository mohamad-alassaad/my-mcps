# Hello MCP

A simple MCP server to test that Goose MCP integration is working correctly.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `say_hello` | Returns a greeting message | `name` (string) |
| `add_numbers` | Adds two numbers together | `a` (int), `b` (int) |

## Setup

### 1. Create the Python virtual environment

From the `my-mcps` root folder:

```powershell
cd C:\path\to\my-mcps
python -m venv .venv
.venv\Scripts\activate
pip install mcp
```

### 2. Register in Goose

Add this to `C:\Users\<your-username>\.config\goose\config.yaml`:

```yaml
extensions:
  hello-mcp:
    name: hello-mcp
    type: stdio
    cmd: C:\path\to\my-mcps\.venv\Scripts\python.exe
    args:
      - C:\path\to\my-mcps\hello-mcp\hello_mcp.py
    enabled: true
```

### 3. Restart Goose

The `hello-mcp` extension will appear under **Extensions** in the sidebar. Toggle it on.

## Test it

In Goose chat, try:
- `say hello to John`
- `add 5 and 3`
