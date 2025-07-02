"""Comprehensive tests for DocumentCompass system."""

import pytest
from pathlib import Path
from docnav.models import DocumentNode, SearchResult, NavigationContext
from docnav.navigator import DocumentCompass, DocumentNavigator


class TestDocumentCompass:
    """Test suite for DocumentCompass core functionality."""
    
    @pytest.fixture
    def sample_markdown(self):
        """Sample Markdown content for testing."""
        return """# Introduction
This is the introduction to our document.

## Getting Started
Here's how to get started with the system.

### Prerequisites
You need these things first:
- Python 3.8+
- pip package manager

### Installation
Follow these steps to install:

1. Clone the repository
2. Install dependencies
3. Run the setup

## Advanced Topics
More complex stuff here for advanced users.

### Configuration
How to configure the system properly.

Configuration involves several steps:
- Setting up environment variables
- Configuring database connections
- Setting up logging

### Troubleshooting
Common problems and their solutions.

If you encounter issues, try these steps:
1. Check your configuration
2. Verify dependencies
3. Restart the service

# Conclusion
That's all folks! Thanks for reading.
"""
    
    @pytest.fixture
    def compass(self, sample_markdown):
        """Create DocumentCompass instance with sample content."""
        return DocumentCompass(sample_markdown, "markdown")
    
    def test_document_parsing(self, compass):
        """Test that document is parsed into correct tree structure."""
        assert compass.root is not None
        assert compass.root.type == "document"
        assert compass.root.id == "root"
        
        # Should have main headings as children
        headings = [child for child in compass.root.children if child.type == "heading"]
        assert len(headings) >= 2  # Introduction and Conclusion at minimum
        
        # Check first heading
        intro_heading = headings[0]
        assert intro_heading.title == "Introduction"
        assert intro_heading.level == 1
        assert intro_heading.id.startswith("h1_")
    
    def test_index_building(self, compass):
        """Test that node index is built correctly."""
        assert len(compass.index) > 0
        
        # All nodes should be indexed
        for node_id, node in compass.index.items():
            assert node.id == node_id
            assert node_id != ""
        
        # Should have heading nodes indexed
        heading_nodes = [node for node in compass.index.values() if node.type == "heading"]
        assert len(heading_nodes) >= 6  # Multiple heading levels
    
    def test_get_outline(self, compass):
        """Test outline generation."""
        outline = compass.get_outline(max_depth=3)
        assert outline is not None
        assert len(outline) > 0
        
        # Should contain main headings
        assert "Introduction" in outline
        assert "Getting Started" in outline
        assert "Conclusion" in outline
        
        # Should show hierarchy with indentation
        lines = outline.split("\n")
        assert any("  -" in line for line in lines)  # Should have indented subsections
    
    def test_get_section_content(self, compass):
        """Test section content extraction."""
        # Find a heading node
        heading_node = None
        for node in compass.index.values():
            if node.type == "heading" and node.title == "Introduction":
                heading_node = node
                break
        
        assert heading_node is not None
        
        # Get section content
        content = compass.get_section(heading_node.id, include_subsections=True)
        assert content is not None
        assert "Introduction" in content
        assert "introduction to our document" in content
    
    def test_search_functionality(self, compass):
        """Test document search capabilities."""
        # Search for common term
        results = compass.search("install")
        assert len(results) > 0
        
        # Check result structure
        result = results[0]
        assert isinstance(result, SearchResult)
        assert result.node_id is not None
        assert result.content is not None
        assert "install" in result.content.lower()
        
        # Search for specific term
        config_results = compass.search("configuration")
        assert len(config_results) > 0
        
        # Should find in Configuration section
        config_result = config_results[0]
        assert "Configuration" in config_result.section or "configuration" in config_result.content.lower()
    
    def test_navigation_context(self, compass):
        """Test navigation context generation."""
        # Find a subsection heading
        subsection_node = None
        for node in compass.index.values():
            if node.type == "heading" and node.level == 3:  # H3 level
                subsection_node = node
                break
        
        assert subsection_node is not None
        
        # Get navigation context
        context = compass.get_navigation_context(subsection_node.id)
        assert isinstance(context, NavigationContext)
        assert context.current is not None
        assert context.current["id"] == subsection_node.id
        
        # Should have parent information for subsection
        if subsection_node.parent and subsection_node.parent.type == "heading":
            assert context.parent is not None
    
    def test_hierarchical_structure(self, compass):
        """Test that hierarchical structure is correctly maintained."""
        # Find "Getting Started" section
        getting_started = None
        for node in compass.index.values():
            if node.type == "heading" and node.title == "Getting Started":
                getting_started = node
                break
        
        assert getting_started is not None
        assert getting_started.level == 2
        
        # Should have subsections as children
        child_headings = [child for child in getting_started.children if child.type == "heading"]
        assert len(child_headings) >= 2  # Prerequisites and Installation
        
        # Check subsection levels
        for child in child_headings:
            assert child.level == 3  # Should be H3 under H2
            assert child.parent == getting_started
    
    def test_xml_parsing(self):
        """Test XML document parsing."""
        xml_content = """<document>
            <section id="intro">
                <title>Introduction</title>
                <content>This is the introduction.</content>
            </section>
            <section id="main">
                <title>Main Content</title>
                <content>This is the main content.</content>
            </section>
        </document>"""
        
        compass = DocumentCompass(xml_content, "xml")
        assert compass.root is not None
        assert len(compass.index) > 0
        
        # Should have parsed XML elements
        sections = [node for node in compass.index.values() if node.type == "section"]
        assert len(sections) >= 2


