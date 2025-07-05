# DocNav MCP Server

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
        "run",
        "server.py"
      ]
    }
  }
}
```

### Available Tools

The server provides the following MCP tools:

- `load_document`: Load and process a document for navigation
- `get_outline`: Get the document outline/table of contents
- `read_section`: Retrieve content from a specific document section
- `search_document`: Search for content within a document

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
- [ ] Add PDF document support
- [ ] Improve test coverage and quality
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

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation in CLAUDE.md
- Review existing issues and discussions