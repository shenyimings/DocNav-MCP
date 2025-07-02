"""Tests for document processors."""

import pytest
from pathlib import Path

from docnav.processors import MarkdownProcessor


class TestMarkdownProcessor:
    """Tests for the Markdown processor."""
    
    def test_can_process_markdown_files(self) -> None:
        """Test that processor can identify Markdown files."""
        processor = MarkdownProcessor()
        
        assert processor.can_process(Path("test.md"))
        assert processor.can_process(Path("test.markdown"))
        assert processor.can_process(Path("TEST.MD"))
        assert not processor.can_process(Path("test.txt"))
        assert not processor.can_process(Path("test.pdf"))
    
    @pytest.mark.anyio
    async def test_process_placeholder(self) -> None:
        """Placeholder test for process method."""
        processor = MarkdownProcessor()
        # TODO: Implement actual test when process method is implemented
        assert processor is not None