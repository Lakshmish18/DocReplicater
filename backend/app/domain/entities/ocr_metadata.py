"""
OCR Metadata Entity
Stores OCR processing results and positional data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4


@dataclass
class BoundingBox:
    """Bounding box coordinates for OCR elements."""
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "BoundingBox":
        return cls(
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 0),
            height=data.get("height", 0),
        )
    
    def contains(self, other: "BoundingBox") -> bool:
        """Check if this box contains another box."""
        return (
            self.x <= other.x and
            self.y <= other.y and
            (self.x + self.width) >= (other.x + other.width) and
            (self.y + self.height) >= (other.y + other.height)
        )
    
    def overlaps(self, other: "BoundingBox") -> bool:
        """Check if this box overlaps with another."""
        return not (
            self.x + self.width < other.x or
            other.x + other.width < self.x or
            self.y + self.height < other.y or
            other.y + other.height < self.y
        )
    
    def merge(self, other: "BoundingBox") -> "BoundingBox":
        """Merge two bounding boxes into one that contains both."""
        x = min(self.x, other.x)
        y = min(self.y, other.y)
        max_x = max(self.x + self.width, other.x + other.width)
        max_y = max(self.y + self.height, other.y + other.height)
        return BoundingBox(x=x, y=y, width=max_x - x, height=max_y - y)


@dataclass
class OCRBlock:
    """
    Represents a text block extracted by OCR.
    Preserves positional and confidence information.
    """
    
    id: str = field(default_factory=lambda: str(uuid4()))
    
    # Content
    text: str = ""
    
    # Position
    bounding_box: Optional[BoundingBox] = None
    page_number: int = 1
    
    # OCR metrics
    confidence: float = 0.0  # 0-100
    
    # Inferred formatting (from OCR analysis)
    font_size: Optional[float] = None
    is_bold: bool = False
    is_italic: bool = False
    alignment: str = "left"
    
    # Block classification
    block_type: str = "text"  # text, image, table, separator
    
    # Relationships
    parent_block_id: Optional[str] = None
    child_block_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
            "page_number": self.page_number,
            "confidence": self.confidence,
            "font_size": self.font_size,
            "is_bold": self.is_bold,
            "is_italic": self.is_italic,
            "alignment": self.alignment,
            "block_type": self.block_type,
        }


@dataclass
class OCRMetadata:
    """
    Complete OCR metadata for a document.
    Stores all extracted information from OCR processing.
    """
    
    id: UUID = field(default_factory=uuid4)
    document_id: UUID = field(default_factory=uuid4)
    
    # OCR engine info
    engine_name: str = "tesseract"
    engine_version: str = ""
    language: str = "eng"
    
    # Processing info
    dpi: int = 300
    preprocessing_applied: List[str] = field(default_factory=list)
    
    # Results
    blocks: List[OCRBlock] = field(default_factory=list)
    total_pages: int = 0
    
    # Quality metrics
    average_confidence: float = 0.0
    low_confidence_blocks: int = 0
    
    # Page dimensions (per page)
    page_dimensions: Dict[int, Dict[str, float]] = field(default_factory=dict)
    
    # Inferred layout information
    detected_columns: int = 1
    detected_margins: Dict[str, float] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    processing_time_seconds: float = 0.0
    
    def add_block(self, block: OCRBlock) -> None:
        """Add an OCR block and update metrics."""
        self.blocks.append(block)
        self._update_metrics()
    
    def _update_metrics(self) -> None:
        """Update aggregate metrics."""
        if not self.blocks:
            return
        
        confidences = [b.confidence for b in self.blocks if b.confidence > 0]
        if confidences:
            self.average_confidence = sum(confidences) / len(confidences)
        
        self.low_confidence_blocks = sum(
            1 for b in self.blocks 
            if b.confidence < 60 and b.confidence > 0
        )
    
    def get_blocks_by_page(self, page_number: int) -> List[OCRBlock]:
        """Get all blocks for a specific page."""
        return [b for b in self.blocks if b.page_number == page_number]
    
    def get_blocks_sorted(self) -> List[OCRBlock]:
        """Get blocks sorted by page and position (top to bottom, left to right)."""
        return sorted(
            self.blocks,
            key=lambda b: (
                b.page_number,
                b.bounding_box.y if b.bounding_box else 0,
                b.bounding_box.x if b.bounding_box else 0,
            )
        )
    
    def get_quality_assessment(self) -> Dict[str, Any]:
        """Get OCR quality assessment."""
        return {
            "average_confidence": self.average_confidence,
            "low_confidence_blocks": self.low_confidence_blocks,
            "total_blocks": len(self.blocks),
            "quality_rating": (
                "high" if self.average_confidence >= 80 else
                "medium" if self.average_confidence >= 60 else
                "low"
            ),
            "warnings": self._generate_warnings(),
        }
    
    def _generate_warnings(self) -> List[str]:
        """Generate quality warnings."""
        warnings = []
        
        if self.average_confidence < 60:
            warnings.append("Low overall OCR confidence. Results may be inaccurate.")
        
        if self.low_confidence_blocks > len(self.blocks) * 0.3:
            warnings.append("Many blocks have low confidence. Consider rescanning.")
        
        if not self.blocks:
            warnings.append("No text blocks detected. Document may be empty or unreadable.")
        
        return warnings
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "document_id": str(self.document_id),
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "language": self.language,
            "dpi": self.dpi,
            "preprocessing_applied": self.preprocessing_applied,
            "blocks": [b.to_dict() for b in self.blocks],
            "total_pages": self.total_pages,
            "average_confidence": self.average_confidence,
            "low_confidence_blocks": self.low_confidence_blocks,
            "page_dimensions": self.page_dimensions,
            "detected_columns": self.detected_columns,
            "detected_margins": self.detected_margins,
            "created_at": self.created_at.isoformat(),
            "processing_time_seconds": self.processing_time_seconds,
            "quality_assessment": self.get_quality_assessment(),
        }

