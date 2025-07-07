# DocNav MCP Server

[![License](https://img.shields.io/github/license/shenyimings/DocNav-MCP)](https://github.com/shenyimings/DocNav-MCP/blob/main/LICENSE) [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/) [![smithery badge](https://smithery.ai/badge/@shenyimings/docnav-mcp)](https://smithery.ai/server/@shenyimings/docnav-mcp)


DocNav is a Model Context Protocol (MCP) server which empowers LLM Agents to read, analyze, and manage lengthy documents intelligently, mimicking human-like comprehension and navigation capabilities.

## Features

- **Document Navigation**: Navigate through document sections, headings, and content structure
- **Content Extraction**: Extract and summarize specific document sections
- **Search & Query**: Find specific content within documents using intelligent search
- **Multi-format Support**: Currently supports Markdown (.md) files, with planned support for PDF and other formats
- **MCP Integration**: Seamless integration with MCP-compatible LLMs and applications

## Architecture

DocNav follows a modular, extensible architecture:

- **Core MCP Server**: Main server implementation using the MCP protocol
- **Document Processors**: Pluggable processors for different file types
- **Navigation Engine**: Handles document structure analysis and navigation
- **Content Extractors**: Extract and format content from documents
- **Search Engine**: Provides search and query capabilities across documents

## Installation

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/shenyimings/DocNav-MCP.git
cd DocNav-MCP
```

2. Install dependencies:
```bash
uv sync
```


## Usage

### Starting the MCP Server

```bash
uv run server.py
```

### Connect to the MCP server

```json
{
  "mcpServers": {
    "docnav": {
      "command": "{{PATH_TO_UV}}", // Run `which uv` and place the output here
      "args": [
        "--directory",
        "{{PATH_TO_SRC}}",
        "run",
        "server.py"
      ]
    }
  }
}
```

### Available Tools

- `load_document`: Load a document for navigation and analysis
    - Args: `file_path` (path to document file)
    - Returns: Success message with auto-generated document ID

- `get_outline`: Get document outline/table of contents
    - Args: `doc_id` (document identifier), `max_depth` (max heading depth, default 3)
    - Returns: Formatted document outline
    - Tip: Use first after loading a document to understand structure

- `read_section`: Read content of a specific document section
    - Args: `doc_id` (document identifier), `section_id` (e.g., 'h1_0', 'h2_1')
    - Returns: Section content with subsections

- `search_document`: Search for specific content within a document
    - Args: `doc_id` (document identifier), `query` (search term or phrase)
    - Returns: Formatted search results with context

- `navigate_section`: Get navigation context for a section
    - Args: `doc_id` (document identifier), `section_id` (section to navigate to)
    - Returns: Navigation context with parent, siblings, children

- `list_documents`: List all currently loaded documents
    - Returns: List of loaded documents with metadata

- `get_document_stats`: Get statistics about a loaded document
    - Args: `doc_id` (document identifier)
    - Returns: Document statistics and structure info

- `remove_document`: Remove a document from the navigator
    - Args: `doc_id` (document identifier)
    - Returns: Success or error message

### Example Usage

```python
# Load a document
result = await tools.load_document("path/to/document.md")

# Get document outline
outline = await tools.get_outline(doc_id)

# Get specific section content
section = await tools.read_section(doc_id, section_id)

# Search within document
results = await tools.search_document(doc_id, "search query")
```

## Development

### Project Structure

```
docnav-mcp/
--- server.py             # Main MCP server
--- docnav/
------- __init__.py           # Package initialization
------- models.py             # Data models
------- navigator.py          # Document navigation engine
------- processors/
------- __init__.py       # Processor package
------- base.py           # Base processor interface
------- markdown.py       # Markdown processor
--- tests/
------- ...                   # Test files
```

### Development Guidelines

See [CLAUDE.md](./CLAUDE.md) for detailed development guidelines including:

- Code quality standards
- Testing requirements
- Package management with uv
- Formatting and linting rules

### Adding New Document Processors

1. Create a new processor class inheriting from `BaseProcessor`
2. Implement the required methods: `can_process`, `process`, `extract_section`, `search`
3. Register the processor in the `DocumentNavigator`
4. Add comprehensive tests

### Running Tests

```bash
# Run all tests
uv run tests/run_tests.py
```

### Code Quality

```bash
# Format code
uv run --frozen ruff format .

# Check linting
uv run --frozen ruff check .

# Type checking
uv run --frozen pyright
```

## Roadmap

- [x] Complete Markdown processor implementation
- [x] Add PDF document support (PyMuPDF)
- [x] Improve test coverage and quality
- [ ] Implement advanced search capabilities
- [ ] Add document summarization features
- [ ] Support for additional document formats (DOCX, TXT, etc.)
- [ ] Performance optimizations for large documents
- [ ] Caching mechanisms for frequently accessed documents
- [ ] Add persistent storage for loaded documents

## Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the development guidelines in CLAUDE.md
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the Apache-2.0 License - see the LICENSE file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation in CLAUDE.md
- Review existing issues and discussions