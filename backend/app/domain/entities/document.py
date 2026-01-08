"""
Document Entity
Core document representation with metadata and relationships.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4


class DocumentType(str, Enum):
    """Document source type classification."""
    DOCX = "docx"
    PDF_TEXT = "pdf_text"
    PDF_SCANNED = "pdf_scanned"
    IMAGE = "image"
    UNKNOWN = "unknown"


class DocumentStatus(str, Enum):
    """Document processing status."""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    CONVERTING = "converting"  # Converting to DOCX format
    EXTRACTING_DESIGN = "extracting_design"
    RUNNING_OCR = "running_ocr"
    ANALYZING_LAYOUT = "analyzing_layout"
    READY = "ready"
    ERROR = "error"
    DELETED = "deleted"


@dataclass
class Document:
    """
    Core Document entity representing an uploaded document.
    
    This is the aggregate root for document-related operations.
    """
    
    id: UUID = field(default_factory=uuid4)
    user_id: Optional[UUID] = None
    
    # File information
    original_filename: str = ""
    file_extension: str = ""
    file_size: int = 0
    mime_type: str = ""
    storage_path: str = ""
    
    # Classification
    document_type: DocumentType = DocumentType.UNKNOWN
    status: DocumentStatus = DocumentStatus.UPLOADING
    
    # Processing metadata
    page_count: int = 0
    has_images: bool = False
    has_tables: bool = False
    is_scanned: bool = False
    
    # Processing results
    design_schema_id: Optional[UUID] = None
    ocr_metadata_id: Optional[UUID] = None
    
    # Error handling
    error_message: Optional[str] = None
    processing_warnings: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    # Version control
    version: int = 1
    parent_version_id: Optional[UUID] = None
    
    def mark_processing(self, status: DocumentStatus) -> None:
        """Update document processing status."""
        self.status = status
        self.updated_at = datetime.utcnow()
    
    def mark_ready(self) -> None:
        """Mark document as ready for editing."""
        self.status = DocumentStatus.READY
        self.processed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_error(self, message: str) -> None:
        """Mark document as having an error."""
        self.status = DocumentStatus.ERROR
        self.error_message = message
        self.updated_at = datetime.utcnow()
    
    def add_warning(self, warning: str) -> None:
        """Add a processing warning."""
        self.processing_warnings.append(warning)
    
    def is_ocr_required(self) -> bool:
        """Check if OCR processing is required."""
        return self.document_type in [DocumentType.PDF_SCANNED, DocumentType.IMAGE]
    
    def to_dict(self) -> dict:
        """Convert entity to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "original_filename": self.original_filename,
            "file_extension": self.file_extension,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "document_type": self.document_type.value,
            "status": self.status.value,
            "page_count": self.page_count,
            "has_images": self.has_images,
            "has_tables": self.has_tables,
            "is_scanned": self.is_scanned,
            "error_message": self.error_message,
            "processing_warnings": self.processing_warnings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "version": self.version,
        }

