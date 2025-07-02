"""Document navigation engine."""

from pathlib import Path
from typing import Dict, List, Optional

from .models import Document, DocumentSection
from .processors import BaseProcessor, MarkdownProcessor


class DocumentNavigator:
    """Handles document navigation and processing."""
    
    def __init__(self) -> None:
        """Initialize the document navigator."""
        self.processors: List[BaseProcessor] = [
            MarkdownProcessor(),
        ]
        self.loaded_documents: Dict[str, Document] = {}
    
    def _get_processor(self, file_path: Path) -> Optional[BaseProcessor]:
        """Get the appropriate processor for a file."""
        for processor in self.processors:
            if processor.can_process(file_path):
                return processor
        return None
    
    async def load_document(self, file_path: Path) -> Document:
        """Load and process a document."""
        processor = self._get_processor(file_path)
        if processor is None:
            raise ValueError(f"No processor available for file: {file_path}")
        
        document = await processor.process(file_path)
        self.loaded_documents[str(file_path)] = document
        return document
    
    async def get_document_outline(self, file_path: Path) -> List[DocumentSection]:
        """Get the outline/table of contents for a document."""
        if str(file_path) not in self.loaded_documents:
            await self.load_document(file_path)
        
        document = self.loaded_documents[str(file_path)]
        return document.sections
    
    async def get_section_content(
        self, file_path: Path, section_id: str
    ) -> Optional[DocumentSection]:
        """Get the content of a specific section."""
        if str(file_path) not in self.loaded_documents:
            await self.load_document(file_path)
        
        document = self.loaded_documents[str(file_path)]
        return document.get_section(section_id)
    
    async def search_document(
        self, file_path: Path, query: str
    ) -> List[DocumentSection]:
        """Search for content within a document."""
        if str(file_path) not in self.loaded_documents:
            await self.load_document(file_path)
        
        document = self.loaded_documents[str(file_path)]
        processor = self._get_processor(file_path)
        if processor is None:
            return []
        
        return await processor.search(document, query)