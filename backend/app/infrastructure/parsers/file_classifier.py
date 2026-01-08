"""
File Classifier
Automatically classifies uploaded documents and routes them to the correct pipeline.
"""

from pathlib import Path
from typing import Tuple, Optional
import fitz  # PyMuPDF
from app.domain.entities.document import DocumentType
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import magic, fallback to extension-based detection
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning("python-magic not available, using extension-based file detection")


class FileClassifier:
    """
    Classifies documents by type and determines processing pipeline.
    
    Supports:
    - DOCX files
    - Text-based PDFs
    - Scanned PDFs (image-only)
    - Image files (PNG, JPG, TIFF, etc.)
    """
    
    # MIME type mappings
    DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    PDF_MIME = "application/pdf"
    IMAGE_MIMES = {"image/png", "image/jpeg", "image/tiff", "image/bmp"}
    
    @classmethod
    def classify(cls, file_path: str, content: Optional[bytes] = None) -> Tuple[DocumentType, dict]:
        """
        Classify a document and return its type with metadata.
        
        Returns:
            Tuple of (DocumentType, metadata_dict)
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        # Read content if not provided
        if content is None:
            with open(file_path, "rb") as f:
                content = f.read()
        
        # Get MIME type - try magic first, fallback to extension
        mime_type = cls._detect_mime_type(content, extension)
        
        metadata = {
            "extension": extension,
            "mime_type": mime_type,
            "file_size": len(content),
        }
        
        # Classify based on MIME type
        if mime_type == cls.DOCX_MIME or extension == ".docx":
            doc_type = DocumentType.DOCX
            metadata["parser"] = "docx"
            
        elif mime_type == cls.PDF_MIME or extension == ".pdf":
            # For PDF, we need to determine if it's text-based or scanned
            is_scanned, pdf_meta = cls._analyze_pdf(file_path, content)
            metadata.update(pdf_meta)
            
            if is_scanned:
                doc_type = DocumentType.PDF_SCANNED
                metadata["parser"] = "ocr"
            else:
                doc_type = DocumentType.PDF_TEXT
                metadata["parser"] = "pdf"
                
        elif mime_type in cls.IMAGE_MIMES or extension in {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}:
            doc_type = DocumentType.IMAGE
            metadata["parser"] = "ocr"
            
        else:
            doc_type = DocumentType.UNKNOWN
            metadata["parser"] = None
            logger.warning(f"Unknown file type: {mime_type}, extension: {extension}")
        
        logger.info(f"Classified {path.name} as {doc_type.value}")
        return doc_type, metadata
    
    @classmethod
    def _analyze_pdf(cls, file_path: str, content: bytes) -> Tuple[bool, dict]:
        """
        Analyze a PDF to determine if it's text-based or scanned.
        
        Returns:
            Tuple of (is_scanned: bool, metadata: dict)
        """
        metadata = {
            "page_count": 0,
            "has_text": False,
            "has_images": False,
            "text_coverage": 0.0,
            "is_encrypted": False,
        }
        
        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(stream=content, filetype="pdf")
            metadata["page_count"] = len(doc)
            metadata["is_encrypted"] = doc.is_encrypted
            
            if doc.is_encrypted:
                logger.warning("PDF is encrypted, may require password")
                return True, metadata  # Treat encrypted as scanned for safety
            
            total_text_chars = 0
            total_images = 0
            total_page_area = 0
            total_text_area = 0
            
            for page_num in range(min(len(doc), 5)):  # Check first 5 pages
                page = doc[page_num]
                
                # Get page dimensions
                page_rect = page.rect
                page_area = page_rect.width * page_rect.height
                total_page_area += page_area
                
                # Extract text
                text = page.get_text()
                text_chars = len(text.strip())
                total_text_chars += text_chars
                
                # Get text blocks to estimate coverage
                blocks = page.get_text("dict", flags=11)["blocks"]
                for block in blocks:
                    if block.get("type") == 0:  # Text block
                        bbox = block.get("bbox", [0, 0, 0, 0])
                        block_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                        total_text_area += block_area
                
                # Count images
                images = page.get_images()
                total_images += len(images)
            
            doc.close()
            
            # Calculate metrics
            metadata["has_text"] = total_text_chars > 100
            metadata["has_images"] = total_images > 0
            
            if total_page_area > 0:
                metadata["text_coverage"] = total_text_area / total_page_area
            
            # Determine if scanned:
            # - Very little text extracted
            # - Or text coverage is minimal but images present
            is_scanned = (
                total_text_chars < 50 or  # Almost no text
                (metadata["text_coverage"] < 0.05 and total_images > 0)  # Low text, has images
            )
            
            logger.info(
                f"PDF analysis: pages={metadata['page_count']}, "
                f"chars={total_text_chars}, images={total_images}, "
                f"coverage={metadata['text_coverage']:.2%}, scanned={is_scanned}"
            )
            
            return is_scanned, metadata
            
        except Exception as e:
            logger.error(f"PDF analysis failed: {e}")
            metadata["error"] = str(e)
            return True, metadata  # Default to scanned on error
    
    @classmethod
    def _detect_mime_type(cls, content: bytes, extension: str) -> str:
        """
        Detect MIME type from content or extension.
        Uses python-magic if available, falls back to extension mapping.
        """
        # Try magic first
        if MAGIC_AVAILABLE:
            try:
                return magic.from_buffer(content[:2048], mime=True)
            except Exception as e:
                logger.warning(f"Magic detection failed: {e}")
        
        # Fallback to extension-based detection
        extension_mime_map = {
            ".docx": cls.DOCX_MIME,
            ".pdf": cls.PDF_MIME,
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
            ".bmp": "image/bmp",
        }
        
        mime = extension_mime_map.get(extension, "application/octet-stream")
        logger.info(f"Using extension-based MIME detection: {extension} -> {mime}")
        return mime
    
    @classmethod
    def get_page_count(cls, file_path: str, content: bytes, doc_type: DocumentType) -> int:
        """Get the page count for a document."""
        try:
            if doc_type in [DocumentType.PDF_TEXT, DocumentType.PDF_SCANNED]:
                doc = fitz.open(stream=content, filetype="pdf")
                count = len(doc)
                doc.close()
                return count
            elif doc_type == DocumentType.DOCX:
                # DOCX page count requires rendering, estimate from content
                return 1  # Will be updated after parsing
            elif doc_type == DocumentType.IMAGE:
                return 1
            return 1
        except Exception as e:
            logger.error(f"Failed to get page count: {e}")
            return 1

