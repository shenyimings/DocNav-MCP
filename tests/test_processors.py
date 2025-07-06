"""Tests for document processors."""

import sys
from pathlib import Path

import pytest

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from docnav.processors import MarkdownProcessor, PDFProcessor


class TestMarkdownProcessor:
    """Test cases for MarkdownProcessor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = MarkdownProcessor()
        self.test_md_file = Path(__file__).parent / "test_report_markdown.md"

    def test_can_process_markdown_files(self):
        """Test that processor can identify markdown files."""
        assert self.processor.can_process(Path("test.md"))
        assert self.processor.can_process(Path("test.markdown"))
        assert self.processor.can_process(Path("test.mdown"))
        assert self.processor.can_process(Path("test.mkd"))
        assert not self.processor.can_process(Path("test.txt"))
        assert not self.processor.can_process(Path("test.pdf"))

    def test_get_supported_extensions(self):
        """Test that processor returns correct supported extensions."""
        extensions = self.processor.get_supported_extensions()
        assert ".md" in extensions
        assert ".markdown" in extensions
        assert ".mdown" in extensions
        assert ".mkd" in extensions

    def test_get_processor_info(self):
        """Test that processor returns correct metadata."""
        info = self.processor.get_processor_info()
        assert info["name"] == "MarkdownProcessor"
        assert "parsing" in info["features"]
        assert "search" in info["features"]
        assert "navigation" in info["features"]

    @pytest.mark.anyio
    async def test_process_markdown_file(self):
        """Test processing of markdown file."""
        if not self.test_md_file.exists():
            pytest.skip("Test markdown file not found")

        document = await self.processor.process(self.test_md_file)

        # Check document structure
        assert document.file_path == self.test_md_file
        assert document.title == "test_report_markdown"
        assert document.source_format == "markdown"
        assert document.root is not None
        assert document.root.type == "document"
        assert document.root.id == "root"

    @pytest.mark.anyio
    async def test_process_nonexistent_file(self):
        """Test processing of non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            await self.processor.process(Path("nonexistent.md"))

    @pytest.mark.anyio
    async def test_extract_node(self):
        """Test extraction of specific nodes."""
        if not self.test_md_file.exists():
            pytest.skip("Test markdown file not found")

        document = await self.processor.process(self.test_md_file)

        # Test extracting root node
        root_node = await self.processor.extract_node(document, "root")
        assert root_node is not None
        assert root_node.type == "document"

        # Test extracting non-existent node
        non_existent = await self.processor.extract_node(document, "nonexistent")
        assert non_existent is None

    @pytest.mark.anyio
    async def test_search_functionality(self):
        """Test search functionality."""
        if not self.test_md_file.exists():
            pytest.skip("Test markdown file not found")

        document = await self.processor.process(self.test_md_file)

        # Search for common terms that likely exist in any markdown document
        results = await self.processor.search(document, "test")
        assert isinstance(results, list)

        # Each result should have required fields
        for result in results:
            assert hasattr(result, "node_id")
            assert hasattr(result, "section")
            assert hasattr(result, "content")
            assert hasattr(result, "type")

    @pytest.mark.anyio
    async def test_heading_hierarchy(self):
        """Test heading hierarchy extraction."""
        if not self.test_md_file.exists():
            pytest.skip("Test markdown file not found")

        document = await self.processor.process(self.test_md_file)
        headings = self.processor.get_heading_hierarchy(document)

        assert isinstance(headings, list)
        for heading in headings:
            assert "id" in heading
            assert "title" in heading
            assert "level" in heading
            assert heading["level"] >= 1

    @pytest.mark.anyio
    async def test_parse_markdown_structure(self):
        """Test that markdown structure is parsed correctly."""
        # Create a simple test markdown content
        test_content = """# Main Title

Some paragraph content.

## Section 1

- List item 1
- List item 2

### Subsection 1.1

```python
print("Hello World")
```

## Section 2

Another paragraph.
"""

        # Create a temporary file
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(test_content)
            temp_path = Path(f.name)

        try:
            document = await self.processor.process(temp_path)

            # Check that document has content
            assert document.root is not None
            assert len(document.root.children) > 0

            # Check that headings are parsed
            headings = self.processor.get_heading_hierarchy(document)
            assert len(headings) >= 3  # Should have at least 3 headings

            # Check heading levels
            heading_levels = [h["level"] for h in headings]
            assert 1 in heading_levels  # Main title
            assert 2 in heading_levels  # Section headers
            assert 3 in heading_levels  # Subsection

        finally:
            temp_path.unlink()  # Clean up


