"""Base document processor interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import Document, DocumentSection


class BaseProcessor(ABC):
    """Base class for document processors."""
    
    @abstractmethod
    def can_process(self, file_path: Path) -> bool:
        """Check if this processor can handle the given file type."""
        pass
    
    @abstractmethod
    async def process(self, file_path: Path) -> Document:
        """Process a document and return structured data."""
        pass
    
    @abstractmethod
    async def extract_section(
        self, document: Document, section_id: str
    ) -> Optional[DocumentSection]:
        """Extract a specific section from the document."""
        pass
    
    @abstractmethod
    async def search(self, document: Document, query: str) -> List[DocumentSection]:
        """Search for content within the document."""
        pass