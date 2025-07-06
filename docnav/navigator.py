"""Document navigation engine - DOM-like tree structure approach."""

import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

import tiktoken
from markdown_it import MarkdownIt

from .models import Document, DocumentNode, NavigationContext, SearchResult
from .processors import MarkdownProcessor, PDFProcessor


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
        self.loaded_documents: Dict[str, Document] = {}
        self.document_metadata: Dict[
            str, Dict[str, str]
        ] = {}  # Store metadata by doc_id

        # Initialize processors
        self.processors = [
            MarkdownProcessor(),
            PDFProcessor(),
        ]

    def _generate_doc_id(self) -> str:
        """Generate a unique document ID using UUID."""
        return str(uuid.uuid4())

    def _find_processor(self, file_path: Path):
        """Find the appropriate processor for a file."""
        for processor in self.processors:
            if processor.can_process(file_path):
                return processor
        # Default to markdown processor if no specific processor found
        return self.processors[0]  # MarkdownProcessor

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
    ) -> Tuple[str, Document]:
        """Load document from text content (synchronous version).

        Args:
            content: Document text content
            format: Document format (markdown, xml, etc.)
            title: Optional document title

        Returns:
            Tuple of (doc_id, Document) where doc_id is auto-generated UUID
        """
        try:
            # For sync version, use the old DocumentCompass approach for text
            # since we can't await in sync methods
            doc_id = self._generate_doc_id()

            # Create a Document object manually for text content
            from .models import Document, DocumentNode

            document = Document(
                file_path=None,
                title=title or "Untitled Document",
                source_text=content,
                source_format=format,
            )

            # Create simple document structure for text
            if format == "markdown":
                # Use the old DocumentCompass for parsing markdown text
                compass = DocumentCompass(content, format)
                # Convert compass structure to Document structure
                document.root = compass.root
                document.rebuild_index()
            else:
                # For other formats, create a simple root node
                root = DocumentNode(type="document", id="root")
                root.content = content
                document.root = root
                document.rebuild_index()

            self.loaded_documents[doc_id] = document

            # Store metadata
            self.document_metadata[doc_id] = {
                "title": title or "Untitled Document",
                "format": format,
                "source_type": "text",
                "created_at": str(uuid.uuid1().time),
            }

            return doc_id, document

        except Exception as e:
            raise ValueError(f"Error loading document: {str(e)}")

    async def load_document_from_text(
        self, content: str, format: str = "markdown", title: Optional[str] = None
    ) -> Tuple[str, Document]:
        """Load document from text content.

        Args:
            content: Document text content
            format: Document format (markdown, xml, etc.)
            title: Optional document title

        Returns:
            Tuple of (doc_id, Document) where doc_id is auto-generated UUID
        """
        try:
            # Create a temporary file to use with processors
            import tempfile

            # Determine file extension based on format
            ext_map = {"markdown": ".md", "xml": ".xml", "pdf": ".pdf"}
            ext = ext_map.get(format, ".md")

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=ext, delete=False, encoding="utf-8"
            ) as f:
                f.write(content)
                temp_path = Path(f.name)

            try:
                # Find appropriate processor
                processor = self._find_processor(temp_path)

                # Process the document
                document = await processor.process(temp_path)
                doc_id = self._generate_doc_id()

                # Update document metadata
                document.title = title or "Untitled Document"

                self.loaded_documents[doc_id] = document

                # Store metadata
                self.document_metadata[doc_id] = {
                    "title": title or "Untitled Document",
                    "format": format,
                    "source_type": "text",
                    "created_at": str(uuid.uuid1().time),
                }

                return doc_id, document
            finally:
                # Clean up temporary file
                temp_path.unlink()

        except Exception as e:
            raise ValueError(f"Error loading document: {str(e)}")

    def load_document_from_file_sync(self, file_path: Path) -> Tuple[str, Document]:
        """Load document from file (synchronous version).

        Args:
            file_path: Path to the document file

        Returns:
            Tuple of (doc_id, Document) where doc_id is auto-generated UUID
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Normalize path to prevent injection issues
        normalized_path = self._normalize_file_path(file_path)

        try:
            # Check if we're in an async context (like MCP server)
            import asyncio

            try:
                # Try to get the running event loop
                asyncio.get_running_loop()
                # If we get here, we're in an async context
                # Fall back to sync processing immediately
                return self._load_file_fallback_sync(file_path)
            except RuntimeError:
                # No running event loop, we can use asyncio.run
                processor = self._find_processor(file_path)
                document = asyncio.run(processor.process(file_path))

                doc_id = self._generate_doc_id()
                self.loaded_documents[doc_id] = document

                # Store metadata with normalized path
                self.document_metadata[doc_id] = {
                    "title": file_path.name,
                    "format": document.source_format,
                    "source_type": "file",
                    "file_path": normalized_path,
                    "created_at": str(uuid.uuid1().time),
                }

                return doc_id, document

        except Exception as e:
            # For any error, fall back to sync processing
            try:
                return self._load_file_fallback_sync(file_path)
            except Exception as fallback_error:
                raise ValueError(
                    f"Error loading document: {str(e)}. Fallback also failed: {str(fallback_error)}"
                )

    def _load_file_fallback_sync(self, file_path: Path) -> Tuple[str, Document]:
        """Fallback sync file loading for when async processors can't be used."""
        normalized_path = self._normalize_file_path(file_path)

        # Handle PDF files directly with pymupdf4llm (which is actually sync)
        if file_path.suffix.lower() == ".pdf":
            try:
                import pymupdf4llm

                # Convert PDF to markdown using pymupdf4llm (this is actually synchronous)
                markdown_content = pymupdf4llm.to_markdown(str(file_path))

                # Create Document object
                from .models import Document

                document = Document(
                    file_path=file_path,
                    title=file_path.stem,
                    source_text=markdown_content,
                    source_format="pdf",
                )

                # Use markdown processor to parse the converted content
                # Create temporary file for processing
                import tempfile

                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".md", delete=False, encoding="utf-8"
                ) as f:
                    f.write(markdown_content)
                    temp_path = Path(f.name)

                try:
                    # Use the markdown processor synchronously by creating a simple parser
                    from .processors.markdown import MarkdownProcessor

                    md_processor = MarkdownProcessor()

                    # Parse using the internal parsing method directly
                    root = md_processor._parse_markdown_to_tree(markdown_content)
                    document.root = root
                    document.rebuild_index()

                finally:
                    temp_path.unlink()  # Clean up

                # Generate doc ID and store
                doc_id = self._generate_doc_id()
                self.loaded_documents[doc_id] = document

                # Store metadata
                self.document_metadata[doc_id] = {
                    "title": file_path.name,
                    "format": "pdf",
                    "source_type": "file",
                    "file_path": normalized_path,
                    "created_at": str(uuid.uuid1().time),
                }

                return doc_id, document

            except ImportError:
                raise ValueError(
                    "pymupdf4llm is required for PDF processing but not available"
                )
            except Exception as e:
                raise ValueError(f"Error processing PDF file: {str(e)}")

        # For markdown and other text files
        content = file_path.read_text(encoding="utf-8")
        format_map = {
            ".md": "markdown",
            ".markdown": "markdown",
            ".xml": "xml",
        }
        file_format = format_map.get(file_path.suffix.lower(), "markdown")

        # Use the sync text loading method
        doc_id, document = self.load_document_from_text_sync(
            content, file_format, file_path.stem
        )

        # Update metadata to reflect file source
        self.document_metadata[doc_id].update(
            {
                "source_type": "file",
                "file_path": normalized_path,
            }
        )

        return doc_id, document

    async def load_document_from_file(self, file_path: Path) -> Tuple[str, Document]:
        """Load document from file.

        Args:
            file_path: Path to the document file

        Returns:
            Tuple of (doc_id, Document) where doc_id is auto-generated UUID
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Normalize path to prevent injection issues
        normalized_path = self._normalize_file_path(file_path)

        try:
            # Find appropriate processor for this file type
            processor = self._find_processor(file_path)

            # Process the document
            document = await processor.process(file_path)
            doc_id = self._generate_doc_id()
            self.loaded_documents[doc_id] = document

            # Store metadata with normalized path
            self.document_metadata[doc_id] = {
                "title": file_path.name,
                "format": document.source_format,
                "source_type": "file",
                "file_path": normalized_path,
                "created_at": str(uuid.uuid1().time),
            }

            return doc_id, document
        except Exception as e:
            raise ValueError(f"Error loading document: {str(e)}")

    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get loaded document by ID.

        Args:
            doc_id: UUID-based document identifier

        Returns:
            Document instance or None if not found
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
        document = self.get_document(doc_id)
        if not document:
            return f"Document '{doc_id}' not found"

        # Create a simple outline from document nodes
        outline = []

        def build_outline(node: DocumentNode, depth: int = 0) -> None:
            if depth > max_depth:
                return

            if node.type == "heading" and node.title:
                indent = "  " * (depth - 1) if depth > 0 else ""
                outline.append(f"{indent}#{node.id} - {node.title}")

            for child in node.children:
                build_outline(child, depth + 1 if node.type == "heading" else depth)

        if document.root:
            build_outline(document.root)

        return "\n".join(outline)

    def read_section(self, doc_id: str, section_id: str) -> str:
        """Read specified section content."""
        document = self.get_document(doc_id)
        if not document:
            return f"Document '{doc_id}' not found"

        # Get the node and return its content with subsections
        node = document.get_node(section_id)
        if not node:
            return f"Section '{section_id}' not found"

        content = [node.content] if node.content else []

        def collect_content(n: DocumentNode) -> None:
            for child in n.children:
                if child.content:
                    content.append(child.content)
                collect_content(child)

        collect_content(node)
        return "\n".join(content)

    def search_document(self, doc_id: str, query: str) -> str:
        """Search document and return formatted results."""
        document = self.get_document(doc_id)
        if not document:
            return f"Document '{doc_id}' not found"

        # Perform search using document's search functionality
        results = []
        query_lower = query.lower()

        def search_node(node: DocumentNode) -> None:
            if query_lower in node.content.lower():
                # Find nearest heading as context
                parent = node.parent
                while parent and parent.type != "heading":
                    parent = parent.parent

                section_title = parent.title if parent else "Document Root"

                from .models import SearchResult

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

        if not results:
            return f"No results found for '{query}'"

        output = f"Found {len(results)} results for '{query}':\n\n"
        for i, result in enumerate(results[:5], 1):  # Limit to first 5 results
            output += f"{i}. In section '{result.section}' (#{result.section_id}):\n"
            output += f"   {result.content[:100]}...\n\n"

        return output

    def navigate(self, doc_id: str, section_id: str) -> str:
        """Get navigation context as formatted string."""
        document = self.get_document(doc_id)
        if not document:
            return f"Document '{doc_id}' not found"

        node = document.get_node(section_id)
        if not node:
            return f"Section '{section_id}' not found"

        output = f"Current: {node.title or node.id}\n"

        # Build breadcrumbs
        ancestors = []
        current = node.parent
        while current and current.type != "document":
            if current.type == "heading":
                ancestors.append(current)
            current = current.parent

        if ancestors:
            breadcrumb_path = " > ".join([a.title for a in reversed(ancestors)])
            output += f"Path: {breadcrumb_path} > {node.title or node.id}\n"

        # Find parent
        if node.parent and node.parent.type == "heading":
            output += f"Parent: {node.parent.title}\n"

        # Find siblings (same level headings)
        if node.parent:
            siblings = [
                child for child in node.parent.children if child.type == "heading"
            ]
            if len(siblings) > 1:
                output += "Siblings:\n"
                for sibling in siblings:
                    marker = "→ " if sibling.id == node.id else "  "
                    output += f"{marker}{sibling.title} (#{sibling.id})\n"

        # Find children (direct child headings)
        children = [child for child in node.children if child.type == "heading"]
        if children:
            output += "Subsections:\n"
            for child in children:
                output += f"  {child.title} (#{child.id})\n"

        return output

    def get_document_tokens(
        self, doc_id: str, encoding_name: str = "cl100k_base"
    ) -> Optional[Dict[str, int]]:
        """Get token statistics for a document.

        Args:
            doc_id: UUID-based document identifier
            encoding_name: The tokenizer encoding to use

        Returns:
            Dictionary with token statistics or None if document not found
        """
        document = self.get_document(doc_id)
        if not document:
            return None

        try:
            encoding = tiktoken.get_encoding(encoding_name)
            total_tokens = len(encoding.encode(document.source_text))
        except Exception:
            # Fallback to simple word-based estimation if tiktoken fails
            words = len(document.source_text.split())
            total_tokens = int(words / 0.75)

        return {
            "total_tokens": total_tokens,
        }
