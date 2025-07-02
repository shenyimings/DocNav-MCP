"""Main MCP server implementation for DocNav."""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from mcp.server.fastmcp import FastMCP
from mcp.types import Resource, Tool

from .navigator import DocumentNavigator


class DocNavMCPServer:
    """DocNav MCP Server with comprehensive document navigation capabilities.
    
    Provides MCP tools for intelligent document navigation, content extraction,
    search, and structural analysis using DOM-like tree parsing approach.
    """
    
    def __init__(self, name: str = "DocNav MCP Server") -> None:
        """Initialize DocNav MCP server.
        
        Args:
            name: Server name for MCP identification
        """
        self.mcp = FastMCP(
            name,
            instructions=(
                "Use this server to navigate and analyze long-form documents. "
                "Supports intelligent section-by-section reading, content search, "
                "outline generation, and hierarchical navigation."
            )
        )
        self.navigator = DocumentNavigator()
        self._setup_tools()
        self._setup_resources()
    
    def _setup_tools(self) -> None:
        """Setup MCP tools for document operations."""
        
        @self.mcp.tool()
        def load_document(file_path: str, doc_id: Optional[str] = None) -> str:
            """Load a document for navigation and analysis.
            
            Args:
                file_path: Path to the document file
                doc_id: Optional custom document ID (defaults to file_path)
            
            Returns:
                Success message with document info
            """
            try:
                path = Path(file_path).resolve()
                if not path.exists():
                    return f"Error: File not found: {file_path}"
                
                asyncio.create_task(self._load_document_async(path, doc_id))
                
                return (
                    f"Document loaded successfully: {path.name}\n"
                    f"ID: {doc_id or str(path)}\n"
                    f"Use get_outline to see document structure."
                )
            except Exception as e:
                return f"Error loading document: {str(e)}"
        
        @self.mcp.tool()
        def load_document_text(
            content: str, 
            doc_id: str, 
            format: str = "markdown"
        ) -> str:
            """Load document from text content.
            
            Args:
                content: Document text content
                doc_id: Document identifier
                format: Document format (markdown, xml)
            
            Returns:
                Success message with document info
            """
            try:
                asyncio.create_task(
                    self.navigator.load_document_from_text(doc_id, content, format)
                )
                return (
                    f"Document '{doc_id}' loaded from text content.\n"
                    f"Format: {format}\n"
                    f"Use get_outline('{doc_id}') to see structure."
                )
            except Exception as e:
                return f"Error loading document: {str(e)}"
        
        @self.mcp.tool()
        def get_outline(doc_id: str, max_depth: int = 3) -> str:
            """Get document outline/table of contents.
            
            Args:
                doc_id: Document identifier
                max_depth: Maximum heading depth to include
            
            Returns:
                Formatted document outline
            """
            return self.navigator.get_outline(doc_id, max_depth)
        
        @self.mcp.tool()
        def read_section(doc_id: str, section_id: str) -> str:
            """Read content of a specific document section.
            
            Args:
                doc_id: Document identifier
                section_id: Section ID from outline (e.g., 'h1_0', 'h2_1')
            
            Returns:
                Section content with subsections
            """
            return self.navigator.read_section(doc_id, section_id)
        
        @self.mcp.tool()
        def search_document(doc_id: str, query: str) -> str:
            """Search for specific content within a document.
            
            Args:
                doc_id: Document identifier
                query: Search term or phrase
            
            Returns:
                Formatted search results with context
            """
            return self.navigator.search_document(doc_id, query)
        
        @self.mcp.tool()
        def navigate_section(doc_id: str, section_id: str) -> str:
            """Get navigation context for a section (parent, siblings, children).
            
            Args:
                doc_id: Document identifier
                section_id: Section ID to navigate to
            
            Returns:
                Navigation context with related sections
            """
            return self.navigator.navigate(doc_id, section_id)
        
        @self.mcp.tool()
        def list_documents() -> str:
            """List all currently loaded documents.
            
            Returns:
                List of loaded document IDs
            """
            if not self.navigator.loaded_documents:
                return "No documents currently loaded."
            
            output = "Loaded documents:\n"
            for doc_id, compass in self.navigator.loaded_documents.items():
                headings = [
                    node for node in compass.index.values() 
                    if node.type == "heading"
                ]
                output += f"- {doc_id} ({len(headings)} sections)\n"
            
            return output
        
        @self.mcp.tool()
        def get_document_stats(doc_id: str) -> str:
            """Get statistics about a loaded document.
            
            Args:
                doc_id: Document identifier
            
            Returns:
                Document statistics and structure info
            """
            compass = self.navigator.get_document(doc_id)
            if not compass:
                return f"Document '{doc_id}' not found"
            
            headings = [
                node for node in compass.index.values() 
                if node.type == "heading"
            ]
            paragraphs = [
                node for node in compass.index.values() 
                if node.type == "paragraph"
            ]
            
            stats = f"Document: {doc_id}\n"
            stats += f"Total nodes: {len(compass.index)}\n"
            stats += f"Headings: {len(headings)}\n"
            stats += f"Paragraphs: {len(paragraphs)}\n"
            
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
    
    def _setup_resources(self) -> None:
        """Setup MCP resources for document access."""
        
        @self.mcp.resource("document://{doc_id}")
        def get_document_resource(doc_id: str) -> str:
            """Get full document content as a resource.
            
            Args:
                doc_id: Document identifier
            
            Returns:
                Full document content
            """
            compass = self.navigator.get_document(doc_id)
            if not compass:
                return f"Document '{doc_id}' not found"
            
            return compass.source_text
        
        @self.mcp.resource("document://{doc_id}/outline")
        def get_outline_resource(doc_id: str) -> str:
            """Get document outline as a resource.
            
            Args:
                doc_id: Document identifier
            
            Returns:
                Document outline
            """
            return self.navigator.get_outline(doc_id)
        
        @self.mcp.resource("document://{doc_id}/section/{section_id}")
        def get_section_resource(doc_id: str, section_id: str) -> str:
            """Get specific section content as a resource.
            
            Args:
                doc_id: Document identifier
                section_id: Section ID
            
            Returns:
                Section content
            """
            return self.navigator.read_section(doc_id, section_id)
    
    async def _load_document_async(
        self, 
        file_path: Path, 
        doc_id: Optional[str] = None
    ) -> None:
        """Async helper for loading documents."""
        try:
            await self.navigator.load_document_from_file(file_path)
            if doc_id and doc_id != str(file_path):
                # Create alias for custom doc_id
                compass = self.navigator.loaded_documents[str(file_path)]
                self.navigator.loaded_documents[doc_id] = compass
        except Exception as e:
            # Error handling is done in the calling tool
            pass
    
    def run(self) -> None:
        """Run the MCP server."""
        self.mcp.run()


# Create and configure the server instance
def create_server() -> DocNavMCPServer:
    """Create and configure DocNav MCP server instance."""
    return DocNavMCPServer()


# For direct execution
if __name__ == "__main__":
    server = create_server()
    server.run()