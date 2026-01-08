"""Content Section Pydantic Models."""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class ContentSectionModel(BaseModel):
    """Content section representation."""
    id: str
    document_id: str
    order_index: int
    page_number: int = 1
    section_type: str
    content: str
    original_content: str
    style_token: str = "Body"
    editable: bool = True
    ai_enabled: bool = True
    list_items: List[str] = []
    list_level: int = 0
    table_data: Optional[List[List[str]]] = None
    table_headers: Optional[List[str]] = None
    image_path: Optional[str] = None
    image_alt_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    bounding_box: Optional[Dict[str, float]] = None
    ai_generated: bool = False
    version: int = 1
    word_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SectionUpdateModel(BaseModel):
    """Model for updating section content."""
    content: Optional[str] = Field(None, description="New content for the section")
    list_items: Optional[List[str]] = Field(None, description="List items for list sections")
    table_data: Optional[List[List[str]]] = Field(None, description="Table data for table sections")
    
    class Config:
        from_attributes = True


class AIGenerateModel(BaseModel):
    """Model for AI content generation request."""
    prompt: str = Field(..., description="User prompt for content generation")
    tone: Optional[str] = Field("professional", description="Desired tone")
    max_length: Optional[int] = Field(None, description="Maximum word count")
    context: Optional[str] = Field(None, description="Additional context")
    
    class Config:
        from_attributes = True


class SectionBatchUpdateModel(BaseModel):
    """Model for batch updating multiple sections."""
    sections: List[Dict[str, str]] = Field(
        ..., 
        description="List of {id, content} pairs"
    )

