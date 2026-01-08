"""
Export API Routes
Handles document export operations.
"""

from uuid import UUID
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.application.services import ExportService
from app.api.dependencies import get_export_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/documents/{document_id}/export", tags=["Export"])


class ExportRequest(BaseModel):
    """Request model for document export."""
    format: str = "docx"  # docx or pdf


@router.post("")
async def export_document(
    document_id: UUID,
    request: ExportRequest,
    export_service: ExportService = Depends(get_export_service),
):
    """
    Export document in specified format.
    
    Generates the document from current design schema + sections.
    
    Supported formats: docx, pdf
    """
    try:
        format_lower = request.format.lower()
        
        if format_lower not in ["docx", "pdf"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported format. Use 'docx' or 'pdf'"
            )
        
        output_path = export_service.export(document_id, format_lower)
        
        if not output_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or cannot be exported"
            )
        
        return {
            "success": True,
            "message": f"Document exported as {format_lower}",
            "data": {
                "format": format_lower,
                "download_url": f"/api/v1/documents/{document_id}/export/download/{format_lower}",
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/download/{format}")
async def download_export(
    document_id: UUID,
    format: str,
    export_service: ExportService = Depends(get_export_service),
):
    """
    Download exported document.
    
    Returns the file as an attachment for direct download.
    """
    format_lower = format.lower()
    
    if format_lower not in ["docx", "pdf"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported format"
        )
    
    # Get or generate export
    output_path = export_service.get_export_path(document_id, format_lower)
    
    if not output_path or not output_path.exists():
        # Try to generate
        output_path = export_service.export(document_id, format_lower)
    
    if not output_path or not output_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found. Generate it first."
        )
    
    # Determine media type
    media_types = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pdf": "application/pdf",
    }
    
    return FileResponse(
        path=str(output_path),
        media_type=media_types.get(format_lower, "application/octet-stream"),
        filename=f"document.{format_lower}",
        headers={
            "Content-Disposition": f'attachment; filename="document.{format_lower}"'
        }
    )


@router.delete("")
async def delete_exports(
    document_id: UUID,
    export_service: ExportService = Depends(get_export_service),
):
    """
    Delete all exported files for a document.
    """
    deleted = export_service.delete_exports(document_id)
    
    return {
        "success": True,
        "message": f"Deleted {deleted} export files",
    }

