"""Main MCP server implementation for DocNav."""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from docnav.navigator import DocumentNavigator

# Create an MCP server
mcp = FastMCP(
    "DocNav MCP Server",
    instructions=(
        "Use this server to navigate and analyze long-form documents. "
        "Supports intelligent section-by-section reading, content search, "
        "outline generation, and hierarchical navigation. Documents are "
        "identified by auto-generated UUIDs for security."
    ),
)

# Initialize the document navigator
navigator = DocumentNavigator()


@mcp.tool()
def load_document(file_path: str) -> str:
    """Load a document for navigation and analysis.

    Args:
        file_path: Path to the document file

    Returns:
        Success message with auto-generated document ID
    """
    try:
        path = Path(file_path).resolve()
        if not path.exists():
            return f"Error: File not found: {file_path}"

        # Use the synchronous version to avoid event loop conflicts
        doc_id, document = navigator.load_document_from_file_sync(path)

        metadata = navigator.get_document_metadata(doc_id)
        return (
            f"Document loaded successfully!\n"
            f"File: {path.name}\n"
            f"Document ID: {doc_id}\n"
            f"Format: {metadata['format'] if metadata else 'unknown'}\n"
            f"Use get_outline('{doc_id}') to see document structure."
        )
    except Exception as e:
        return f"Error loading document: {str(e)}"


@mcp.tool()
def get_outline(doc_id: str, max_depth: int = 3) -> str:
    """Get document outline/table of contents.

    Tips: First use this tool to understand document structure after you load a document.

    Args:
        doc_id: Document identifier
        max_depth: Maximum heading depth to include, defaults to 3

    Returns:
        Formatted document outline
    """
    return navigator.get_outline(doc_id, max_depth)


@mcp.tool()
def read_section(doc_id: str, section_id: str) -> str:
    """Read content of a specific document section.

    Args:
        doc_id: Document identifier
        section_id: Section ID from outline (e.g., 'h1_0', 'h2_1')

    Returns:
        Section content with subsections
    """

    return navigator.read_section(doc_id, section_id.strip("#"))


@mcp.tool()
def search_document(doc_id: str, query: str) -> str:
    """Search for specific content within a document.

    Args:
        doc_id: Document identifier
        query: Search term or phrase

    Returns:
        Formatted search results with context
    """
    return navigator.search_document(doc_id, query)


@mcp.tool()
def navigate_section(doc_id: str, section_id: str) -> str:
    """Get navigation context for a section (parent, siblings, children).

    Args:
        doc_id: Document identifier
        section_id: Section ID to navigate to

    Returns:
        Navigation context with related sections
    """
    return navigator.navigate(doc_id, section_id.strip("#"))


@mcp.tool()
def list_documents() -> str:
    """List all currently loaded documents.

    Returns:
        List of loaded documents with their metadata
    """
    documents = navigator.list_documents()
    if not documents:
        return "No documents currently loaded."

    output = "Loaded documents:\n"
    for doc in documents:
        document = navigator.get_document(doc["id"])
        headings_count = 0
        if document and document.index:
            headings = [
                node for node in document.index.values() if node.type == "heading"
            ]
            headings_count = len(headings)

        output += (
            f"- {doc['title']} (ID: {doc['id']})\n"
            f"  Format: {doc['format']}, Sections: {headings_count}\n"
            f"  Source: {doc['source_type']}\n\n"
        )

    return output


@mcp.tool()
def get_document_stats(doc_id: str) -> str:
    """Get statistics about a loaded document.

    Args:
        doc_id: Document identifier

    Returns:
        Document statistics and structure info
    """
    document = navigator.get_document(doc_id)
    if not document:
        return f"Document '{doc_id}' not found"

    headings = []
    paragraphs = []
    if document.index:
        headings = [node for node in document.index.values() if node.type == "heading"]
        paragraphs = [
            node for node in document.index.values() if node.type == "paragraph"
        ]

    stats = f"Document: {doc_id}\n"
    stats += f"Total nodes: {len(document.index) if document.index else 0}\n"
    stats += f"Headings: {len(headings)}\n"
    stats += f"Paragraphs: {len(paragraphs)}\n"

    # Token statistics
    token_stats = navigator.get_document_tokens(doc_id)
    if token_stats:
        stats += f"Total tokens: {token_stats['total_tokens']}\n"
        # stats += f"Content tokens: {token_stats['content_tokens']}\n"

    # Heading level breakdown
    level_counts = {}
    for heading in headings:
        level = heading.level or 0
        level_counts[level] = level_counts.get(level, 0) + 1

    if level_counts:
        stats += "Heading levels:\n"
        for level in sorted(level_counts.keys()):
            stats += f"  H{level}: {level_counts[level]}\n"

    return stats


@mcp.tool()
def remove_document(doc_id: str) -> str:
    """Remove a document from the navigator.

    Args:
        doc_id: Document identifier (UUID)

    Returns:
        Success or error message
    """
    success = navigator.remove_document(doc_id)
    if success:
        return f"Document '{doc_id}' removed successfully"
    else:
        return f"Document '{doc_id}' not found or could not be removed"


# For direct execution
if __name__ == "__main__":
    mcp.run()
