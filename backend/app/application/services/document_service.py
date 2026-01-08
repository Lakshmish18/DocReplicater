"""
Document Service
Orchestrates document processing pipeline.

DOCX-First Architecture:
All uploaded documents are converted to DOCX format for maximum fidelity.
This ensures 100% design preservation during editing and export.
"""

from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID
from pathlib import Path
import asyncio

from app.domain.entities.document import Document, DocumentType, DocumentStatus
from app.domain.entities.design_schema import DesignSchema
from app.domain.entities.content_section import ContentSection
from app.domain.entities.ocr_metadata import OCRMetadata
from app.infrastructure.parsers import FileClassifier, DocxParser, PDFParser, EnhancedDocxParser
from app.infrastructure.ocr import OCREngine
from app.infrastructure.storage import FileStorage
from app.infrastructure.converters import ConversionService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentService:
    """
    Service for document processing operations.
    
    Responsibilities:
    - File classification and routing
    - Document processing pipeline orchestration
    - Design schema and section extraction
    """
    
    def __init__(self):
        self.storage = FileStorage()
        self.ocr_engine = OCREngine()
        self.conversion_service = ConversionService()
        
        # In-memory storage (replace with database in production)
        self._documents: Dict[UUID, Document] = {}
        self._design_schemas: Dict[UUID, DesignSchema] = {}
        self._sections: Dict[UUID, List[ContentSection]] = {}
        self._ocr_metadata: Dict[UUID, OCRMetadata] = {}
        
        # Enhanced data storage for 100% fidelity
        self._design_data: Dict[UUID, Dict[str, Any]] = {}  # Full design info
        self._sections_data: Dict[UUID, List[Dict[str, Any]]] = {}  # Full section data
        self._original_docx_paths: Dict[UUID, str] = {}  # For template-based regeneration
    
    async def process_upload(
        self, 
        content: bytes, 
        filename: str,
        user_id: Optional[UUID] = None
    ) -> Document:
        """
        Process an uploaded document through the DOCX-first pipeline.
        
        DOCX-First Pipeline:
        1. Save original file
        2. Classify document type
        3. Convert to DOCX if needed (PDF, images -> DOCX)
        4. Parse DOCX with enhanced parser for 100% fidelity
        5. Extract design schema and content sections
        
        Returns:
            Processed Document entity
        """
        # Create document entity
        document = Document(
            original_filename=filename,
            file_extension=Path(filename).suffix.lower(),
            file_size=len(content),
            user_id=user_id,
        )
        
        try:
            # Save original file
            file_path = self.storage.save_upload_sync(
                content, filename, document.id
            )
            document.storage_path = str(file_path)
            
            # Classify document
            document.mark_processing(DocumentStatus.PROCESSING)
            doc_type, metadata = FileClassifier.classify(str(file_path), content)
            document.document_type = doc_type
            document.mime_type = metadata.get("mime_type", "")
            document.page_count = metadata.get("page_count", 1)
            document.has_images = metadata.get("has_images", False)
            document.is_scanned = doc_type in [DocumentType.PDF_SCANNED, DocumentType.IMAGE]
            
            logger.info(f"Document classified as: {doc_type.value}")
            
            # DOCX-First: Convert non-DOCX to DOCX
            docx_path = str(file_path)
            if doc_type != DocumentType.DOCX:
                logger.info(f"Converting {doc_type.value} to DOCX for maximum fidelity")
                document.mark_processing(DocumentStatus.CONVERTING)
                
                conversion_result = self.conversion_service.convert_to_docx(
                    str(file_path), content,
                    output_dir=str(Path(file_path).parent)
                )
                
                if not conversion_result.success:
                    raise ValueError(f"Conversion failed: {conversion_result.error}")
                
                docx_path = conversion_result.output_path
                logger.info(f"Converted to DOCX: {docx_path}")
                
                # Store OCR metadata if applicable
                if doc_type in [DocumentType.PDF_SCANNED, DocumentType.IMAGE]:
                    # Run OCR separately to get metadata
                    try:
                        ocr_metadata, _, _ = self._process_ocr(document)
                        self._ocr_metadata[document.id] = ocr_metadata
                        document.ocr_metadata_id = ocr_metadata.id
                    except Exception as ocr_error:
                        logger.warning(f"OCR metadata extraction failed: {ocr_error}")
            
            # Store original DOCX path for template-based regeneration
            self._original_docx_paths[document.id] = docx_path
            
            # Parse DOCX with enhanced parser for 100% fidelity
            document.mark_processing(DocumentStatus.EXTRACTING_DESIGN)
            design_data, sections_data = self._process_docx_enhanced(docx_path, document.id)
            
            # Store enhanced data for regeneration
            self._design_data[document.id] = design_data
            self._sections_data[document.id] = sections_data
            
            # Create legacy DesignSchema and ContentSection objects for API compatibility
            design_schema, sections = self._create_legacy_objects(
                document.id, design_data, sections_data
            )
            
            # Store results
            self._design_schemas[document.id] = design_schema
            self._sections[document.id] = sections
            document.design_schema_id = design_schema.id
            
            # Mark complete
            document.mark_ready()
            document.page_count = max(
                document.page_count,
                max((s.page_number for s in sections), default=1)
            )
            
            # Store document
            self._documents[document.id] = document
            
            logger.info(
                f"Document processed successfully: {document.id}, "
                f"{len(sections)} sections (from {len(sections_data)} raw), 100% fidelity mode"
            )
            
            # Debug: log what sections have content
            for idx, section in enumerate(sections):
                content_preview = section.content[:50].replace("\n", " ") if section.content else "(empty)"
                logger.info(f"  Final section {idx}: type={section.section_type.value}, content='{content_preview}...'")
            
            return document
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            document.mark_error(str(e))
            self._documents[document.id] = document
            raise
    
    def _process_docx_enhanced(
        self, docx_path: str, document_id: UUID
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Process DOCX with enhanced parser for 100% fidelity."""
        parser = EnhancedDocxParser(docx_path)
        return parser.parse(document_id)
    
    def _create_legacy_objects(
        self, 
        document_id: UUID,
        design_data: Dict[str, Any],
        sections_data: List[Dict[str, Any]]
    ) -> Tuple[DesignSchema, List[ContentSection]]:
        """Create legacy DesignSchema and ContentSection objects for API compatibility."""
        from app.domain.entities.design_schema import PageSetup, StyleToken, FontStyle
        
        # Create DesignSchema
        page_setup_data = design_data.get("page_setup", {})
        page_setup = PageSetup(
            width=page_setup_data.get("page_width", 8.5),
            height=page_setup_data.get("page_height", 11.0),
            margin_top=page_setup_data.get("margin_top", 1.0),
            margin_bottom=page_setup_data.get("margin_bottom", 1.0),
            margin_left=page_setup_data.get("margin_left", 1.0),
            margin_right=page_setup_data.get("margin_right", 1.0),
        )
        
        # Create style tokens from styles
        style_tokens = {}
        for style_name, style_data in design_data.get("styles", {}).items():
            font_data = style_data.get("font", {})
            font_style = FontStyle(
                family=font_data.get("name") or "Arial",
                size=font_data.get("size") or 12.0,
            )
            style_tokens[style_name] = StyleToken(
                name=style_name,
                font=font_style,
            )
        
        design_schema = DesignSchema(
            document_id=document_id,
            page_setup=page_setup,
            style_tokens=style_tokens,
            extracted_from="docx_enhanced",
            confidence_score=1.0,
        )
        design_schema.lock()
        
        # Create ContentSection objects
        sections = []
        for section_data in sections_data:
            # Get content - check multiple sources
            content = section_data.get("content", "")
            
            # Also check runs for content if main content is empty
            if not content.strip() and section_data.get("runs"):
                run_texts = [r.get("text", "") for r in section_data.get("runs", [])]
                content = "".join(run_texts)
            
            # Skip truly empty sections (no content anywhere)
            if not content.strip():
                continue
                
            from app.domain.entities.content_section import SectionType
            
            section_type_str = section_data.get("section_type", "paragraph")
            try:
                section_type = SectionType(section_type_str)
            except:
                section_type = SectionType.PARAGRAPH
            
            section = ContentSection(
                document_id=document_id,
                order_index=section_data.get("order_index", 0),
                section_type=section_type,
                content=content,
                original_content=section_data.get("original_content", content),
                style_token=section_data.get("style_name", "Normal"),
                editable=section_data.get("editable", True),
                ai_enabled=section_data.get("ai_enabled", True),
            )
            sections.append(section)
        
        return design_schema, sections
    
    def _process_docx(self, document: Document) -> Tuple[DesignSchema, List[ContentSection]]:
        """Process DOCX document."""
        document.mark_processing(DocumentStatus.EXTRACTING_DESIGN)
        
        parser = DocxParser(document.storage_path)
        return parser.parse(document.id)
    
    def _process_pdf(self, document: Document) -> Tuple[DesignSchema, List[ContentSection]]:
        """Process text-based PDF."""
        document.mark_processing(DocumentStatus.EXTRACTING_DESIGN)
        
        parser = PDFParser(document.storage_path)
        return parser.parse(document.id)
    
    def _process_ocr(
        self, document: Document
    ) -> Tuple[OCRMetadata, DesignSchema, List[ContentSection]]:
        """Process scanned document with OCR."""
        document.mark_processing(DocumentStatus.RUNNING_OCR)
        
        is_pdf = document.document_type == DocumentType.PDF_SCANNED
        return self.ocr_engine.process_document(
            document.storage_path,
            document.id,
            is_pdf=is_pdf
        )
    
    def get_document(self, document_id: UUID) -> Optional[Document]:
        """Get document by ID."""
        return self._documents.get(document_id)
    
    def get_design_schema(self, document_id: UUID) -> Optional[DesignSchema]:
        """Get design schema for document."""
        return self._design_schemas.get(document_id)
    
    def get_sections(self, document_id: UUID) -> List[ContentSection]:
        """Get content sections for document."""
        return self._sections.get(document_id, [])
    
    def get_ocr_metadata(self, document_id: UUID) -> Optional[OCRMetadata]:
        """Get OCR metadata for document."""
        return self._ocr_metadata.get(document_id)
    
    def get_document_data(self, document_id: UUID) -> Optional[Dict[str, Any]]:
        """Get complete document data."""
        document = self.get_document(document_id)
        if not document:
            return None
        
        design_schema = self.get_design_schema(document_id)
        sections = self.get_sections(document_id)
        ocr_metadata = self.get_ocr_metadata(document_id)
        
        return {
            "document": document.to_dict(),
            "design_schema": design_schema.to_dict() if design_schema else None,
            "sections": [s.to_dict() for s in sections],
            "ocr_metadata": ocr_metadata.to_dict() if ocr_metadata else None,
        }
    
    def list_documents(
        self, 
        user_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Document], int]:
        """List documents with pagination."""
        documents = list(self._documents.values())
        
        if user_id:
            documents = [d for d in documents if d.user_id == user_id]
        
        # Filter out deleted
        documents = [d for d in documents if d.status != DocumentStatus.DELETED]
        
        # Sort by created_at descending
        documents.sort(key=lambda d: d.created_at, reverse=True)
        
        total = len(documents)
        start = (page - 1) * page_size
        end = start + page_size
        
        return documents[start:end], total
    
    def delete_document(self, document_id: UUID) -> bool:
        """Delete a document and its files."""
        document = self._documents.get(document_id)
        if not document:
            return False
        
        # Delete files
        self.storage.delete_document_files(document_id)
        
        # Mark as deleted
        document.status = DocumentStatus.DELETED
        
        # Remove from memory
        self._sections.pop(document_id, None)
        self._design_schemas.pop(document_id, None)
        self._ocr_metadata.pop(document_id, None)
        
        logger.info(f"Document deleted: {document_id}")
        return True
    
    def update_sections(
        self, 
        document_id: UUID, 
        updated_sections: List[Dict]
    ) -> List[ContentSection]:
        """Update content sections."""
        sections = self._sections.get(document_id, [])
        section_map = {str(s.id): s for s in sections}
        
        for update in updated_sections:
            section_id = update.get("id")
            if section_id and section_id in section_map:
                section = section_map[section_id]
                if "content" in update:
                    section.update_content(update["content"])
                if "list_items" in update:
                    section.list_items = update["list_items"]
                if "table_data" in update:
                    section.table_data = update["table_data"]
        
        return list(section_map.values())

