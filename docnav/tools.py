"""MCP tools for document navigation."""

from pathlib import Path
from typing import Any, Dict, List

from .navigator import DocumentNavigator


class DocNavTools:
    """MCP tools for document navigation."""
    
    def __init__(self) -> None:
        """Initialize the tools."""
        self.navigator = DocumentNavigator()
    
    async def load_document(self, file_path: str) -> Dict[str, Any]:
        """Load a document for processing."""
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}"}
        
        try:
            document = await self.navigator.load_document(path)
            return {
                "success": True,
                "title": document.title,
                "sections_count": len(document.sections),
                "file_path": str(document.file_path),
            }
        except Exception as e:
            return {"error": f"Failed to load document: {str(e)}"}
    
    async def get_outline(self, file_path: str) -> Dict[str, Any]:
        """Get document outline/table of contents."""
        path = Path(file_path)
        try:
            sections = await self.navigator.get_document_outline(path)
            outline = []
            for section in sections:
                outline.append({
                    "id": section.id,
                    "title": section.title,
                    "level": section.level,
                    "parent_id": section.parent_id,
                })
            return {"success": True, "outline": outline}
        except Exception as e:
            return {"error": f"Failed to get outline: {str(e)}"}
    
    async def get_section(self, file_path: str, section_id: str) -> Dict[str, Any]:
        """Get content of a specific section."""
        path = Path(file_path)
        try:
            section = await self.navigator.get_section_content(path, section_id)
            if section is None:
                return {"error": f"Section not found: {section_id}"}
            
            return {
                "success": True,
                "section": {
                    "id": section.id,
                    "title": section.title,
                    "content": section.content,
                    "level": section.level,
                    "start_line": section.start_line,
                    "end_line": section.end_line,
                },
            }
        except Exception as e:
            return {"error": f"Failed to get section: {str(e)}"}
    
    async def search_document(self, file_path: str, query: str) -> Dict[str, Any]:
        """Search for content within a document."""
        path = Path(file_path)
        try:
            results = await self.navigator.search_document(path, query)
            search_results = []
            for section in results:
                search_results.append({
                    "id": section.id,
                    "title": section.title,
                    "content": section.content,
                    "level": section.level,
                })
            return {"success": True, "results": search_results}
        except Exception as e:
            return {"error": f"Failed to search document: {str(e)}"}