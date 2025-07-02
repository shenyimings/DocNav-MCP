"""Data models for document representation based on DOM-like tree structure."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DocumentNode:
    """Document node - similar to DOM node structure.
    
    Represents a hierarchical element in a document tree structure,
    supporting various content types like headings, paragraphs, lists, etc.
    """
    
    type: str  # node type: heading, paragraph, list, code, etc.
    level: Optional[int] = None  # hierarchy level for headings
    id: str = ""
    title: str = ""  # display title for headings
    content: str = ""  # actual text content
    attributes: Dict[str, Any] = field(default_factory=dict)  # additional metadata
    children: List["DocumentNode"] = field(default_factory=list)  # child nodes
    parent: Optional["DocumentNode"] = None  # parent node reference
    
    def __post_init__(self) -> None:
        """Initialize default values after dataclass creation."""
        if self.attributes is None:
            self.attributes = {}
        if self.children is None:
            self.children = []
    
    def add_child(self, child: "DocumentNode") -> None:
        """Add a child node and set parent reference."""
        child.parent = self
        self.children.append(child)
    
    def get_ancestors(self) -> List["DocumentNode"]:
        """Get list of ancestor nodes from root to parent."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors
    
    def get_depth(self) -> int:
        """Get the depth of this node in the tree."""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth


@dataclass
class SearchResult:
    """Represents a search result within a document."""
    
    node_id: str
    section: str  # section title where match was found
    section_id: str  # section node ID
    content: str  # matching content
    type: str  # node type
    line_number: Optional[int] = None
    context_before: str = ""
    context_after: str = ""


@dataclass
class NavigationContext:
    """Navigation context for a specific document node."""
    
    current: Dict[str, str]  # current node info
    parent: Optional[Dict[str, str]] = None  # parent node info
    siblings: List[Dict[str, Any]] = field(default_factory=list)  # sibling nodes
    children: List[Dict[str, str]] = field(default_factory=list)  # child nodes
    breadcrumbs: List[Dict[str, str]] = field(default_factory=list)  # ancestor path


@dataclass
class Document:
    """Represents a processed document with hierarchical structure.
    
    Uses a tree-based approach for better navigation and content organization,
    similar to DOM structure for web documents.
    """
    
    file_path: Path
    title: str
    source_text: str  # original document content
    source_format: str = "markdown"  # document format
    root: Optional[DocumentNode] = None  # document root node
    index: Dict[str, DocumentNode] = field(default_factory=dict)  # node lookup index
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Initialize document structure after creation."""
        if self.metadata is None:
            self.metadata = {}
        if self.root is None:
            self.root = DocumentNode(type="document", id="root", title=self.title)
        if not self.index:
            self.rebuild_index()
    
    def rebuild_index(self) -> None:
        """Rebuild the node lookup index."""
        self.index.clear()
        if self.root:
            self._traverse_and_index(self.root)
    
    def _traverse_and_index(self, node: DocumentNode) -> None:
        """Recursively traverse and index all nodes."""
        if node.id:
            self.index[node.id] = node
        for child in node.children:
            self._traverse_and_index(child)
    
    def get_node(self, node_id: str) -> Optional[DocumentNode]:
        """Get a node by ID using the index."""
        return self.index.get(node_id)
    
    def get_nodes_by_type(self, node_type: str) -> List[DocumentNode]:
        """Get all nodes of a specific type."""
        return [node for node in self.index.values() if node.type == node_type]
    
    def get_headings(self, max_level: Optional[int] = None) -> List[DocumentNode]:
        """Get all heading nodes, optionally filtered by maximum level."""
        headings = [node for node in self.index.values() if node.type == "heading"]
        if max_level is not None:
            headings = [h for h in headings if h.level and h.level <= max_level]
        return sorted(headings, key=lambda h: (h.level or 0, h.id))
    
    def get_outline(self, max_depth: int = 3) -> List[Dict[str, Any]]:
        """Get document outline as a structured list."""
        outline = []
        
        def build_outline(node: DocumentNode, depth: int = 0) -> None:
            if depth > max_depth:
                return
            
            if node.type == "heading" and node.level:
                outline.append({
                    "id": node.id,
                    "title": node.title,
                    "level": node.level,
                    "depth": depth,
                    "has_children": bool([
                        child for child in node.children 
                        if child.type == "heading"
                    ])
                })
            
            for child in node.children:
                build_outline(
                    child, 
                    depth + 1 if node.type == "heading" else depth
                )
        
        if self.root:
            build_outline(self.root)
        return outline