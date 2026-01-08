"""
Content Section Entity
Represents editable content units within a document.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4


class SectionType(str, Enum):
    """Types of content sections."""
    TITLE = "title"
    HEADING_1 = "heading_1"
    HEADING_2 = "heading_2"
    HEADING_3 = "heading_3"
    PARAGRAPH = "paragraph"
    BULLET_LIST = "bullet_list"
    NUMBERED_LIST = "numbered_list"
    TABLE = "table"
    IMAGE = "image"
    CAPTION = "caption"
    QUOTE = "quote"
    CODE = "code"
    HEADER = "header"
    FOOTER = "footer"
    PAGE_BREAK = "page_break"
    UNKNOWN = "unknown"


@dataclass
class ContentSection:
    """
    Represents an editable content section within a document.
    
    Sections are the ONLY editable units. Each section is linked to a
    style token from the design schema.
    """
    
    id: UUID = field(default_factory=uuid4)
    document_id: UUID = field(default_factory=uuid4)
    
    # Position and ordering
    order_index: int = 0
    page_number: int = 1
    
    # Content
    section_type: SectionType = SectionType.PARAGRAPH
    content: str = ""
    original_content: str = ""  # Preserved for comparison
    
    # Style reference (links to DesignSchema.style_tokens)
    style_token: str = "Body"
    
    # Editability flags
    editable: bool = True
    ai_enabled: bool = True
    
    # For lists
    list_items: List[str] = field(default_factory=list)
    list_level: int = 0
    
    # For tables
    table_data: Optional[List[List[str]]] = None
    table_headers: Optional[List[str]] = None
    
    # For images
    image_path: Optional[str] = None
    image_alt_text: Optional[str] = None
    
    # OCR-specific metadata
    ocr_confidence: Optional[float] = None
    bounding_box: Optional[Dict[str, float]] = None  # {x, y, width, height}
    
    # AI generation metadata
    ai_generated: bool = False
    ai_prompt_used: Optional[str] = None
    
    # Version tracking
    version: int = 1
    last_edited_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def update_content(self, new_content: str, ai_generated: bool = False) -> None:
        """Update section content."""
        if not self.editable:
            raise ValueError("Section is not editable")
        
        self.content = new_content
        self.ai_generated = ai_generated
        self.version += 1
        self.last_edited_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def reset_to_original(self) -> None:
        """Reset content to original."""
        self.content = self.original_content
        self.ai_generated = False
        self.version += 1
        self.updated_at = datetime.utcnow()
    
    def is_empty(self) -> bool:
        """Check if section has no content."""
        if self.section_type == SectionType.TABLE:
            return self.table_data is None or len(self.table_data) == 0
        if self.section_type in [SectionType.BULLET_LIST, SectionType.NUMBERED_LIST]:
            return len(self.list_items) == 0
        return not self.content.strip()
    
    def get_word_count(self) -> int:
        """Get word count of content."""
        if self.section_type in [SectionType.BULLET_LIST, SectionType.NUMBERED_LIST]:
            return sum(len(item.split()) for item in self.list_items)
        return len(self.content.split())
    
    def get_character_count(self) -> int:
        """Get character count of content."""
        if self.section_type in [SectionType.BULLET_LIST, SectionType.NUMBERED_LIST]:
            return sum(len(item) for item in self.list_items)
        return len(self.content)
    
    @classmethod
    def from_ocr_block(cls, block: "OCRBlock", document_id: UUID, order_index: int) -> "ContentSection":
        """Create a content section from an OCR block."""
        from .ocr_metadata import OCRBlock
        
        # Infer section type from OCR block characteristics
        section_type = SectionType.PARAGRAPH
        style_token = "Body"
        
        # Simple heuristics for type detection
        if block.font_size and block.font_size >= 18:
            section_type = SectionType.HEADING_1
            style_token = "H1"
        elif block.font_size and block.font_size >= 14:
            section_type = SectionType.HEADING_2
            style_token = "H2"
        elif block.is_bold and block.font_size and block.font_size >= 12:
            section_type = SectionType.HEADING_3
            style_token = "H3"
        
        return cls(
            document_id=document_id,
            order_index=order_index,
            page_number=block.page_number,
            section_type=section_type,
            content=block.text,
            original_content=block.text,
            style_token=style_token,
            ocr_confidence=block.confidence,
            bounding_box={
                "x": block.bounding_box.x,
                "y": block.bounding_box.y,
                "width": block.bounding_box.width,
                "height": block.bounding_box.height,
            } if block.bounding_box else None,
        )
    
    def to_dict(self) -> dict:
        """Convert section to dictionary."""
        return {
            "id": str(self.id),
            "document_id": str(self.document_id),
            "order_index": self.order_index,
            "page_number": self.page_number,
            "section_type": self.section_type.value,
            "content": self.content,
            "original_content": self.original_content,
            "style_token": self.style_token,
            "editable": self.editable,
            "ai_enabled": self.ai_enabled,
            "list_items": self.list_items,
            "list_level": self.list_level,
            "table_data": self.table_data,
            "table_headers": self.table_headers,
            "image_path": self.image_path,
            "image_alt_text": self.image_alt_text,
            "ocr_confidence": self.ocr_confidence,
            "bounding_box": self.bounding_box,
            "ai_generated": self.ai_generated,
            "version": self.version,
            "word_count": self.get_word_count(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

