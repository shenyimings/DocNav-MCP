"""Document navigation engine - DOM-like tree structure approach."""

import re
from pathlib import Path
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

from .models import Document, DocumentNode, NavigationContext, SearchResult


class DocumentCompass:
    """Document navigation engine using DOM-like tree structure.
    
    Core navigation engine that parses documents into hierarchical tree structures,
    enabling efficient navigation, content extraction, and search operations.
    """
    
    def __init__(self, source_text: str, source_format: str = "markdown") -> None:
        """Initialize document compass with source content.
        
        Args:
            source_text: Raw document content
            source_format: Document format (markdown, xml, etc.)
        """
        self.source_text = source_text
        self.source_format = source_format
        self.root = self._parse_document()
        self.index = self._build_index()
    
    def _parse_document(self) -> DocumentNode:
        """Parse document into tree structure based on format."""
        if self.source_format == "markdown":
            return self._parse_markdown()
        elif self.source_format == "xml":
            return self._parse_xml()
        else:
            raise ValueError(f"Unsupported format: {self.source_format}")
    
    def _parse_xml(self) -> DocumentNode:
        """Parse XML content into DOM tree structure."""
        root = DocumentNode(type="document", id="root")
        xml_root = ET.fromstring(self.source_text)
        
        def process_element(element: ET.Element, parent_node: DocumentNode) -> None:
            for child in element:
                node = DocumentNode(
                    type=child.tag,
                    id=child.get("id", f"xml_{len(parent_node.children)}"),
                    content=child.text if child.text else "",
                    attributes=dict(child.attrib),
                    parent=parent_node
                )
                parent_node.children.append(node)
                process_element(child, node)
        
        process_element(xml_root, root)
        return root
    
    def _parse_markdown(self) -> DocumentNode:
        """Parse Markdown content into DOM tree structure."""
        root = DocumentNode(type="document", id="root")
        lines = self.source_text.split("\n")
        
        current_parents = [root]  # Stack to track parent nodes
        node_counter = 0
        
        for line_num, line in enumerate(lines):
            # Parse headings
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                node_id = f"h{level}_{node_counter}"
                
                # Adjust parent stack based on heading level
                while len(current_parents) > level:
                    current_parents.pop()
                
                heading_node = DocumentNode(
                    type="heading",
                    level=level,
                    id=node_id,
                    title=title,
                    content=line,
                    attributes={"line_number": line_num},
                )
                
                current_parents[-1].children.append(heading_node)
                heading_node.parent = current_parents[-1]
                current_parents.append(heading_node)
                node_counter += 1
                continue
            
            # Parse paragraphs and other content
            if line.strip():
                para_node = DocumentNode(
                    type="paragraph",
                    id=f"p_{node_counter}",
                    content=line,
                    attributes={"line_number": line_num},
                )
                current_parents[-1].children.append(para_node)
                para_node.parent = current_parents[-1]
                node_counter += 1
        
        return root
    
    def _build_index(self) -> Dict[str, DocumentNode]:
        """Build node index for fast lookup - similar to getElementById."""
        index = {}
        
        def traverse(node: DocumentNode) -> None:
            if node.id:
                index[node.id] = node
            for child in node.children:
                traverse(child)
        
        traverse(self.root)
        return index
    
    def get_outline(self, max_depth: int = 3) -> str:
        """Get document outline as formatted string."""
        outline = []
        
        def build_outline(node: DocumentNode, depth: int = 0) -> None:
            if depth > max_depth:
                return
            
            if node.type == "heading":
                indent = "  " * (depth - 1) if depth > 0 else ""
                outline.append(f"{indent}- {node.title} (#{node.id})")
            
            for child in node.children:
                build_outline(
                    child, 
                    depth + 1 if node.type == "heading" else depth
                )
        
        build_outline(self.root)
        return "\n".join(outline)
    
    def get_section(self, node_id: str, include_subsections: bool = True) -> str:
        """Get content of specified node and optionally its subsections."""
        if node_id not in self.index:
            return f"Section '{node_id}' not found"
        
        node = self.index[node_id]
        content = [node.content] if node.content else []
        
        if include_subsections:
            def collect_content(n: DocumentNode) -> None:
                for child in n.children:
                    if child.content:
                        content.append(child.content)
                    if (child.type == "heading" and node.level and 
                        child.level and child.level > node.level):
                        content.append(child.content)
                    collect_content(child)
            
            collect_content(node)
        
        return "\n".join(content)
    
    def search(self, query: str, context_lines: int = 2) -> List[SearchResult]:
        """Search document content and return structured results."""
        results = []
        
        def search_node(node: DocumentNode) -> None:
            if query.lower() in node.content.lower():
                # Find nearest heading as context
                parent = node.parent
                while parent and parent.type != "heading":
                    parent = parent.parent
                
                section_title = parent.title if parent else "Document Root"
                
                results.append(SearchResult(
                    node_id=node.id,
                    section=section_title,
                    section_id=parent.id if parent else "root",
                    content=node.content,
                    type=node.type,
                    line_number=node.attributes.get("line_number")
                ))
            
            for child in node.children:
                search_node(child)
        
        search_node(self.root)
        return results
    
    def get_navigation_context(self, node_id: str) -> NavigationContext:
        """Get navigation context with parent, siblings, and children info."""
        if node_id not in self.index:
            raise ValueError("Node not found")
        
        node = self.index[node_id]
        parent = node.parent
        
        current_info = {"id": node.id, "title": node.title, "type": node.type}
        parent_info = None
        siblings = []
        children = []
        breadcrumbs = []
        
        if parent:
            parent_info = {"id": parent.id, "title": parent.title}
            
            # Get siblings (same-level headings)
            for sibling in parent.children:
                if sibling.type == "heading":
                    siblings.append({
                        "id": sibling.id,
                        "title": sibling.title,
                        "is_current": sibling.id == node.id,
                    })
        
        # Get children (direct child headings)
        for child in node.children:
            if child.type == "heading":
                children.append({"id": child.id, "title": child.title})
        
        # Build breadcrumbs
        ancestors = node.get_ancestors()
        for ancestor in ancestors:
            if ancestor.type == "heading":
                breadcrumbs.append({"id": ancestor.id, "title": ancestor.title})
        
        return NavigationContext(
            current=current_info,
            parent=parent_info,
            siblings=siblings,
            children=children,
            breadcrumbs=breadcrumbs
        )


