# server.py
import os
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("DocNav MCP Server",instructions="Use this server to navigate and manage long-form documents.")


# Example of Add an tool
# @mcp.tool()
# def add(a: int, b: int) -> int:
#     """Add two numbers"""
#     return a + b


# Add a dynamic resource
@mcp.resource("document://{document_name}")
def get_document(document_name: str) -> str:
    """Get the full text of the document"""
    if not os.path.exists(document_name):
        return f"Document {document_name} not found."
    with open(document_name, "r", encoding="utf8") as file:
        content = file.read()
    return content
