"""
File Storage
Handles file uploads and storage operations.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4
import aiofiles

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FileStorage:
    """
    File storage handler for uploaded documents and generated outputs.
    """
    
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.output_dir = settings.OUTPUT_DIR
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure storage directories exist."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_upload(
        self, 
        content: bytes, 
        filename: str, 
        document_id: Optional[UUID] = None
    ) -> Path:
        """
        Save an uploaded file.
        
        Args:
            content: File content as bytes
            filename: Original filename
            document_id: Optional document UUID for naming
            
        Returns:
            Path to saved file
        """
        # Generate unique filename
        doc_id = document_id or uuid4()
        extension = Path(filename).suffix.lower()
        safe_filename = f"{doc_id}{extension}"
        
        file_path = self.upload_dir / safe_filename
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        logger.info(f"Saved upload: {file_path}")
        return file_path
    
    def save_upload_sync(
        self, 
        content: bytes, 
        filename: str, 
        document_id: Optional[UUID] = None
    ) -> Path:
        """
        Save an uploaded file synchronously.
        """
        doc_id = document_id or uuid4()
        extension = Path(filename).suffix.lower()
        safe_filename = f"{doc_id}{extension}"
        
        file_path = self.upload_dir / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved upload: {file_path}")
        return file_path
    
    def get_upload_path(self, document_id: UUID, extension: str) -> Path:
        """Get the path for an uploaded document."""
        return self.upload_dir / f"{document_id}{extension}"
    
    def get_output_path(self, document_id: UUID, format: str) -> Path:
        """Get the path for an output document."""
        return self.output_dir / f"{document_id}_output.{format}"
    
    async def read_file(self, path: Path) -> bytes:
        """Read file content."""
        async with aiofiles.open(path, "rb") as f:
            return await f.read()
    
    def read_file_sync(self, path: Path) -> bytes:
        """Read file content synchronously."""
        with open(path, "rb") as f:
            return f.read()
    
    def file_exists(self, path: Path) -> bool:
        """Check if file exists."""
        return path.exists()
    
    def delete_file(self, path: Path) -> bool:
        """Delete a file."""
        try:
            if path.exists():
                path.unlink()
                logger.info(f"Deleted file: {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete {path}: {e}")
            return False
    
    def delete_document_files(self, document_id: UUID) -> int:
        """Delete all files associated with a document."""
        deleted = 0
        
        # Delete uploaded files
        for ext in [".docx", ".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            path = self.upload_dir / f"{document_id}{ext}"
            if self.delete_file(path):
                deleted += 1
        
        # Delete output files
        for format in ["docx", "pdf"]:
            path = self.output_dir / f"{document_id}_output.{format}"
            if self.delete_file(path):
                deleted += 1
        
        logger.info(f"Deleted {deleted} files for document {document_id}")
        return deleted
    
    def get_file_size(self, path: Path) -> int:
        """Get file size in bytes."""
        return path.stat().st_size if path.exists() else 0
    
    def cleanup_old_files(self, max_age_days: int = 7) -> int:
        """
        Clean up files older than specified days.
        
        Returns number of files deleted.
        """
        import time
        
        deleted = 0
        cutoff = time.time() - (max_age_days * 24 * 60 * 60)
        
        for directory in [self.upload_dir, self.output_dir]:
            for file_path in directory.iterdir():
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff:
                        self.delete_file(file_path)
                        deleted += 1
        
        logger.info(f"Cleaned up {deleted} old files")
        return deleted

