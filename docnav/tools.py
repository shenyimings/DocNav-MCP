"""MCP tools for document navigation with DocumentCompass integration."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import SearchResult, NavigationContext
from .navigator import DocumentNavigator, DocumentCompass


class DocNavTools:
    """MCP tools for document navigation using DocumentCompass engine.
    
    Provides high-level tools that integrate with MCP for document operations
    including loading, navigation, search, and content extraction.
    """
    
    def __init__(self) -> None:
        """Initialize the navigation tools."""
        self.navigator = DocumentNavigator()
    
    async def load_document(self, file_path: str) -> Dict[str, Any]:
        """Load a document for processing from file system.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Dictionary with success status and document info
        """
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}"}
        
        try:
            compass = await self.navigator.load_document_from_file(path)
            
            # Get document statistics
            headings = [
                node for node in compass.index.values() 
                if node.type == "heading"
            ]
            
            return {
                "success": True,
                "document": {
                    "id": str(path),
                    "name": path.name,
                    "format": compass.source_format,
                    "total_nodes": len(compass.index),
                    "headings_count": len(headings),
                    "file_path": str(path.resolve()),
                }
            }
        except Exception as e:
            return {"error": f"Failed to load document: {str(e)}"}
    
    async def load_document_text(
        self, 
        content: str, 
        doc_id: str, 
        format: str = "markdown"
    ) -> Dict[str, Any]:
        """Load document from text content.
        
        Args:
            content: Document text content
            doc_id: Document identifier
            format: Document format (markdown, xml)
            
        Returns:
            Dictionary with success status and document info
        """
        try:
            compass = await self.navigator.load_document_from_text(
                doc_id, content, format
            )
            
            headings = [
                node for node in compass.index.values() 
                if node.type == "heading"
            ]
            
            return {
                "success": True,
                "document": {
                    "id": doc_id,
                    "format": format,
                    "total_nodes": len(compass.index),
                    "headings_count": len(headings),
                    "content_length": len(content),
                }
            }
        except Exception as e:
            return {"error": f"Failed to load document: {str(e)}"}
    
    def get_outline(
        self, 
        doc_id: str, 
        max_depth: int = 3, 
        format: str = "text"
    ) -> Dict[str, Any]:
        """Get document outline/table of contents.
        
        Args:
            doc_id: Document identifier
            max_depth: Maximum heading depth to include
            format: Output format ('text' or 'structured')
            
        Returns:
            Dictionary with outline data
        """
        compass = self.navigator.get_document(doc_id)
        if not compass:
            return {"error": f"Document '{doc_id}' not found"}
        
        try:
            if format == "structured":
                # Return structured outline data
                outline_data = []
                
                def build_structured_outline(node, depth=0):
                    if depth > max_depth:
                        return
                    
                    if node.type == "heading" and node.level:
                        outline_data.append({
                            "id": node.id,
                            "title": node.title,
                            "level": node.level,
                            "depth": depth,
                            "line_number": node.attributes.get("line_number"),
                            "has_children": bool([
                                child for child in node.children 
                                if child.type == "heading"
                            ])
                        })
                    
                    for child in node.children:
                        build_structured_outline(
                            child, 
                            depth + 1 if node.type == "heading" else depth
                        )
                
                build_structured_outline(compass.root)
                
                return {
                    "success": True,
                    "outline": outline_data,
                    "total_sections": len(outline_data)
                }
            else:
                # Return formatted text outline
                outline_text = compass.get_outline(max_depth)
                return {
                    "success": True,
                    "outline": outline_text,
                    "format": "text"
                }
                
        except Exception as e:
            return {"error": f"Failed to get outline: {str(e)}"}
    
    def get_section(
        self, 
        doc_id: str, 
        section_id: str,
        include_subsections: bool = True
    ) -> Dict[str, Any]:
        """Get content of a specific section.
        
        Args:
            doc_id: Document identifier
            section_id: Section ID from outline
            include_subsections: Whether to include subsection content
            
        Returns:
            Dictionary with section data
        """
        compass = self.navigator.get_document(doc_id)
        if not compass:
            return {"error": f"Document '{doc_id}' not found"}
        
        try:
            node = compass.index.get(section_id)
            if not node:
                return {"error": f"Section '{section_id}' not found"}
            
            content = compass.get_section(section_id, include_subsections)
            
            # Get navigation context
            try:
                context = compass.get_navigation_context(section_id)
            except ValueError:
                context = None
            
            return {
                "success": True,
                "section": {
                    "id": node.id,
                    "title": node.title,
                    "type": node.type,
                    "level": node.level,
                    "content": content,
                    "line_number": node.attributes.get("line_number"),
                    "attributes": node.attributes,
                },
                "navigation": {
                    "parent": context.parent if context else None,
                    "siblings_count": len(context.siblings) if context else 0,
                    "children_count": len(context.children) if context else 0,
                    "breadcrumbs": context.breadcrumbs if context else [],
                }
            }
        except Exception as e:
            return {"error": f"Failed to get section: {str(e)}"}
    
    def search_document(
        self, 
        doc_id: str, 
        query: str, 
        max_results: int = 10
    ) -> Dict[str, Any]:
        """Search for content within a document.
        
        Args:
            doc_id: Document identifier
            query: Search term or phrase
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with search results
        """
        compass = self.navigator.get_document(doc_id)
        if not compass:
            return {"error": f"Document '{doc_id}' not found"}
        
        try:
            results = compass.search(query)
            
            if not results:
                return {
                    "success": True,
                    "results": [],
                    "total_results": 0,
                    "query": query
                }
            
            # Format results for return
            formatted_results = []
            for result in results[:max_results]:
                formatted_results.append({
                    "node_id": result.node_id,
                    "section_title": result.section,
                    "section_id": result.section_id,
                    "content": result.content,
                    "content_preview": result.content[:200] + "..." if len(result.content) > 200 else result.content,
                    "type": result.type,
                    "line_number": result.line_number,
                })
            
            return {
                "success": True,
                "results": formatted_results,
                "total_results": len(results),
                "returned_results": len(formatted_results),
                "query": query
            }
            
        except Exception as e:
            return {"error": f"Failed to search document: {str(e)}"}
    
    def navigate_section(self, doc_id: str, section_id: str) -> Dict[str, Any]:
        """Get navigation context for a section.
        
        Args:
            doc_id: Document identifier
            section_id: Section ID to navigate to
            
        Returns:
            Dictionary with navigation context
        """
        compass = self.navigator.get_document(doc_id)
        if not compass:
            return {"error": f"Document '{doc_id}' not found"}
        
        try:
            context = compass.get_navigation_context(section_id)
            
            return {
                "success": True,
                "navigation": {
                    "current": context.current,
                    "parent": context.parent,
                    "siblings": context.siblings,
                    "children": context.children,
                    "breadcrumbs": context.breadcrumbs,
                },
                "formatted_output": self.navigator.navigate(doc_id, section_id)
            }
            
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to navigate: {str(e)}"}
    
    def get_document_stats(self, doc_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics about a document.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Dictionary with document statistics
        """
        compass = self.navigator.get_document(doc_id)
        if not compass:
            return {"error": f"Document '{doc_id}' not found"}
        
        try:
            # Categorize nodes by type
            node_types = {}
            heading_levels = {}
            
            for node in compass.index.values():
                node_types[node.type] = node_types.get(node.type, 0) + 1
                
                if node.type == "heading" and node.level:
                    level_key = f"h{node.level}"
                    heading_levels[level_key] = heading_levels.get(level_key, 0) + 1
            
            # Calculate content statistics
            total_content_length = sum(
                len(node.content) for node in compass.index.values()
                if node.content
            )
            
            return {
                "success": True,
                "statistics": {
                    "document_id": doc_id,
                    "format": compass.source_format,
                    "total_nodes": len(compass.index),
                    "node_types": node_types,
                    "heading_levels": heading_levels,
                    "content_stats": {
                        "total_characters": len(compass.source_text),
                        "content_characters": total_content_length,
                        "total_lines": len(compass.source_text.split("\n")),
                    }
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to get statistics: {str(e)}"}
    
    def list_documents(self) -> Dict[str, Any]:
        """List all currently loaded documents.
        
        Returns:
            Dictionary with loaded documents information
        """
        if not self.navigator.loaded_documents:
            return {
                "success": True,
                "documents": [],
                "total_documents": 0
            }
        
        documents = []
        for doc_id, compass in self.navigator.loaded_documents.items():
            headings = [
                node for node in compass.index.values() 
                if node.type == "heading"
            ]
            
            documents.append({
                "id": doc_id,
                "format": compass.source_format,
                "total_nodes": len(compass.index),
                "headings_count": len(headings),
                "content_length": len(compass.source_text),
            })
        
        return {
            "success": True,
            "documents": documents,
            "total_documents": len(documents)
        }