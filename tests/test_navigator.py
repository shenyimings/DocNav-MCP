"""Tests for document navigator and compass classes."""

import sys
from pathlib import Path

import pytest

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from docnav.navigator import DocumentCompass, DocumentNavigator


class TestDocumentCompass:
    """Test cases for DocumentCompass class."""

    def test_init_with_markdown(self):
        """Test initialization with markdown content."""
        content = "# Test\n\nHello world"
        compass = DocumentCompass(content, "markdown")

        assert compass.source_text == content
        assert compass.source_format == "markdown"
        assert compass.root is not None
        assert compass.root.type == "document"
        assert compass.root.id == "root"

    def test_init_with_xml(self):
        """Test initialization with XML content."""
        content = "<root><test>Hello</test></root>"
        compass = DocumentCompass(content, "xml")

        assert compass.source_text == content
        assert compass.source_format == "xml"
        assert compass.root is not None

    def test_init_with_unsupported_format(self):
        """Test initialization with unsupported format raises error."""
        with pytest.raises(ValueError, match="Unsupported format"):
            DocumentCompass("test", "unsupported")

    def test_parse_markdown_headings(self):
        """Test parsing of markdown headings."""
        content = """# Main Title

## Section 1

Content here.

### Subsection 1.1

More content.

## Section 2

Final content.
"""
        compass = DocumentCompass(content, "markdown")

        # Test that index contains heading nodes
        heading_nodes = [
            node for node in compass.index.values() if node.type == "heading"
        ]
        assert len(heading_nodes) >= 3

        # Test heading hierarchy
        h1_nodes = [node for node in heading_nodes if node.level == 1]
        h2_nodes = [node for node in heading_nodes if node.level == 2]
        h3_nodes = [node for node in heading_nodes if node.level == 3]

        assert len(h1_nodes) >= 1
        assert len(h2_nodes) >= 2
        assert len(h3_nodes) >= 1

    def test_parse_markdown_lists(self):
        """Test parsing of markdown lists."""
        content = """# Test

- Item 1
- Item 2
  - Nested item
- Item 3

1. Numbered item 1
2. Numbered item 2
"""
        compass = DocumentCompass(content, "markdown")

        # Should have list and list_item nodes
        list_nodes = [node for node in compass.index.values() if node.type == "list"]
        list_item_nodes = [
            node for node in compass.index.values() if node.type == "list_item"
        ]

        assert len(list_nodes) >= 2  # bullet and ordered lists
        assert len(list_item_nodes) >= 5  # total items

    def test_parse_markdown_code_blocks(self):
        """Test parsing of markdown code blocks."""
        content = """# Test

```python
def hello():
    print("Hello World")
```

```javascript
console.log("Hello");
```
"""
        compass = DocumentCompass(content, "markdown")

        code_nodes = [
            node for node in compass.index.values() if node.type == "code_block"
        ]
        assert len(code_nodes) >= 2

    def test_get_outline(self):
        """Test outline generation."""
        content = """# Main Title

## Section 1

### Subsection 1.1

## Section 2

### Subsection 2.1
"""
        compass = DocumentCompass(content, "markdown")
        outline = compass.get_outline(max_depth=3)

        assert "Main Title" in outline
        assert "Section 1" in outline
        assert "Section 2" in outline
        assert "Subsection 1.1" in outline
        assert "Subsection 2.1" in outline

    def test_get_section_content(self):
        """Test section content extraction."""
        content = """# Main Title

## Section 1

This is section 1 content.

### Subsection 1.1

This is subsection content.

## Section 2

This is section 2 content.
"""
        compass = DocumentCompass(content, "markdown")

        # Find a section node
        section_nodes = [
            node
            for node in compass.index.values()
            if node.type == "heading" and "Section 1" in node.title
        ]
        if section_nodes:
            section_content = compass.get_section(section_nodes[0].id)
            assert "Section 1" in section_content

    def test_search_functionality(self):
        """Test search functionality."""
        content = """# Main Title

## Section 1

This contains the word elephant.

## Section 2

This contains the word tiger.
"""
        compass = DocumentCompass(content, "markdown")

        # Search for specific term
        results = compass.search("elephant")
        assert len(results) >= 1
        assert any("elephant" in result.content.lower() for result in results)

        # Search for non-existent term
        results = compass.search("nonexistent")
        assert len(results) == 0

    def test_navigation_context(self):
        """Test navigation context generation."""
        content = """# Main Title

## Section 1

### Subsection 1.1

## Section 2

### Subsection 2.1
"""
        compass = DocumentCompass(content, "markdown")

        # Find a section node to test navigation
        section_nodes = [
            node
            for node in compass.index.values()
            if node.type == "heading" and node.level == 2
        ]
        if section_nodes:
            context = compass.get_navigation_context(section_nodes[0].id)
            assert context.current is not None
            assert context.current["type"] == "heading"

    def test_token_counting(self):
        """Test token counting functionality."""
        content = "# Test\n\nThis is a test document with some content."
        compass = DocumentCompass(content, "markdown")

        total_tokens = compass.get_total_tokens()
        assert total_tokens > 0
        assert isinstance(total_tokens, int)

        content_tokens = compass.get_content_tokens()
        assert content_tokens > 0
        assert isinstance(content_tokens, int)

    def test_build_index(self):
        """Test index building."""
        content = """# Main Title

## Section 1

Content here.
"""
        compass = DocumentCompass(content, "markdown")

        # Index should contain all nodes with IDs
        assert len(compass.index) > 0
        assert "root" in compass.index

        # All indexed nodes should have IDs
        for node_id, node in compass.index.items():
            assert node.id == node_id


