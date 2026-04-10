from src.core.agents.orchestrator import Orchestrator

from fastmcp import FastMCP

mcp = FastMCP("CR MCP")

# @mcp.tool()
# async def upload_files(files: list[str]) -> dict:
#     """

#     """s
#     return []


@mcp.tool()
async def create_cr(content: str, files: list[str] = [], language: str = "fr") -> dict:
    """
    Professional meeting minutes generator.
    Transforms raw transcripts or shorthand notes into
    structured documentation including a summary, key
    discussion points, and a categorized list of action items with owners.

    Args:
        - content: transciption or notes of the meeting
        - language: language of the minuete agent
        - files: list of files (teams STT, email export ...) if provided. Can be paths or encoded base64
    """
    agent = Orchestrator()
    result = agent.run(texte=content, langue=language)
    return result