class DocumentNavigator:
    """High-level document navigation interface.
    
    Provides a clean interface for document operations, managing multiple
    documents and coordinating with processors.
    """
    
    def __init__(self) -> None:
        """Initialize the document navigator."""
        self.loaded_documents: Dict[str, DocumentCompass] = {}
    
    async def load_document_from_text(
        self, 
        doc_id: str, 
        content: str, 
        format: str = "markdown"
    ) -> DocumentCompass:
        """Load document from text content."""
        try:
            compass = DocumentCompass(content, format)
            self.loaded_documents[doc_id] = compass
            return compass
        except Exception as e:
            raise ValueError(f"Error loading document: {str(e)}")
    
    async def load_document_from_file(self, file_path: Path) -> DocumentCompass:
        """Load document from file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine format from file extension
        format_map = {
            ".md": "markdown",
            ".markdown": "markdown",
            ".xml": "xml",
        }
        
        file_format = format_map.get(file_path.suffix.lower(), "markdown")
        
        try:
            content = file_path.read_text(encoding="utf-8")
            compass = DocumentCompass(content, file_format)
            self.loaded_documents[str(file_path)] = compass
            return compass
        except Exception as e:
            raise ValueError(f"Error loading document: {str(e)}")
    
    def get_document(self, doc_id: str) -> Optional[DocumentCompass]:
        """Get loaded document by ID."""
        return self.loaded_documents.get(doc_id)
    
    def get_outline(self, doc_id: str, max_depth: int = 3) -> str:
        """Get document outline."""
        if doc_id not in self.loaded_documents:
            return f"Document '{doc_id}' not found"
        return self.loaded_documents[doc_id].get_outline(max_depth)
    
    def read_section(self, doc_id: str, section_id: str) -> str:
        """Read specified section content."""
        if doc_id not in self.loaded_documents:
            return f"Document '{doc_id}' not found"
        return self.loaded_documents[doc_id].get_section(section_id)
    
    def search_document(self, doc_id: str, query: str) -> str:
        """Search document and return formatted results."""
        if doc_id not in self.loaded_documents:
            return f"Document '{doc_id}' not found"
        
        results = self.loaded_documents[doc_id].search(query)
        if not results:
            return f"No results found for '{query}'"
        
        output = f"Found {len(results)} results for '{query}':\n\n"
        for i, result in enumerate(results[:5], 1):  # Limit to first 5 results
            output += (
                f"{i}. In section '{result.section}' (#{result.section_id}):\n"
            )
            output += f"   {result.content[:100]}...\n\n"
        
        return output
    
    def navigate(self, doc_id: str, section_id: str) -> str:
        """Get navigation context as formatted string."""
        if doc_id not in self.loaded_documents:
            return f"Document '{doc_id}' not found"
        
        try:
            context = self.loaded_documents[doc_id].get_navigation_context(section_id)
        except ValueError as e:
            return str(e)
        
        output = f"Current: {context.current['title']}\n"
        
        if context.breadcrumbs:
            breadcrumb_path = " > ".join([b["title"] for b in context.breadcrumbs])
            output += f"Path: {breadcrumb_path} > {context.current['title']}\n"
        
        if context.parent:
            output += f"Parent: {context.parent['title']}\n"
        
        if context.siblings:
            output += "Siblings:\n"
            for sibling in context.siblings:
                marker = "→ " if sibling["is_current"] else "  "
                output += f"{marker}{sibling['title']} (#{sibling['id']})\n"
        
        if context.children:
            output += "Subsections:\n"
            for child in context.children:
                output += f"  {child['title']} (#{child['id']})\n"
        
        return output