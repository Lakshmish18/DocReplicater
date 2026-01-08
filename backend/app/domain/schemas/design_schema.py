"""Design Schema Pydantic Models."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class FontStyleModel(BaseModel):
    """Font style configuration."""
    family: str = "Arial"
    size: float = 12.0
    weight: str = "normal"
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    color: str = "#000000"
    background_color: Optional[str] = None
    
    class Config:
        from_attributes = True


class PageSetupModel(BaseModel):
    """Page setup configuration."""
    width: float = Field(default=8.5, description="Page width in inches")
    height: float = Field(default=11.0, description="Page height in inches")
    orientation: str = "portrait"
    margin_top: float = 1.0
    margin_bottom: float = 1.0
    margin_left: float = 1.0
    margin_right: float = 1.0
    columns: int = 1
    column_spacing: float = 0.5
    
    class Config:
        from_attributes = True


class StyleTokenModel(BaseModel):
    """Style token for consistent formatting."""
    name: str = Field(..., description="Token name (e.g., H1, Body)")
    font: FontStyleModel
    alignment: str = "left"
    line_spacing: float = 1.15
    space_before: float = 0.0
    space_after: float = 0.0
    first_line_indent: float = 0.0
    left_indent: float = 0.0
    right_indent: float = 0.0
    
    class Config:
        from_attributes = True


class DesignSchemaModel(BaseModel):
    """Complete design schema for a document."""
    id: str
    document_id: str
    page_setup: PageSetupModel
    style_tokens: Dict[str, StyleTokenModel]
    default_font_family: str = "Arial"
    default_font_size: float = 12.0
    default_line_spacing: float = 1.15
    heading_hierarchy: List[str] = []
    color_palette: List[str] = []
    table_style: Optional[dict] = None
    bullet_style: Optional[dict] = None
    numbered_style: Optional[dict] = None
    extracted_from: str = "unknown"
    confidence_score: float = 1.0
    created_at: datetime
    locked: bool = False
    
    class Config:
        from_attributes = True


class DesignSchemaCreateModel(BaseModel):
    """Model for creating a design schema."""
    page_setup: Optional[PageSetupModel] = None
    style_tokens: Optional[Dict[str, StyleTokenModel]] = None
    default_font_family: str = "Arial"
    default_font_size: float = 12.0

