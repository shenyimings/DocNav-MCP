"""Data models for document representation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DocumentSection:
    """Represents a section within a document."""
    
    id: str
    title: str
    content: str
    level: int
    start_line: int
    end_line: int
    parent_id: Optional[str] = None
    children: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        """Initialize default values."""
        if self.children is None:
            self.children = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Document:
    """Represents a processed document."""
    
    file_path: Path
    title: str
    content: str
    sections: List[DocumentSection]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}
    
    def get_section(self, section_id: str) -> Optional[DocumentSection]:
        """Get a section by ID."""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None
    
    def get_sections_by_level(self, level: int) -> List[DocumentSection]:
        """Get all sections at a specific level."""
        return [section for section in self.sections if section.level == level]