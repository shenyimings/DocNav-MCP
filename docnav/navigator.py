"""Document navigation engine - DOM-like tree structure approach."""

import re
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

import tiktoken
from markdown_it import MarkdownIt
from markdown_it.token import Token

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
                    parent=parent_node,
                )
                parent_node.children.append(node)
                process_element(child, node)

        process_element(xml_root, root)
        return root

    def _parse_markdown(self) -> DocumentNode:
        """Parse Markdown content into DOM tree structure using markdown-it-py."""
        root = DocumentNode(type="document", id="root")

        # Initialize markdown parser with CommonMark compatibility
        md = MarkdownIt("commonmark")
        tokens = md.parse(self.source_text)

        current_parents = [root]  # Stack to track parent nodes
        node_counter = 0

        for token in tokens:
            if token.type == "heading_open":
                level = int(token.tag[1])  # Extract level from h1, h2, etc.
                node_id = f"h{level}_{node_counter}"

                # Adjust parent stack based on heading level
                while len(current_parents) > level:
                    current_parents.pop()

                # Create heading node - content will be added by heading_close
                heading_node = DocumentNode(
                    type="heading",
                    level=level,
                    id=node_id,
                    title="",  # Will be filled by inline content
                    content="",
                    attributes={
                        "line_number": token.map[0] if token.map else None,
                        "tag": token.tag,
                    },
                )

                current_parents[-1].children.append(heading_node)
                heading_node.parent = current_parents[-1]
                current_parents.append(heading_node)
                node_counter += 1

            elif token.type == "heading_close":
                # The heading content should already be processed by inline tokens
                pass

            elif token.type == "paragraph_open":
                # Create paragraph node
                para_node = DocumentNode(
                    type="paragraph",
                    id=f"p_{node_counter}",
                    content="",  # Will be filled by inline content
                    attributes={
                        "line_number": token.map[0] if token.map else None,
                    },
                )
                current_parents[-1].children.append(para_node)
                para_node.parent = current_parents[-1]
                current_parents.append(para_node)
                node_counter += 1

            elif token.type == "paragraph_close":
                # Pop paragraph from stack
                if len(current_parents) > 1 and current_parents[-1].type == "paragraph":
                    current_parents.pop()

            elif token.type == "inline":
                # Add inline content to current parent
                if current_parents and token.content:
                    current_node = current_parents[-1]
                    if current_node.content:
                        current_node.content += " " + token.content
                    else:
                        current_node.content = token.content

                    # For headings, also set the title
                    if current_node.type == "heading":
                        current_node.title = token.content

            elif token.type == "list_item_open":
                # Create list item node
                item_node = DocumentNode(
                    type="list_item",
                    id=f"li_{node_counter}",
                    content="",
                    attributes={
                        "line_number": token.map[0] if token.map else None,
                    },
                )
                current_parents[-1].children.append(item_node)
                item_node.parent = current_parents[-1]
                current_parents.append(item_node)
                node_counter += 1

            elif token.type == "list_item_close":
                # Pop list item from stack
                if len(current_parents) > 1 and current_parents[-1].type == "list_item":
                    current_parents.pop()

            elif token.type == "bullet_list_open" or token.type == "ordered_list_open":
                # Create list node
                list_node = DocumentNode(
                    type="list",
                    id=f"list_{node_counter}",
                    content="",
                    attributes={
                        "list_type": (
                            "bullet" if token.type == "bullet_list_open" else "ordered"
                        ),
                        "line_number": token.map[0] if token.map else None,
                    },
                )
                current_parents[-1].children.append(list_node)
                list_node.parent = current_parents[-1]
                current_parents.append(list_node)
                node_counter += 1

            elif (
                token.type == "bullet_list_close" or token.type == "ordered_list_close"
            ):
                # Pop list from stack
                if len(current_parents) > 1 and current_parents[-1].type == "list":
                    current_parents.pop()

            elif token.type == "code_block" or token.type == "fence":
                # Create code block node
                code_node = DocumentNode(
                    type="code_block",
                    id=f"code_{node_counter}",
                    content=token.content,
                    attributes={
                        "line_number": token.map[0] if token.map else None,
                        "language": (
                            getattr(token, "info", "").strip()
                            if hasattr(token, "info")
                            else ""
                        ),
                    },
                )
                current_parents[-1].children.append(code_node)
                code_node.parent = current_parents[-1]
                node_counter += 1

            elif token.type == "blockquote_open":
                # Create blockquote node
                quote_node = DocumentNode(
                    type="blockquote",
                    id=f"quote_{node_counter}",
                    content="",
                    attributes={
                        "line_number": token.map[0] if token.map else None,
                    },
                )
                current_parents[-1].children.append(quote_node)
                quote_node.parent = current_parents[-1]
                current_parents.append(quote_node)
                node_counter += 1

            elif token.type == "blockquote_close":
                # Pop blockquote from stack
                if (
                    len(current_parents) > 1
                    and current_parents[-1].type == "blockquote"
                ):
                    current_parents.pop()

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
                outline.append(f"{indent}#{node.id} - {node.title}")

            for child in node.children:
                build_outline(child, depth + 1 if node.type == "heading" else depth)

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
                    if (
                        child.type == "heading"
                        and node.level
                        and child.level
                        and child.level > node.level
                    ):
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

                results.append(
                    SearchResult(
                        node_id=node.id,
                        section=section_title,
                        section_id=parent.id if parent else "root",
                        content=node.content,
                        type=node.type,
                        line_number=node.attributes.get("line_number"),
                    )
                )

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
                    siblings.append(
                        {
                            "id": sibling.id,
                            "title": sibling.title,
                            "is_current": sibling.id == node.id,
                        }
                    )

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
            breadcrumbs=breadcrumbs,
        )

    def get_total_tokens(self, encoding_name: str = "cl100k_base") -> int:
        """Calculate total token count for the document.

        Args:
            encoding_name: The tokenizer encoding to use (default: cl100k_base for GPT-4)

        Returns:
            Total number of tokens in the document
        """
        try:
            encoding = tiktoken.get_encoding(encoding_name)
            return len(encoding.encode(self.source_text))
        except Exception:
            # Fallback to simple word-based estimation if tiktoken fails
            # Rough approximation: 1 token ≈ 0.75 words
            words = len(self.source_text.split())
            return int(words / 0.75)

    def get_content_tokens(self, encoding_name: str = "cl100k_base") -> int:
        """Calculate token count for structured content only (excluding markup).

        Args:
            encoding_name: The tokenizer encoding to use

        Returns:
            Token count for content text only
        """
        try:
            encoding = tiktoken.get_encoding(encoding_name)

            # Collect all text content from nodes
            content_parts = []

            def collect_text_content(node: DocumentNode) -> None:
                if node.content and node.content.strip():
                    content_parts.append(node.content.strip())
                if hasattr(node, "title") and node.title and node.title.strip():
                    content_parts.append(node.title.strip())
                for child in node.children:
                    collect_text_content(child)

            collect_text_content(self.root)
            content_text = " ".join(content_parts)

            return len(encoding.encode(content_text))
        except Exception:
            # Fallback estimation
            content_parts = []

            def collect_text_content_fallback(node: DocumentNode) -> None:
                if node.content and node.content.strip():
                    content_parts.append(node.content.strip())
                if hasattr(node, "title") and node.title and node.title.strip():
                    content_parts.append(node.title.strip())
                for child in node.children:
                    collect_text_content_fallback(child)

            collect_text_content_fallback(self.root)
            content_text = " ".join(content_parts)
            words = len(content_text.split())
            return int(words / 0.75)


