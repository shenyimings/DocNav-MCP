"""Tests for document navigator."""

import pytest
from pathlib import Path

from docnav.navigator import DocumentNavigator
from docnav.processors import MarkdownProcessor


class TestDocumentNavigator:
    """Tests for the document navigator."""
    
    def test_init(self) -> None:
        """Test navigator initialization."""
        navigator = DocumentNavigator()
        assert len(navigator.processors) > 0
        assert isinstance(navigator.processors[0], MarkdownProcessor)
        assert len(navigator.loaded_documents) == 0
    
    def test_get_processor(self) -> None:
        """Test processor selection."""
        navigator = DocumentNavigator()
        
        md_processor = navigator._get_processor(Path("test.md"))
        assert isinstance(md_processor, MarkdownProcessor)
        
        no_processor = navigator._get_processor(Path("test.txt"))
        assert no_processor is None
    
    @pytest.mark.anyio
    async def test_load_document_no_processor(self) -> None:
        """Test loading document with no available processor."""
        navigator = DocumentNavigator()
        
        with pytest.raises(ValueError, match="No processor available"):
            await navigator.load_document(Path("test.txt"))