"""Base document processor interface compatible with DocumentNode structure."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import Document, DocumentNode, SearchResult


class BaseProcessor(ABC):
    """Base class for document processors using DocumentNode tree structure.
    
    Provides interface for document processing that works with the new
    DOM-like DocumentNode structure for better navigation and analysis.
    """
    
    @abstractmethod
    def can_process(self, file_path: Path) -> bool:
        """Check if this processor can handle the given file type.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if this processor can handle the file type
        """
        pass
    
    @abstractmethod
    async def process(self, file_path: Path) -> Document:
        """Process a document and return structured Document with tree structure.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Document with populated DocumentNode tree structure
        """
        pass
    
    @abstractmethod
    async def extract_node(
        self, document: Document, node_id: str
    ) -> Optional[DocumentNode]:
        """Extract a specific node from the document tree.
        
        Args:
            document: Document containing the node tree
            node_id: ID of the node to extract
            
        Returns:
            DocumentNode if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def search(self, document: Document, query: str) -> List[SearchResult]:
        """Search for content within the document tree structure.
        
        Args:
            document: Document to search within
            query: Search query string
            
        Returns:
            List of SearchResult objects with matches
        """
        pass
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions.
        
        Returns:
            List of file extensions this processor supports
        """
        return []
    
    def get_processor_info(self) -> Dict[str, Any]:
        """Get information about this processor.
        
        Returns:
            Dictionary with processor metadata
        """
        return {
            "name": self.__class__.__name__,
            "supported_extensions": self.get_supported_extensions(),
            "features": ["parsing", "search", "navigation"]
        }