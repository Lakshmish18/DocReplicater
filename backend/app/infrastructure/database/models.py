"""
Database Models
SQLAlchemy models for persistence.
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, 
    ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.domain.entities.document import DocumentType, DocumentStatus
from app.domain.entities.content_section import SectionType

Base = declarative_base()


class UserModel(Base):
    """User model for authentication and document ownership."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("DocumentModel", back_populates="user")


class DocumentModel(Base):
    """Document model for storing uploaded documents."""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # File information
    original_filename = Column(String(255), nullable=False)
    file_extension = Column(String(10), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100))
    storage_path = Column(String(500))
    
    # Classification
    document_type = Column(SQLEnum(DocumentType), default=DocumentType.UNKNOWN)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADING, index=True)
    
    # Processing metadata
    page_count = Column(Integer, default=0)
    has_images = Column(Boolean, default=False)
    has_tables = Column(Boolean, default=False)
    is_scanned = Column(Boolean, default=False)
    
    # Error handling
    error_message = Column(Text)
    processing_warnings = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Version control
    version = Column(Integer, default=1)
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    
    # Relationships
    user = relationship("UserModel", back_populates="documents")
    design_schema = relationship("DesignSchemaModel", back_populates="document", uselist=False)
    sections = relationship("ContentSectionModel", back_populates="document", order_by="ContentSectionModel.order_index")
    ocr_metadata = relationship("OCRMetadataModel", back_populates="document", uselist=False)
    versions = relationship("DocumentModel")


class DesignSchemaModel(Base):
    """Design schema model - immutable after creation."""
    __tablename__ = "design_schemas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, unique=True)
    
    # Page setup (stored as JSON)
    page_setup = Column(JSON, nullable=False)
    
    # Style tokens (stored as JSON)
    style_tokens = Column(JSON, nullable=False)
    
    # Defaults
    default_font_family = Column(String(100), default="Arial")
    default_font_size = Column(Float, default=12.0)
    default_line_spacing = Column(Float, default=1.15)
    
    # Document structure
    heading_hierarchy = Column(JSON, default=list)
    color_palette = Column(JSON, default=list)
    
    # Optional styles
    table_style = Column(JSON)
    bullet_style = Column(JSON)
    numbered_style = Column(JSON)
    
    # Metadata
    extracted_from = Column(String(50), default="unknown")
    confidence_score = Column(Float, default=1.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("DocumentModel", back_populates="design_schema")


class ContentSectionModel(Base):
    """Content section model - editable content units."""
    __tablename__ = "content_sections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    
    # Position
    order_index = Column(Integer, nullable=False, index=True)
    page_number = Column(Integer, default=1)
    
    # Content
    section_type = Column(SQLEnum(SectionType), default=SectionType.PARAGRAPH)
    content = Column(Text, default="")
    original_content = Column(Text, default="")
    
    # Style reference
    style_token = Column(String(50), default="Body")
    
    # Editability
    editable = Column(Boolean, default=True)
    ai_enabled = Column(Boolean, default=True)
    
    # List data
    list_items = Column(JSON, default=list)
    list_level = Column(Integer, default=0)
    
    # Table data
    table_data = Column(JSON)
    table_headers = Column(JSON)
    
    # Image data
    image_path = Column(String(500))
    image_alt_text = Column(String(500))
    
    # OCR metadata
    ocr_confidence = Column(Float)
    bounding_box = Column(JSON)
    
    # AI metadata
    ai_generated = Column(Boolean, default=False)
    ai_prompt_used = Column(Text)
    
    # Version tracking
    version = Column(Integer, default=1)
    last_edited_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = relationship("DocumentModel", back_populates="sections")


class OCRMetadataModel(Base):
    """OCR metadata model for scanned documents."""
    __tablename__ = "ocr_metadata"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, unique=True)
    
    # Engine info
    engine_name = Column(String(50), default="tesseract")
    engine_version = Column(String(50))
    language = Column(String(10), default="eng")
    
    # Processing info
    dpi = Column(Integer, default=300)
    preprocessing_applied = Column(JSON, default=list)
    
    # Results (blocks stored as JSON)
    blocks = Column(JSON, default=list)
    total_pages = Column(Integer, default=0)
    
    # Quality metrics
    average_confidence = Column(Float, default=0.0)
    low_confidence_blocks = Column(Integer, default=0)
    
    # Page dimensions
    page_dimensions = Column(JSON, default=dict)
    
    # Layout info
    detected_columns = Column(Integer, default=1)
    detected_margins = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processing_time_seconds = Column(Float, default=0.0)
    
    # Relationships
    document = relationship("DocumentModel", back_populates="ocr_metadata")


class DocumentVersionModel(Base):
    """Document version model for version history."""
    __tablename__ = "document_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    
    version_number = Column(Integer, nullable=False)
    
    # Snapshot of sections at this version
    sections_snapshot = Column(JSON, nullable=False)
    
    # Change info
    change_description = Column(String(500))
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

