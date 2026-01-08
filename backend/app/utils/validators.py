"""
File and Input Validators
Handles validation of uploads, inputs, and security checks.
"""

from pathlib import Path
from typing import BinaryIO, Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import magic, fallback to extension-based validation
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning("python-magic not available, MIME validation will use extension-based detection")


class FileValidator:
    """Validates uploaded files for security and compliance."""
    
    # MIME type mappings for allowed file types
    MIME_TYPE_MAP = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/pdf": ".pdf",
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/tiff": ".tiff",
        "image/bmp": ".bmp",
    }
    
    EXTENSION_MIME_MAP = {v: k for k, v in MIME_TYPE_MAP.items()}
    
    @classmethod
    def validate_extension(cls, filename: str) -> Tuple[bool, str]:
        """Validate file extension."""
        ext = Path(filename).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            return False, f"File extension '{ext}' not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        return True, ext
    
    @classmethod
    def validate_mime_type(cls, content: bytes, expected_extension: str) -> Tuple[bool, str]:
        """Validate MIME type matches expected extension."""
        try:
            # Try magic-based detection first
            if MAGIC_AVAILABLE:
                mime = magic.from_buffer(content[:2048], mime=True)
            else:
                # Fallback to extension-based MIME type
                mime = cls.EXTENSION_MIME_MAP.get(expected_extension, "application/octet-stream")
                # For images, do basic header checks
                if expected_extension in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
                    detected = cls._detect_image_type(content)
                    if detected:
                        mime = detected
                logger.info(f"Using extension-based MIME: {expected_extension} -> {mime}")
            
            expected_mime = cls.EXTENSION_MIME_MAP.get(expected_extension)
            
            # Allow JPEG variations
            if expected_extension in [".jpg", ".jpeg"] and mime in ["image/jpeg", "image/jpg"]:
                return True, mime
            
            if expected_mime and mime != expected_mime:
                logger.warning(f"MIME type mismatch: expected {expected_mime}, got {mime}")
                # Be lenient for some cases
                if mime in cls.MIME_TYPE_MAP:
                    return True, mime
                return False, f"MIME type '{mime}' does not match extension '{expected_extension}'"
            
            return True, mime
        except Exception as e:
            logger.error(f"MIME validation error: {e}")
            return False, f"Could not validate MIME type: {str(e)}"
    
    @classmethod
    def _detect_image_type(cls, content: bytes) -> Optional[str]:
        """Detect image type from file header (magic bytes)."""
        if len(content) < 12:
            return None
        
        # PNG: 89 50 4E 47
        if content[:4] == b'\x89PNG':
            return "image/png"
        # JPEG: FF D8 FF
        if content[:3] == b'\xff\xd8\xff':
            return "image/jpeg"
        # TIFF: 49 49 2A 00 (little endian) or 4D 4D 00 2A (big endian)
        if content[:4] in [b'II*\x00', b'MM\x00*']:
            return "image/tiff"
        # BMP: 42 4D
        if content[:2] == b'BM':
            return "image/bmp"
        # PDF: 25 50 44 46
        if content[:4] == b'%PDF':
            return "application/pdf"
        
        return None
    
    @classmethod
    def validate_size(cls, size: int) -> Tuple[bool, str]:
        """Validate file size."""
        if size > settings.MAX_FILE_SIZE:
            max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"File size {size / (1024 * 1024):.2f}MB exceeds maximum {max_mb}MB"
        return True, "OK"
    
    @classmethod
    async def validate_upload(cls, file: UploadFile) -> Tuple[str, str, bytes]:
        """
        Comprehensive file upload validation.
        Returns: (extension, mime_type, content)
        """
        # Validate filename exists
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        # Validate extension
        valid, ext = cls.validate_extension(file.filename)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ext
            )
        
        # Read content
        content = await file.read()
        await file.seek(0)
        
        # Validate size
        valid, msg = cls.validate_size(len(content))
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=msg
            )
        
        # Validate MIME type
        valid, mime = cls.validate_mime_type(content, ext)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=mime
            )
        
        logger.info(f"File validated: {file.filename}, extension: {ext}, mime: {mime}, size: {len(content)}")
        return ext, mime, content


async def validate_file_upload(file: UploadFile) -> Tuple[str, str, bytes]:
    """Convenience function for file validation."""
    return await FileValidator.validate_upload(file)

