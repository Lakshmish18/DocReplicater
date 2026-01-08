"""Document Pydantic Models."""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentModel(BaseModel):
    """Document representation."""
    id: str
    user_id: Optional[str] = None
    original_filename: str
    file_extension: str
    file_size: int
    mime_type: str
    document_type: str
    status: str
    page_count: int = 0
    has_images: bool = False
    has_tables: bool = False
    is_scanned: bool = False
    error_message: Optional[str] = None
    processing_warnings: List[str] = []
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    version: int = 1
    
    class Config:
        from_attributes = True


class DocumentCreateModel(BaseModel):
    """Model for document upload response."""
    original_filename: str
    file_size: int
    mime_type: str


class DocumentResponseModel(BaseModel):
    """Complete document response with design and sections."""
    document: DocumentModel
    design_schema: Optional[dict] = None
    sections: List[dict] = []
    ocr_metadata: Optional[dict] = None
    
    class Config:
        from_attributes = True


class DocumentListResponseModel(BaseModel):
    """Response for listing documents."""
    documents: List[DocumentModel]
    total: int
    page: int
    page_size: int
    
    class Config:
        from_attributes = True


class ExportRequestModel(BaseModel):
    """Model for document export request."""
    format: str = Field("docx", description="Export format: docx or pdf")
    include_original_formatting: bool = True
    
    class Config:
        from_attributes = True

