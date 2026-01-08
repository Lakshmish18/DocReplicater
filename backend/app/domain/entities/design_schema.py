"""
Design Schema Entity
Immutable design representation extracted from documents.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4


class FontWeight(str, Enum):
    """Font weight classification."""
    LIGHT = "light"
    NORMAL = "normal"
    MEDIUM = "medium"
    SEMIBOLD = "semibold"
    BOLD = "bold"
    EXTRABOLD = "extrabold"


class TextAlignment(str, Enum):
    """Text alignment options."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


@dataclass(frozen=True)
class FontStyle:
    """Immutable font style definition."""
    family: str = "Arial"
    size: float = 12.0
    weight: FontWeight = FontWeight.NORMAL
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    color: str = "#000000"
    background_color: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "family": self.family,
            "size": self.size,
            "weight": self.weight.value,
            "italic": self.italic,
            "underline": self.underline,
            "strikethrough": self.strikethrough,
            "color": self.color,
            "background_color": self.background_color,
        }


@dataclass(frozen=True)
class PageSetup:
    """Immutable page setup configuration."""
    width: float = 8.5  # inches
    height: float = 11.0  # inches
    orientation: str = "portrait"
    margin_top: float = 1.0
    margin_bottom: float = 1.0
    margin_left: float = 1.0
    margin_right: float = 1.0
    columns: int = 1
    column_spacing: float = 0.5
    
    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "orientation": self.orientation,
            "margin_top": self.margin_top,
            "margin_bottom": self.margin_bottom,
            "margin_left": self.margin_left,
            "margin_right": self.margin_right,
            "columns": self.columns,
            "column_spacing": self.column_spacing,
        }


@dataclass(frozen=True)
class StyleToken:
    """
    Immutable style token representing a reusable style.
    Used for consistent formatting across sections.
    """
    name: str  # e.g., "H1", "H2", "Body", "Caption"
    font: FontStyle
    alignment: TextAlignment = TextAlignment.LEFT
    line_spacing: float = 1.15
    space_before: float = 0.0  # points
    space_after: float = 0.0  # points
    first_line_indent: float = 0.0  # inches
    left_indent: float = 0.0
    right_indent: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "font": self.font.to_dict(),
            "alignment": self.alignment.value,
            "line_spacing": self.line_spacing,
            "space_before": self.space_before,
            "space_after": self.space_after,
            "first_line_indent": self.first_line_indent,
            "left_indent": self.left_indent,
            "right_indent": self.right_indent,
        }


@dataclass
class DesignSchema:
    """
    Complete design schema for a document.
    This schema is IMMUTABLE after creation - design cannot be modified.
    Only content sections can be edited.
    """
    
    id: UUID = field(default_factory=uuid4)
    document_id: UUID = field(default_factory=uuid4)
    
    # Page configuration
    page_setup: PageSetup = field(default_factory=PageSetup)
    
    # Style tokens - mapped by name
    style_tokens: Dict[str, StyleToken] = field(default_factory=dict)
    
    # Document-level styles
    default_font_family: str = "Arial"
    default_font_size: float = 12.0
    default_line_spacing: float = 1.15
    
    # Heading hierarchy (inferred from document)
    heading_hierarchy: List[str] = field(default_factory=list)  # ["H1", "H2", "H3"]
    
    # Color palette extracted from document
    color_palette: List[str] = field(default_factory=list)
    
    # Table styles
    table_style: Optional[dict] = None
    
    # List styles
    bullet_style: Optional[dict] = None
    numbered_style: Optional[dict] = None
    
    # Metadata
    extracted_from: str = "unknown"  # "docx", "pdf", "ocr"
    confidence_score: float = 1.0  # For OCR-extracted schemas
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Immutability flag
    _locked: bool = field(default=False, repr=False)
    
    def lock(self) -> None:
        """Lock the schema to prevent modifications."""
        object.__setattr__(self, '_locked', True)
    
    def is_locked(self) -> bool:
        """Check if schema is locked."""
        return self._locked
    
    def get_style_token(self, name: str) -> Optional[StyleToken]:
        """Get a style token by name."""
        return self.style_tokens.get(name)
    
    def add_style_token(self, token: StyleToken) -> None:
        """Add a style token (only if not locked)."""
        if self._locked:
            raise ValueError("Cannot modify locked design schema")
        self.style_tokens[token.name] = token
    
    @classmethod
    def create_default_tokens(cls) -> Dict[str, StyleToken]:
        """Create default style tokens."""
        return {
            "Title": StyleToken(
                name="Title",
                font=FontStyle(family="Arial", size=26, weight=FontWeight.BOLD),
                alignment=TextAlignment.CENTER,
                space_after=24
            ),
            "H1": StyleToken(
                name="H1",
                font=FontStyle(family="Arial", size=20, weight=FontWeight.BOLD),
                space_before=18,
                space_after=12
            ),
            "H2": StyleToken(
                name="H2",
                font=FontStyle(family="Arial", size=16, weight=FontWeight.BOLD),
                space_before=14,
                space_after=8
            ),
            "H3": StyleToken(
                name="H3",
                font=FontStyle(family="Arial", size=14, weight=FontWeight.SEMIBOLD),
                space_before=12,
                space_after=6
            ),
            "Body": StyleToken(
                name="Body",
                font=FontStyle(family="Arial", size=12, weight=FontWeight.NORMAL),
                line_spacing=1.15,
                space_after=8
            ),
            "Caption": StyleToken(
                name="Caption",
                font=FontStyle(family="Arial", size=10, weight=FontWeight.NORMAL, italic=True),
                alignment=TextAlignment.CENTER
            ),
        }
    
    def to_dict(self) -> dict:
        """Convert schema to dictionary."""
        return {
            "id": str(self.id),
            "document_id": str(self.document_id),
            "page_setup": self.page_setup.to_dict(),
            "style_tokens": {k: v.to_dict() for k, v in self.style_tokens.items()},
            "default_font_family": self.default_font_family,
            "default_font_size": self.default_font_size,
            "default_line_spacing": self.default_line_spacing,
            "heading_hierarchy": self.heading_hierarchy,
            "color_palette": self.color_palette,
            "table_style": self.table_style,
            "bullet_style": self.bullet_style,
            "numbered_style": self.numbered_style,
            "extracted_from": self.extracted_from,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat(),
            "locked": self._locked,
        }

