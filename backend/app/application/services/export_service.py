"""
Export Service
Handles document export operations with 100% fidelity.

Uses the enhanced DOCX generator for maximum formatting preservation.
"""

from typing import Optional
from uuid import UUID
from pathlib import Path

from app.domain.entities.design_schema import DesignSchema
from app.domain.entities.content_section import ContentSection
from app.infrastructure.generators import DocxGenerator, PDFGenerator, EnhancedDocxGenerator
from app.infrastructure.storage import FileStorage
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ExportService:
    """
    Service for document export operations with 100% fidelity.
    
    Responsibilities:
    - Generate DOCX from schema + sections (with full formatting)
    - Generate PDF from schema + sections
    - Manage export files
    
    Uses template-based regeneration when original DOCX is available
    for maximum formatting fidelity.
    """
    
    def __init__(self, document_service):
        self.document_service = document_service
        self.storage = FileStorage()
    
    def export_docx(self, document_id: UUID) -> Optional[Path]:
        """
        Export document as DOCX with 100% fidelity.
        
        Uses enhanced generator with template-based approach when
        original DOCX is available.
        
        Returns:
            Path to generated DOCX file
        """
        # Get enhanced data if available
        design_data = self.document_service._design_data.get(document_id)
        sections_data = self.document_service._sections_data.get(document_id)
        original_docx_path = self.document_service._original_docx_paths.get(document_id)
        
        # Get output path
        output_path = self.storage.get_output_path(document_id, "docx")
        
        if design_data and original_docx_path:
            # Use enhanced generator for 100% fidelity
            logger.info(f"Using enhanced DOCX generator for {document_id}")
            
            # Get the CURRENT sections (with user edits)
            sections = self.document_service.get_sections(document_id)
            
            # Build a map of content changes: original_content -> new_content
            content_changes = {}
            for section in sections:
                if section.content != section.original_content:
                    content_changes[section.original_content] = section.content
                    logger.info(f"Content change: '{section.original_content[:30]}...' -> '{section.content[:30]}...'")
            
            # Also build a sections data list from the actual sections
            updated_sections_data = []
            for section in sections:
                section_data = {
                    "id": str(section.id),
                    "order_index": section.order_index,
                    "section_type": section.section_type.value,
                    "content": section.content,
                    "original_content": section.original_content,
                    "style_token": section.style_token,
                }
                updated_sections_data.append(section_data)
            
            logger.info(f"Exporting with {len(sections)} sections, {len(content_changes)} content changes")
            
            generator = EnhancedDocxGenerator(design_data, original_docx_path)
            result_path = generator.generate_with_replacements(
                updated_sections_data, 
                content_changes,
                str(output_path)
            )
            
            logger.info(f"Exported DOCX with 100% fidelity: {result_path}")
            return Path(result_path)
        
        # Fallback to standard generator
        design_schema = self.document_service.get_design_schema(document_id)
        sections = self.document_service.get_sections(document_id)
        
        if not design_schema or not sections:
            logger.error(f"Cannot export: missing schema or sections for {document_id}")
            return None
        
        generator = DocxGenerator(design_schema)
        result_path = generator.generate(sections, str(output_path))
        
        logger.info(f"Exported DOCX: {result_path}")
        return Path(result_path)
    
    def export_pdf(self, document_id: UUID) -> Optional[Path]:
        """
        Export document as PDF.
        
        Merges design schema with current content sections.
        
        Returns:
            Path to generated PDF file
        """
        design_schema = self.document_service.get_design_schema(document_id)
        sections = self.document_service.get_sections(document_id)
        
        if not design_schema or not sections:
            logger.error(f"Cannot export: missing schema or sections for {document_id}")
            return None
        
        # Get output path
        output_path = self.storage.get_output_path(document_id, "pdf")
        
        # Generate document
        generator = PDFGenerator(design_schema)
        result_path = generator.generate(sections, str(output_path))
        
        logger.info(f"Exported PDF: {result_path}")
        return Path(result_path)
    
    def export(self, document_id: UUID, format: str) -> Optional[Path]:
        """
        Export document in specified format.
        
        Args:
            document_id: Document UUID
            format: 'docx' or 'pdf'
            
        Returns:
            Path to generated file
        """
        if format.lower() == "docx":
            return self.export_docx(document_id)
        elif format.lower() == "pdf":
            return self.export_pdf(document_id)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_export_path(self, document_id: UUID, format: str) -> Optional[Path]:
        """Get path to existing export file."""
        path = self.storage.get_output_path(document_id, format)
        return path if path.exists() else None
    
    def delete_exports(self, document_id: UUID) -> int:
        """Delete all export files for a document."""
        deleted = 0
        
        for format in ["docx", "pdf"]:
            path = self.storage.get_output_path(document_id, format)
            if self.storage.delete_file(path):
                deleted += 1
        
        return deleted