class TestDocumentNavigator:
    """Test cases for DocumentNavigator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.navigator = DocumentNavigator()
        self.test_md_file = Path(__file__).parent / "test_report_markdown.md"
        self.test_pdf_file = Path(__file__).parent / "test_report_pdf.pdf"

    def test_init(self):
        """Test navigator initialization."""
        assert self.navigator.loaded_documents == {}
        assert self.navigator.document_metadata == {}

    def test_generate_doc_id(self):
        """Test document ID generation."""
        doc_id = self.navigator._generate_doc_id()
        assert isinstance(doc_id, str)
        assert len(doc_id) > 0

        # Should be valid UUID
        import uuid

        uuid.UUID(doc_id)  # This will raise ValueError if invalid

    def test_normalize_file_path(self):
        """Test file path normalization."""
        test_path = Path(__file__).parent / "test_file.txt"
        normalized = self.navigator._normalize_file_path(test_path)
        assert isinstance(normalized, str)
        assert test_path.name in normalized

    @pytest.mark.anyio
    async def test_load_document_from_text(self):
        """Test loading document from text content."""
        content = "# Test Document\n\nThis is a test."
        doc_id, compass = await self.navigator.load_document_from_text(content)

        assert isinstance(doc_id, str)
        assert isinstance(compass, DocumentCompass)
        assert doc_id in self.navigator.loaded_documents
        assert doc_id in self.navigator.document_metadata

        # Check metadata
        metadata = self.navigator.get_document_metadata(doc_id)
        assert metadata is not None
        assert metadata["format"] == "markdown"
        assert metadata["source_type"] == "text"

    def test_load_document_from_text_sync(self):
        """Test synchronous loading of document from text."""
        content = "# Test Document\n\nThis is a test."
        doc_id, compass = self.navigator.load_document_from_text_sync(content)

        assert isinstance(doc_id, str)
        assert isinstance(compass, DocumentCompass)
        assert doc_id in self.navigator.loaded_documents

    @pytest.mark.anyio
    async def test_load_document_from_file(self):
        """Test loading document from file."""
        if not self.test_md_file.exists():
            pytest.skip("Test markdown file not found")

        doc_id, compass = await self.navigator.load_document_from_file(
            self.test_md_file
        )

        assert isinstance(doc_id, str)
        assert isinstance(compass, DocumentCompass)
        assert doc_id in self.navigator.loaded_documents

        # Check metadata
        metadata = self.navigator.get_document_metadata(doc_id)
        assert metadata is not None
        assert metadata["format"] == "markdown"
        assert metadata["source_type"] == "file"
        assert self.test_md_file.name in metadata["title"]

    def test_load_document_from_file_sync(self):
        """Test synchronous loading of document from file."""
        if not self.test_md_file.exists():
            pytest.skip("Test markdown file not found")

        doc_id, compass = self.navigator.load_document_from_file_sync(self.test_md_file)

        assert isinstance(doc_id, str)
        assert isinstance(compass, DocumentCompass)

    @pytest.mark.anyio
    async def test_load_nonexistent_file(self):
        """Test loading non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            await self.navigator.load_document_from_file(Path("nonexistent.md"))

    def test_get_document(self):
        """Test getting loaded document."""
        content = "# Test Document\n\nThis is a test."
        doc_id, compass = self.navigator.load_document_from_text_sync(content)

        # Get existing document
        retrieved = self.navigator.get_document(doc_id)
        assert retrieved is compass

        # Get non-existent document
        non_existent = self.navigator.get_document("invalid-id")
        assert non_existent is None

    def test_get_document_metadata(self):
        """Test getting document metadata."""
        content = "# Test Document\n\nThis is a test."
        doc_id, _ = self.navigator.load_document_from_text_sync(
            content, title="My Test"
        )

        metadata = self.navigator.get_document_metadata(doc_id)
        assert metadata is not None
        assert metadata["title"] == "My Test"
        assert metadata["format"] == "markdown"

        # Test invalid ID
        invalid_metadata = self.navigator.get_document_metadata("invalid-id")
        assert invalid_metadata is None

    def test_list_documents(self):
        """Test listing all documents."""
        # Initially empty
        docs = self.navigator.list_documents()
        assert len(docs) == 0

        # Add some documents
        content1 = "# Doc 1\n\nContent 1"
        content2 = "# Doc 2\n\nContent 2"
        doc_id1, _ = self.navigator.load_document_from_text_sync(
            content1, title="Doc 1"
        )
        doc_id2, _ = self.navigator.load_document_from_text_sync(
            content2, title="Doc 2"
        )

        docs = self.navigator.list_documents()
        assert len(docs) == 2

        # Check document info
        doc_ids = [doc["id"] for doc in docs]
        assert doc_id1 in doc_ids
        assert doc_id2 in doc_ids

    def test_remove_document(self):
        """Test removing documents."""
        content = "# Test Document\n\nThis is a test."
        doc_id, _ = self.navigator.load_document_from_text_sync(content)

        # Document should exist
        assert doc_id in self.navigator.loaded_documents
        assert doc_id in self.navigator.document_metadata

        # Remove document
        result = self.navigator.remove_document(doc_id)
        assert result is True

        # Document should be gone
        assert doc_id not in self.navigator.loaded_documents
        assert doc_id not in self.navigator.document_metadata

        # Try to remove non-existent document
        result = self.navigator.remove_document("invalid-id")
        assert result is False

    def test_get_outline(self):
        """Test getting document outline."""
        content = """# Main Title

## Section 1

### Subsection 1.1

## Section 2
"""
        doc_id, _ = self.navigator.load_document_from_text_sync(content)

        outline = self.navigator.get_outline(doc_id)
        assert "Main Title" in outline
        assert "Section 1" in outline
        assert "Section 2" in outline

        # Test invalid document ID
        invalid_outline = self.navigator.get_outline("invalid-id")
        assert "not found" in invalid_outline

    def test_read_section(self):
        """Test reading section content."""
        content = """# Main Title

## Section 1

This is section 1 content.

## Section 2

This is section 2 content.
"""
        doc_id, compass = self.navigator.load_document_from_text_sync(content)

        # Find a section to read
        section_nodes = [
            node
            for node in compass.index.values()
            if node.type == "heading" and "Section 1" in node.title
        ]
        if section_nodes:
            section_content = self.navigator.read_section(doc_id, section_nodes[0].id)
            assert "Section 1" in section_content

        # Test invalid document ID
        invalid_section = self.navigator.read_section("invalid-id", "section-1")
        assert "not found" in invalid_section

    def test_search_document(self):
        """Test searching document content."""
        content = """# Main Title

## Section 1

This section contains the word elephant.

## Section 2

This section contains the word tiger.
"""
        doc_id, _ = self.navigator.load_document_from_text_sync(content)

        # Search for existing term
        results = self.navigator.search_document(doc_id, "elephant")
        assert "elephant" in results.lower()
        assert "results" in results.lower()

        # Search for non-existent term
        results = self.navigator.search_document(doc_id, "nonexistent")
        assert "No results found" in results

        # Test invalid document ID
        invalid_results = self.navigator.search_document("invalid-id", "test")
        assert "not found" in invalid_results

    def test_navigate(self):
        """Test navigation functionality."""
        content = """# Main Title

## Section 1

### Subsection 1.1

## Section 2

### Subsection 2.1
"""
        doc_id, compass = self.navigator.load_document_from_text_sync(content)

        # Find a section to navigate to
        section_nodes = [
            node
            for node in compass.index.values()
            if node.type == "heading" and node.level == 2
        ]
        if section_nodes:
            nav_result = self.navigator.navigate(doc_id, section_nodes[0].id)
            assert "Current:" in nav_result
            assert section_nodes[0].title in nav_result

        # Test invalid document ID
        invalid_nav = self.navigator.navigate("invalid-id", "section-1")
        assert "not found" in invalid_nav

    def test_get_document_tokens(self):
        """Test getting document token statistics."""
        content = "# Test Document\n\nThis is a test document with some content."
        doc_id, _ = self.navigator.load_document_from_text_sync(content)

        tokens = self.navigator.get_document_tokens(doc_id)
        assert tokens is not None
        assert "total_tokens" in tokens
        assert tokens["total_tokens"] > 0

        # Test invalid document ID
        invalid_tokens = self.navigator.get_document_tokens("invalid-id")
        assert invalid_tokens is None


