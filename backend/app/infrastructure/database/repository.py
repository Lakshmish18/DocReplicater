"""
Document Repository
Database operations for documents.
"""

from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .models import (
    DocumentModel, DesignSchemaModel, ContentSectionModel, 
    OCRMetadataModel, DocumentVersionModel
)
from app.domain.entities.document import Document, DocumentStatus
from app.domain.entities.design_schema import DesignSchema
from app.domain.entities.content_section import ContentSection
from app.domain.entities.ocr_metadata import OCRMetadata
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentRepository:
    """
    Repository for document persistence operations.
    
    Handles all database operations for documents and related entities.
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    # Document operations
    
    def create_document(self, document: Document) -> DocumentModel:
        """Create a new document record."""
        db_document = DocumentModel(
            id=document.id,
            user_id=document.user_id,
            original_filename=document.original_filename,
            file_extension=document.file_extension,
            file_size=document.file_size,
            mime_type=document.mime_type,
            storage_path=document.storage_path,
            document_type=document.document_type,
            status=document.status,
            page_count=document.page_count,
            has_images=document.has_images,
            has_tables=document.has_tables,
            is_scanned=document.is_scanned,
        )
        
        self.session.add(db_document)
        self.session.commit()
        self.session.refresh(db_document)
        
        return db_document
    
    def get_document(self, document_id: UUID) -> Optional[DocumentModel]:
        """Get document by ID."""
        return self.session.query(DocumentModel).filter(
            DocumentModel.id == document_id
        ).first()
    
    def get_document_with_relations(self, document_id: UUID) -> Optional[DocumentModel]:
        """Get document with all relations loaded."""
        return self.session.query(DocumentModel).filter(
            DocumentModel.id == document_id
        ).first()
    
    def list_documents(
        self, 
        user_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[DocumentModel], int]:
        """List documents with pagination."""
        query = self.session.query(DocumentModel).filter(
            DocumentModel.status != DocumentStatus.DELETED
        )
        
        if user_id:
            query = query.filter(DocumentModel.user_id == user_id)
        
        total = query.count()
        
        documents = query.order_by(
            desc(DocumentModel.created_at)
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        return documents, total
    
    def update_document(self, document: Document) -> DocumentModel:
        """Update document record."""
        db_document = self.get_document(document.id)
        if not db_document:
            raise ValueError(f"Document {document.id} not found")
        
        db_document.status = document.status
        db_document.page_count = document.page_count
        db_document.has_images = document.has_images
        db_document.has_tables = document.has_tables
        db_document.is_scanned = document.is_scanned
        db_document.error_message = document.error_message
        db_document.processing_warnings = document.processing_warnings
        db_document.processed_at = document.processed_at
        
        self.session.commit()
        self.session.refresh(db_document)
        
        return db_document
    
    def delete_document(self, document_id: UUID) -> bool:
        """Soft delete document."""
        db_document = self.get_document(document_id)
        if not db_document:
            return False
        
        db_document.status = DocumentStatus.DELETED
        self.session.commit()
        
        return True
    
    # Design schema operations
    
    def create_design_schema(
        self, 
        schema: DesignSchema, 
        document_id: UUID
    ) -> DesignSchemaModel:
        """Create design schema record."""
        db_schema = DesignSchemaModel(
            id=schema.id,
            document_id=document_id,
            page_setup=schema.page_setup.to_dict(),
            style_tokens={k: v.to_dict() for k, v in schema.style_tokens.items()},
            default_font_family=schema.default_font_family,
            default_font_size=schema.default_font_size,
            default_line_spacing=schema.default_line_spacing,
            heading_hierarchy=schema.heading_hierarchy,
            color_palette=schema.color_palette,
            table_style=schema.table_style,
            bullet_style=schema.bullet_style,
            numbered_style=schema.numbered_style,
            extracted_from=schema.extracted_from,
            confidence_score=schema.confidence_score,
        )
        
        self.session.add(db_schema)
        self.session.commit()
        
        return db_schema
    
    def get_design_schema(self, document_id: UUID) -> Optional[DesignSchemaModel]:
        """Get design schema for document."""
        return self.session.query(DesignSchemaModel).filter(
            DesignSchemaModel.document_id == document_id
        ).first()
    
    # Content section operations
    
    def create_sections(
        self, 
        sections: List[ContentSection], 
        document_id: UUID
    ) -> List[ContentSectionModel]:
        """Create multiple content section records."""
        db_sections = []
        
        for section in sections:
            db_section = ContentSectionModel(
                id=section.id,
                document_id=document_id,
                order_index=section.order_index,
                page_number=section.page_number,
                section_type=section.section_type,
                content=section.content,
                original_content=section.original_content,
                style_token=section.style_token,
                editable=section.editable,
                ai_enabled=section.ai_enabled,
                list_items=section.list_items,
                list_level=section.list_level,
                table_data=section.table_data,
                table_headers=section.table_headers,
                image_path=section.image_path,
                image_alt_text=section.image_alt_text,
                ocr_confidence=section.ocr_confidence,
                bounding_box=section.bounding_box,
            )
            db_sections.append(db_section)
            self.session.add(db_section)
        
        self.session.commit()
        return db_sections
    
    def get_sections(self, document_id: UUID) -> List[ContentSectionModel]:
        """Get all sections for document."""
        return self.session.query(ContentSectionModel).filter(
            ContentSectionModel.document_id == document_id
        ).order_by(ContentSectionModel.order_index).all()
    
    def update_section(self, section: ContentSection) -> ContentSectionModel:
        """Update a section."""
        db_section = self.session.query(ContentSectionModel).filter(
            ContentSectionModel.id == section.id
        ).first()
        
        if not db_section:
            raise ValueError(f"Section {section.id} not found")
        
        db_section.content = section.content
        db_section.list_items = section.list_items
        db_section.table_data = section.table_data
        db_section.ai_generated = section.ai_generated
        db_section.ai_prompt_used = section.ai_prompt_used
        db_section.version = section.version
        db_section.last_edited_at = section.last_edited_at
        
        self.session.commit()
        self.session.refresh(db_section)
        
        return db_section
    
    # OCR metadata operations
    
    def create_ocr_metadata(
        self, 
        metadata: OCRMetadata, 
        document_id: UUID
    ) -> OCRMetadataModel:
        """Create OCR metadata record."""
        db_metadata = OCRMetadataModel(
            id=metadata.id,
            document_id=document_id,
            engine_name=metadata.engine_name,
            engine_version=metadata.engine_version,
            language=metadata.language,
            dpi=metadata.dpi,
            preprocessing_applied=metadata.preprocessing_applied,
            blocks=[b.to_dict() for b in metadata.blocks],
            total_pages=metadata.total_pages,
            average_confidence=metadata.average_confidence,
            low_confidence_blocks=metadata.low_confidence_blocks,
            page_dimensions=metadata.page_dimensions,
            detected_columns=metadata.detected_columns,
            detected_margins=metadata.detected_margins,
            processing_time_seconds=metadata.processing_time_seconds,
        )
        
        self.session.add(db_metadata)
        self.session.commit()
        
        return db_metadata
    
    def get_ocr_metadata(self, document_id: UUID) -> Optional[OCRMetadataModel]:
        """Get OCR metadata for document."""
        return self.session.query(OCRMetadataModel).filter(
            OCRMetadataModel.document_id == document_id
        ).first()
    
    # Version operations
    
    def create_version(
        self,
        document_id: UUID,
        version_number: int,
        sections: List[ContentSection],
        description: str = None,
        user_id: UUID = None
    ) -> DocumentVersionModel:
        """Create a document version snapshot."""
        db_version = DocumentVersionModel(
            document_id=document_id,
            version_number=version_number,
            sections_snapshot=[s.to_dict() for s in sections],
            change_description=description,
            changed_by=user_id,
        )
        
        self.session.add(db_version)
        self.session.commit()
        
        return db_version
    
    def get_versions(self, document_id: UUID) -> List[DocumentVersionModel]:
        """Get all versions for a document."""
        return self.session.query(DocumentVersionModel).filter(
            DocumentVersionModel.document_id == document_id
        ).order_by(desc(DocumentVersionModel.version_number)).all()