class DocumentNavigator:
    """High-level document navigation interface.

    Provides a clean interface for document operations, managing multiple
    documents and coordinating with processors. Uses UUID-based document IDs
    for security and uniqueness.
    """

    def __init__(self) -> None:
        """Initialize the document navigator."""
        self.loaded_documents: Dict[str, DocumentCompass] = {}
        self.document_metadata: Dict[str, Dict[str, str]] = (
            {}
        )  # Store metadata by doc_id

    def _generate_doc_id(self) -> str:
        """Generate a unique document ID using UUID."""
        return str(uuid.uuid4())

    def _normalize_file_path(self, file_path: Path) -> str:
        """Normalize file path to prevent path injection and ensure consistency."""
        try:
            # Resolve to absolute path to handle relative paths consistently
            normalized = file_path.resolve()
            return str(normalized)
        except (OSError, ValueError) as e:
            raise ValueError(f"Invalid file path: {e}")

    def load_document_from_text_sync(
        self, content: str, format: str = "markdown", title: Optional[str] = None
    ) -> Tuple[str, DocumentCompass]:
        """Load document from text content (synchronous version).

        Args:
            content: Document text content
            format: Document format (markdown, xml, etc.)
            title: Optional document title

        Returns:
            Tuple of (doc_id, DocumentCompass) where doc_id is auto-generated UUID
        """
        try:
            doc_id = self._generate_doc_id()
            compass = DocumentCompass(content, format)
            self.loaded_documents[doc_id] = compass

            # Store metadata
            self.document_metadata[doc_id] = {
                "title": title or "Untitled Document",
                "format": format,
                "source_type": "text",
                "created_at": str(uuid.uuid1().time),
            }

            return doc_id, compass
        except Exception as e:
            raise ValueError(f"Error loading document: {str(e)}")

    async def load_document_from_text(
        self, content: str, format: str = "markdown", title: Optional[str] = None
    ) -> Tuple[str, DocumentCompass]:
        """Load document from text content.

        Args:
            content: Document text content
            format: Document format (markdown, xml, etc.)
            title: Optional document title

        Returns:
            Tuple of (doc_id, DocumentCompass) where doc_id is auto-generated UUID
        """
        # Just call the sync version since there's no actual async work
        return self.load_document_from_text_sync(content, format, title)

    def load_document_from_file_sync(
        self, file_path: Path
    ) -> Tuple[str, DocumentCompass]:
        """Load document from file (synchronous version).

        Args:
            file_path: Path to the document file

        Returns:
            Tuple of (doc_id, DocumentCompass) where doc_id is auto-generated UUID
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Normalize path to prevent injection issues
        normalized_path = self._normalize_file_path(file_path)

        # Determine format from file extension
        format_map = {
            ".md": "markdown",
            ".markdown": "markdown",
            ".xml": "xml",
        }

        file_format = format_map.get(file_path.suffix.lower(), "markdown")

        try:
            content = file_path.read_text(encoding="utf-8")
            doc_id = self._generate_doc_id()
            compass = DocumentCompass(content, file_format)
            self.loaded_documents[doc_id] = compass

            # Store metadata with normalized path
            self.document_metadata[doc_id] = {
                "title": file_path.name,
                "format": file_format,
                "source_type": "file",
                "file_path": normalized_path,
                "created_at": str(uuid.uuid1().time),
            }

            return doc_id, compass
        except Exception as e:
            raise ValueError(f"Error loading document: {str(e)}")

    async def load_document_from_file(
        self, file_path: Path
    ) -> Tuple[str, DocumentCompass]:
        """Load document from file.

        Args:
            file_path: Path to the document file

        Returns:
            Tuple of (doc_id, DocumentCompass) where doc_id is auto-generated UUID
        """
        # Just call the sync version since there's no actual async work
        return self.load_document_from_file_sync(file_path)

    def get_document(self, doc_id: str) -> Optional[DocumentCompass]:
        """Get loaded document by ID.

        Args:
            doc_id: UUID-based document identifier

        Returns:
            DocumentCompass instance or None if not found
        """
        # Validate doc_id format to prevent injection
        try:
            uuid.UUID(doc_id)  # This will raise ValueError if invalid UUID
        except ValueError:
            return None

        return self.loaded_documents.get(doc_id)

    def get_document_metadata(self, doc_id: str) -> Optional[Dict[str, str]]:
        """Get document metadata by ID.

        Args:
            doc_id: UUID-based document identifier

        Returns:
            Metadata dictionary or None if not found
        """
        try:
            uuid.UUID(doc_id)
        except ValueError:
            return None

        return self.document_metadata.get(doc_id)

    def list_documents(self) -> List[Dict[str, str]]:
        """List all loaded documents with their metadata.

        Returns:
            List of document info dictionaries
        """
        documents = []
        for doc_id, metadata in self.document_metadata.items():
            documents.append({"id": doc_id, **metadata})
        return documents

    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from the navigator.

        Args:
            doc_id: UUID-based document identifier

        Returns:
            True if document was removed, False if not found
        """
        try:
            uuid.UUID(doc_id)
        except ValueError:
            return False

        if doc_id in self.loaded_documents:
            del self.loaded_documents[doc_id]
            if doc_id in self.document_metadata:
                del self.document_metadata[doc_id]
            return True
        return False

    def get_outline(self, doc_id: str, max_depth: int = 3) -> str:
        """Get document outline."""
        compass = self.get_document(doc_id)
        if not compass:
            return f"Document '{doc_id}' not found"
        return compass.get_outline(max_depth)

    def read_section(self, doc_id: str, section_id: str) -> str:
        """Read specified section content."""
        compass = self.get_document(doc_id)
        if not compass:
            return f"Document '{doc_id}' not found"
        return compass.get_section(section_id)

    def search_document(self, doc_id: str, query: str) -> str:
        """Search document and return formatted results."""
        compass = self.get_document(doc_id)
        if not compass:
            return f"Document '{doc_id}' not found"

        results = compass.search(query)
        if not results:
            return f"No results found for '{query}'"

        output = f"Found {len(results)} results for '{query}':\n\n"
        for i, result in enumerate(results[:5], 1):  # Limit to first 5 results
            output += f"{i}. In section '{result.section}' (#{result.section_id}):\n"
            output += f"   {result.content[:100]}...\n\n"

        return output

    def navigate(self, doc_id: str, section_id: str) -> str:
        """Get navigation context as formatted string."""
        compass = self.get_document(doc_id)
        if not compass:
            return f"Document '{doc_id}' not found"

        try:
            context = compass.get_navigation_context(section_id)
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

    def get_document_tokens(
        self, doc_id: str, encoding_name: str = "cl100k_base"
    ) -> Dict[str, int]:
        """Get token statistics for a document.

        Args:
            doc_id: UUID-based document identifier
            encoding_name: The tokenizer encoding to use

        Returns:
            Dictionary with token statistics or None if document not found
        """
        compass = self.get_document(doc_id)
        if not compass:
            return None

        return {
            "total_tokens": compass.get_total_tokens(encoding_name),
            # "content_tokens": compass.get_content_tokens(encoding_name)
        }
