# /// script
# dependencies = [
#   "fastmcp",
#   "requests",
# ]
# ///

from src.core.mcp_tools import mcp
from dotenv import load_dotenv
import os

if __name__ == "__main__":
    load_dotenv()
    # mcp.run()
    mcp_port = int(os.getenv("MCP_PORT", 9000))
    mcp.run(transport="http", host="0.0.0.0", port=mcp_port)