class TestNavigatorIntegration:
    """Integration tests for navigator with real files."""

    def setup_method(self):
        """Set up test fixtures."""
        self.navigator = DocumentNavigator()
        self.test_md_file = Path(__file__).parent / "test_report_markdown.md"

    @pytest.mark.anyio
    async def test_real_file_processing(self):
        """Test processing real markdown file."""
        if not self.test_md_file.exists():
            pytest.skip("Test markdown file not found")

        doc_id, compass = await self.navigator.load_document_from_file(
            self.test_md_file
        )

        # Test basic functionality
        assert compass.root is not None
        assert len(compass.index) > 0

        # Test outline generation
        outline = self.navigator.get_outline(doc_id)
        assert len(outline) > 0

        # Test search functionality
        search_results = self.navigator.search_document(doc_id, "test")
        assert isinstance(search_results, str)

        # Test navigation
        heading_nodes = [
            node for node in compass.index.values() if node.type == "heading"
        ]
        if heading_nodes:
            nav_result = self.navigator.navigate(doc_id, heading_nodes[0].id)
            assert "Current:" in nav_result

    def test_multiple_document_management(self):
        """Test managing multiple documents."""
        content1 = "# Document 1\n\nContent for document 1."
        content2 = "# Document 2\n\nContent for document 2."

        doc_id1, _ = self.navigator.load_document_from_text_sync(
            content1, title="Doc 1"
        )
        doc_id2, _ = self.navigator.load_document_from_text_sync(
            content2, title="Doc 2"
        )

        # Both documents should be loaded
        assert len(self.navigator.loaded_documents) == 2
        assert len(self.navigator.document_metadata) == 2

        # Test independent operations
        outline1 = self.navigator.get_outline(doc_id1)
        outline2 = self.navigator.get_outline(doc_id2)

        assert "Document 1" in outline1
        assert "Document 2" in outline2
        assert "Document 1" not in outline2
        assert "Document 2" not in outline1

        # Test removal
        self.navigator.remove_document(doc_id1)
        assert len(self.navigator.loaded_documents) == 1
        assert doc_id2 in self.navigator.loaded_documents