class TestDocumentNavigator:
    """Test suite for DocumentNavigator high-level interface."""
    
    @pytest.fixture
    def navigator(self):
        """Create DocumentNavigator instance."""
        return DocumentNavigator()
    
    @pytest.fixture
    def sample_content(self):
        """Sample content for testing."""
        return """# Test Document
This is a test document.

## Section 1
Content for section 1.

## Section 2
Content for section 2.
"""
    
    @pytest.mark.asyncio
    async def test_load_document_from_text(self, navigator, sample_content):
        """Test loading document from text content."""
        doc_id = "test_doc"
        compass = await navigator.load_document_from_text(doc_id, sample_content)
        
        assert compass is not None
        assert doc_id in navigator.loaded_documents
        assert navigator.loaded_documents[doc_id] == compass
    
    @pytest.mark.asyncio
    async def test_load_document_from_file(self, navigator, tmp_path):
        """Test loading document from file."""
        # Create temporary markdown file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\nThis is a test file.")
        
        compass = await navigator.load_document_from_file(test_file)
        assert compass is not None
        assert str(test_file) in navigator.loaded_documents
    
    def test_get_outline_interface(self, navigator):
        """Test outline interface."""
        # Load a document first
        import asyncio
        sample_content = "# Test\n## Section 1\n### Subsection"
        asyncio.run(navigator.load_document_from_text("test", sample_content))
        
        outline = navigator.get_outline("test")
        assert "Test" in outline
        assert "Section 1" in outline
    
    def test_search_interface(self, navigator):
        """Test search interface."""
        # Load a document first
        import asyncio
        sample_content = "# Test\nThis is searchable content.\n## Search Results\nMore content here."
        asyncio.run(navigator.load_document_from_text("test", sample_content))
        
        results = navigator.search_document("test", "searchable")
        assert "searchable" in results.lower()
        assert "Found" in results
    
    def test_navigation_interface(self, navigator):
        """Test navigation interface."""
        # Load a document first
        import asyncio
        sample_content = """# Main
Content here.

## Section A
Section content.

### Subsection 1
Subsection content.

## Section B
More content.
"""
        asyncio.run(navigator.load_document_from_text("test", sample_content))
        
        # Get the document and find a heading ID
        compass = navigator.get_document("test")
        heading_id = None
        for node in compass.index.values():
            if node.type == "heading" and node.level == 2:
                heading_id = node.id
                break
        
        assert heading_id is not None
        
        nav_result = navigator.navigate("test", heading_id)
        assert "Current:" in nav_result
        assert "Section" in nav_result  # Should show section info


class TestDocumentNode:
    """Test suite for DocumentNode model."""
    
    def test_node_creation(self):
        """Test basic node creation."""
        node = DocumentNode(
            type="heading",
            level=1,
            id="h1_0",
            title="Test Heading",
            content="# Test Heading"
        )
        
        assert node.type == "heading"
        assert node.level == 1
        assert node.id == "h1_0"
        assert node.title == "Test Heading"
        assert node.content == "# Test Heading"
        assert isinstance(node.attributes, dict)
        assert isinstance(node.children, list)
    
    def test_node_hierarchy(self):
        """Test node parent-child relationships."""
        parent = DocumentNode(type="document", id="root")
        child = DocumentNode(type="heading", id="h1_0", title="Child")
        
        parent.add_child(child)
        
        assert child.parent == parent
        assert child in parent.children
        assert len(parent.children) == 1
    
    def test_get_ancestors(self):
        """Test ancestor retrieval."""
        root = DocumentNode(type="document", id="root")
        section = DocumentNode(type="heading", id="h1_0", level=1)
        subsection = DocumentNode(type="heading", id="h2_0", level=2)
        
        root.add_child(section)
        section.add_child(subsection)
        
        ancestors = subsection.get_ancestors()
        assert len(ancestors) == 2
        assert ancestors[0] == root
        assert ancestors[1] == section
    
    def test_get_depth(self):
        """Test depth calculation."""
        root = DocumentNode(type="document", id="root")
        level1 = DocumentNode(type="heading", id="h1_0")
        level2 = DocumentNode(type="heading", id="h2_0")
        
        root.add_child(level1)
        level1.add_child(level2)
        
        assert root.get_depth() == 0
        assert level1.get_depth() == 1
        assert level2.get_depth() == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])