"""
Code Review MCP (SSE transport)

An MCP server that provides code-review tooling. Each tool does a specific
job (review, refactor, commit-message, error-explain) and uses a local
Ollama model internally as its reasoning engine.

The client (e.g. Goose) may have its own chat LLM; this MCP offloads
specialized, structured tasks to a local model via Ollama.
"""
import json
import os
import re
import requests
from mcp.server.fastmcp import FastMCP

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")
REQUEST_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))

mcp = FastMCP("code-review-mcp")


def _chat(system: str, user: str, model: str | None = None, json_mode: bool = False) -> str:
    """Send a single-turn chat to Ollama and return the assistant text."""
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
    }
    if json_mode:
        payload["format"] = "json"
    r = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json().get("message", {}).get("content", "").strip()


def _parse_json(text: str) -> dict | list:
    """Parse JSON from a model reply, tolerating code fences / prose."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return {"raw": text, "error": "failed to parse JSON from model output"}


# --------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------

@mcp.tool()
def review_code(code: str, language: str = "auto", focus: str = "general") -> dict:
    """
    Review a snippet of code and return structured findings.

    Args:
        code: Source code to review.
        language: Language hint (e.g. "python", "typescript"), or "auto".
        focus: Focus area - "general", "security", "performance", "style".

    Returns a dict with: summary, issues[{severity, line, category, message,
    suggestion}], overall_score (1-10).
    """
    system = (
        "You are a senior code reviewer. Reply with JSON only, matching this "
        "schema: {\"summary\": string, \"overall_score\": number (1-10), "
        "\"issues\": [{\"severity\": \"low|medium|high|critical\", "
        "\"line\": number|null, \"category\": string, \"message\": string, "
        "\"suggestion\": string}]}. Do not add prose outside the JSON."
    )
    user = (
        f"Review focus: {focus}\nLanguage: {language}\n\n"
        f"Code:\n```\n{code}\n```"
    )
    return _parse_json(_chat(system, user, json_mode=True))


@mcp.tool()
def suggest_refactor(code: str, language: str = "auto", goal: str = "readability") -> dict:
    """
    Suggest a refactor of the given code.

    Args:
        code: Source code to refactor.
        language: Language hint, or "auto".
        goal: "readability", "performance", "testability", or a free-form goal.

    Returns a dict with: refactored_code, rationale, breaking_changes (bool).
    """
    system = (
        "You are a senior engineer. Reply with JSON only, matching this schema: "
        "{\"refactored_code\": string, \"rationale\": string, "
        "\"breaking_changes\": boolean}. Preserve behavior unless the goal "
        "requires a behavior change; if it does, set breaking_changes=true "
        "and explain in rationale."
    )
    user = (
        f"Refactor goal: {goal}\nLanguage: {language}\n\n"
        f"Code:\n```\n{code}\n```"
    )
    return _parse_json(_chat(system, user, json_mode=True))


@mcp.tool()
def generate_commit_message(diff: str, style: str = "conventional") -> dict:
    """
    Produce a commit message for a git diff.

    Args:
        diff: Output of `git diff` (staged or unstaged).
        style: "conventional" (default) or "plain".

    Returns a dict with: subject, body, type (feat/fix/chore/...), scope.
    """
    system = (
        "You generate concise git commit messages. Reply with JSON only: "
        "{\"subject\": string (<=72 chars), \"body\": string, "
        "\"type\": string, \"scope\": string|null}. "
        "If style is 'conventional', subject must be 'type(scope): summary'."
    )
    user = f"Style: {style}\n\nDiff:\n```diff\n{diff}\n```"
    return _parse_json(_chat(system, user, json_mode=True))


@mcp.tool()
def explain_error(error_message: str, code_context: str = "") -> dict:
    """
    Explain an error/stack trace and suggest a fix.

    Returns: probable_cause, suggested_fix, confidence (0-1), references (list).
    """
    system = (
        "You are a debugging expert. Reply with JSON only: "
        "{\"probable_cause\": string, \"suggested_fix\": string, "
        "\"confidence\": number (0-1), \"references\": [string]}."
    )
    user = (
        f"Error:\n{error_message}\n\n"
        f"Code context (may be empty):\n```\n{code_context}\n```"
    )
    return _parse_json(_chat(system, user, json_mode=True))


@mcp.tool()
def generate_tests(code: str, framework: str = "pytest") -> dict:
    """
    Generate unit tests for a function/module.

    Returns: test_code, framework, coverage_notes.
    """
    system = (
        "You write clear, idiomatic unit tests. Reply with JSON only: "
        "{\"test_code\": string, \"framework\": string, "
        "\"coverage_notes\": string}."
    )
    user = f"Framework: {framework}\n\nCode under test:\n```\n{code}\n```"
    return _parse_json(_chat(system, user, json_mode=True))


@mcp.tool()
def health() -> dict:
    """Check Ollama connectivity and report the active model."""
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        return {
            "ollama_host": OLLAMA_HOST,
            "default_model": DEFAULT_MODEL,
            "available_models": models,
            "ok": True,
        }
    except Exception as e:
        return {"ollama_host": OLLAMA_HOST, "ok": False, "error": str(e)}


if __name__ == "__main__":
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8081"))
    mcp.settings.host = host
    mcp.settings.port = port
    # SSE transport so Goose / other clients can connect over HTTP
    mcp.run(transport="sse")