class TestPDFProcessor:
    """Test cases for PDFProcessor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = PDFProcessor()
        self.test_pdf_file = Path(__file__).parent / "test_report_pdf.pdf"

    def test_can_process_pdf_files(self):
        """Test that processor can identify PDF files."""
        assert self.processor.can_process(Path("test.pdf"))
        assert self.processor.can_process(Path("test.PDF"))
        assert not self.processor.can_process(Path("test.txt"))
        assert not self.processor.can_process(Path("test.md"))

    def test_get_supported_extensions(self):
        """Test that processor returns correct supported extensions."""
        extensions = self.processor.get_supported_extensions()
        assert ".pdf" in extensions

    def test_get_processor_info(self):
        """Test that processor returns correct metadata."""
        info = self.processor.get_processor_info()
        assert info["name"] == "PDFProcessor"
        assert "parsing" in info["features"]
        assert "search" in info["features"]
        assert "navigation" in info["features"]

    @pytest.mark.anyio
    async def test_process_pdf_file(self):
        """Test processing of PDF file."""
        if not self.test_pdf_file.exists():
            pytest.skip("Test PDF file not found")

        document = await self.processor.process(self.test_pdf_file)

        # Check document structure
        assert document.file_path == self.test_pdf_file
        assert document.title == "test_report_pdf"
        assert document.source_format == "pdf"
        assert document.root is not None
        assert document.root.type == "document"
        assert document.root.id == "root"

        # Check that PDF content was converted to markdown
        assert isinstance(document.source_text, str)
        assert len(document.source_text) > 0

    @pytest.mark.anyio
    async def test_process_nonexistent_pdf(self):
        """Test processing of non-existent PDF file raises error."""
        with pytest.raises(FileNotFoundError):
            await self.processor.process(Path("nonexistent.pdf"))

    @pytest.mark.anyio
    async def test_extract_node_pdf(self):
        """Test extraction of specific nodes from PDF."""
        if not self.test_pdf_file.exists():
            pytest.skip("Test PDF file not found")

        document = await self.processor.process(self.test_pdf_file)

        # Test extracting root node
        root_node = await self.processor.extract_node(document, "root")
        assert root_node is not None
        assert root_node.type == "document"

        # Test extracting non-existent node
        non_existent = await self.processor.extract_node(document, "nonexistent")
        assert non_existent is None

    @pytest.mark.anyio
    async def test_search_pdf_content(self):
        """Test search functionality on PDF content."""
        if not self.test_pdf_file.exists():
            pytest.skip("Test PDF file not found")

        document = await self.processor.process(self.test_pdf_file)

        # Search for common terms that likely exist in any document
        results = await self.processor.search(document, "test")
        assert isinstance(results, list)

        # Each result should have required fields
        for result in results:
            assert hasattr(result, "node_id")
            assert hasattr(result, "section")
            assert hasattr(result, "content")
            assert hasattr(result, "type")

    @pytest.mark.anyio
    async def test_pdf_heading_hierarchy(self):
        """Test heading hierarchy extraction from PDF."""
        if not self.test_pdf_file.exists():
            pytest.skip("Test PDF file not found")

        document = await self.processor.process(self.test_pdf_file)
        headings = self.processor.get_heading_hierarchy(document)

        assert isinstance(headings, list)
        for heading in headings:
            assert "id" in heading
            assert "title" in heading
            assert "level" in heading
            assert heading["level"] >= 1


class TestProcessorComparison:
    """Test cases comparing processors."""

    def setup_method(self):
        """Set up test fixtures."""
        self.md_processor = MarkdownProcessor()
        self.pdf_processor = PDFProcessor()
        self.test_md_file = Path(__file__).parent / "test_report_markdown.md"
        self.test_pdf_file = Path(__file__).parent / "test_report_pdf.pdf"

    @pytest.mark.anyio
    async def test_both_processors_create_valid_documents(self):
        """Test that both processors create valid document structures."""
        md_doc = None
        pdf_doc = None

        if self.test_md_file.exists():
            md_doc = await self.md_processor.process(self.test_md_file)

        if self.test_pdf_file.exists():
            pdf_doc = await self.pdf_processor.process(self.test_pdf_file)

        for doc in [md_doc, pdf_doc]:
            if doc is not None:
                assert doc.root is not None
                assert doc.root.type == "document"
                assert doc.root.id == "root"
                assert hasattr(doc, "file_path")
                assert hasattr(doc, "title")
                assert hasattr(doc, "source_format")

    @pytest.mark.anyio
    async def test_search_consistency(self):
        """Test that search works consistently across processors."""
        md_doc = None
        pdf_doc = None

        if self.test_md_file.exists():
            md_doc = await self.md_processor.process(self.test_md_file)

        if self.test_pdf_file.exists():
            pdf_doc = await self.pdf_processor.process(self.test_pdf_file)

        search_term = "test"

        for doc, processor in [
            (md_doc, self.md_processor),
            (pdf_doc, self.pdf_processor),
        ]:
            if doc is not None:
                results = await processor.search(doc, search_term)
                assert isinstance(results, list)

                # Each result should have the same structure
                for result in results:
                    assert hasattr(result, "node_id")
                    assert hasattr(result, "section")
                    assert hasattr(result, "content")
                    assert hasattr(result, "type")
                    assert search_term.lower() in result.content.lower()

    def test_processor_metadata_consistency(self):
        """Test that processor metadata is consistent."""
        md_info = self.md_processor.get_processor_info()
        pdf_info = self.pdf_processor.get_processor_info()

        # Both should have the same feature set
        assert md_info["features"] == pdf_info["features"]

        # Both should have valid names
        assert md_info["name"] == "MarkdownProcessor"
        assert pdf_info["name"] == "PDFProcessor"

        # Both should have supported extensions
        assert len(md_info["supported_extensions"]) > 0
        assert len(pdf_info["supported_extensions"]) > 0
