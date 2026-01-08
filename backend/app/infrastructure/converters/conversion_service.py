"""
Conversion Service
Handles document format conversion with automatic detection.
"""

from typing import Optional
from pathlib import Path
from enum import Enum

from app.domain.entities.document import DocumentType
from app.infrastructure.parsers import FileClassifier
from .pdf_to_docx import PDFToDocxConverter
from .image_to_docx import ImageToDocxConverter
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConversionResult:
    """Result of a document conversion."""
    
    def __init__(
        self, 
        success: bool, 
        output_path: Optional[str] = None,
        original_type: Optional[DocumentType] = None,
        error: Optional[str] = None
    ):
        self.success = success
        self.output_path = output_path
        self.original_type = original_type
        self.error = error


class ConversionService:
    """
    Service for converting documents to DOCX format.
    
    Supports:
    - PDF (text-based) -> DOCX
    - PDF (scanned) -> DOCX via OCR
    - Images (PNG, JPG, TIFF) -> DOCX via OCR
    - DOCX -> DOCX (pass-through)
    """
    
    def __init__(self):
        self.image_converter = ImageToDocxConverter()
    
    def convert_to_docx(
        self, 
        file_path: str, 
        content: bytes,
        output_dir: Optional[str] = None
    ) -> ConversionResult:
        """
        Convert any supported file to DOCX format.
        
        Args:
            file_path: Path to the source file.
            content: File content as bytes.
            output_dir: Optional output directory. If None, uses same directory as source.
            
        Returns:
            ConversionResult with success status and output path.
        """
        try:
            # Classify the document
            doc_type, metadata = FileClassifier.classify(file_path, content)
            
            logger.info(f"Converting {doc_type.value} to DOCX: {file_path}")
            
            # Determine output path
            if output_dir:
                output_path = str(Path(output_dir) / (Path(file_path).stem + "_converted.docx"))
            else:
                output_path = str(Path(file_path).with_suffix('.docx'))
            
            # Handle based on document type
            if doc_type == DocumentType.DOCX:
                # Already DOCX, no conversion needed
                logger.info("File is already DOCX, no conversion needed")
                return ConversionResult(
                    success=True,
                    output_path=file_path,
                    original_type=doc_type
                )
            
            elif doc_type == DocumentType.PDF_TEXT:
                # Text-based PDF
                output_path = self._convert_text_pdf(file_path, output_path)
                return ConversionResult(
                    success=True,
                    output_path=output_path,
                    original_type=doc_type
                )
            
            elif doc_type == DocumentType.PDF_SCANNED:
                # Scanned PDF - needs OCR
                output_path = self._convert_scanned_pdf(file_path, output_path)
                return ConversionResult(
                    success=True,
                    output_path=output_path,
                    original_type=doc_type
                )
            
            elif doc_type == DocumentType.IMAGE:
                # Image file - needs OCR
                output_path = self._convert_image(file_path, output_path)
                return ConversionResult(
                    success=True,
                    output_path=output_path,
                    original_type=doc_type
                )
            
            else:
                return ConversionResult(
                    success=False,
                    error=f"Unsupported document type: {doc_type.value}",
                    original_type=doc_type
                )
                
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            return ConversionResult(
                success=False,
                error=str(e)
            )
    
    def _convert_text_pdf(self, pdf_path: str, output_path: str) -> str:
        """Convert text-based PDF to DOCX."""
        with PDFToDocxConverter(pdf_path) as converter:
            return converter.convert(output_path)
    
    def _convert_scanned_pdf(self, pdf_path: str, output_path: str) -> str:
        """Convert scanned PDF to DOCX using OCR."""
        return self.image_converter.convert_scanned_pdf(pdf_path, output_path)
    
    def _convert_image(self, image_path: str, output_path: str) -> str:
        """Convert image to DOCX using OCR."""
        return self.image_converter.convert_image(image_path, output_path)
    
    @staticmethod
    def is_conversion_needed(file_path: str, content: bytes) -> bool:
        """Check if a file needs conversion to DOCX."""
        doc_type, _ = FileClassifier.classify(file_path, content)
        return doc_type != DocumentType.DOCX
    
    @staticmethod
    def get_supported_formats() -> list:
        """Get list of supported input formats."""
        return [".docx", ".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"]

