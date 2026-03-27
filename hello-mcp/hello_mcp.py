from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hello")

@mcp.tool()
def say_hello(name: str) -> str:
    """Say hello to someone"""
    return f"Hello {name}, MCP is working!"

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b

if __name__ == "__main__":
    mcp.run()
