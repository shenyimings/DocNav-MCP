"""PDF document processor using pymupdf4llm for DocumentNode tree structure."""

import re
from pathlib import Path
from typing import List, Optional

import pymupdf4llm

from ..models import Document, DocumentNode, SearchResult
from .base import BaseProcessor


class PDFProcessor(BaseProcessor):
    """Processor for PDF documents using pymupdf4llm and DocumentNode tree structure.

    Converts PDF documents to Markdown format and then parses into DOM-like tree
    structure for efficient navigation and content extraction.
    """

    def can_process(self, file_path: Path) -> bool:
        """Check if this processor can handle PDF files."""
        return file_path.suffix.lower() == ".pdf"

    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return [".pdf"]

    async def process(self, file_path: Path) -> Document:
        """Process a PDF document into DocumentNode tree structure.

        Args:
            file_path: Path to the PDF file

        Returns:
            Document with populated DocumentNode tree
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Convert PDF to markdown using pymupdf4llm
        markdown_content = pymupdf4llm.to_markdown(str(file_path))

        # Create document with tree structure
        document = Document(
            file_path=file_path,
            title=file_path.stem,
            source_text=markdown_content,
            source_format="pdf",
        )

        # Parse markdown content into tree structure
        root = self._parse_markdown_to_tree(markdown_content)
        document.root = root
        document.rebuild_index()

        return document

    def _parse_markdown_to_tree(self, content: str) -> DocumentNode:
        """Parse Markdown content into DocumentNode tree structure."""
        root = DocumentNode(type="document", id="root")
        lines = content.split("\n")

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
                    attributes={"line_number": line_num, "raw_line": line},
                )

                current_parents[-1].add_child(heading_node)
                current_parents.append(heading_node)
                node_counter += 1
                continue

            # Parse code blocks
            if line.strip().startswith("```"):
                code_node = DocumentNode(
                    type="code_block",
                    id=f"code_{node_counter}",
                    content=line,
                    attributes={"line_number": line_num, "language": line.strip()[3:]},
                )
                current_parents[-1].add_child(code_node)
                node_counter += 1
                continue

            # Parse lists
            if re.match(r"^(\s*)([-*+]|\d+\.)\s+", line):
                list_node = DocumentNode(
                    type="list_item",
                    id=f"list_{node_counter}",
                    content=line,
                    attributes={
                        "line_number": line_num,
                        "list_type": (
                            "ordered" if re.match(r"^\s*\d+\.", line) else "unordered"
                        ),
                    },
                )
                current_parents[-1].add_child(list_node)
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
                current_parents[-1].add_child(para_node)
                node_counter += 1

        return root

    async def extract_node(
        self, document: Document, node_id: str
    ) -> Optional[DocumentNode]:
        """Extract a specific node from the document tree.

        Args:
            document: Document containing the node tree
            node_id: ID of the node to extract

        Returns:
            DocumentNode if found, None otherwise
        """
        return document.get_node(node_id)

    async def search(self, document: Document, query: str) -> List[SearchResult]:
        """Search for content within the PDF document tree.

        Args:
            document: Document to search within
            query: Search query string

        Returns:
            List of SearchResult objects with matches
        """
        results = []
        query_lower = query.lower()

        def search_node(node: DocumentNode) -> None:
            if query_lower in node.content.lower():
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

        if document.root:
            search_node(document.root)

        return results

    def get_heading_hierarchy(self, document: Document) -> List[dict]:
        """Get hierarchical structure of headings in the document.

        Args:
            document: Document to analyze

        Returns:
            List of heading information with hierarchy
        """
        headings = []

        def collect_headings(node: DocumentNode, depth: int = 0) -> None:
            if node.type == "heading" and node.level:
                headings.append(
                    {
                        "id": node.id,
                        "title": node.title,
                        "level": node.level,
                        "depth": depth,
                        "line_number": node.attributes.get("line_number"),
                        "has_children": bool(
                            [
                                child
                                for child in node.children
                                if child.type == "heading"
                            ]
                        ),
                    }
                )

            for child in node.children:
                collect_headings(child, depth + 1 if node.type == "heading" else depth)

        if document.root:
            collect_headings(document.root)

        return headings
