"""
Document API Routes
Handles document upload, retrieval, and management.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse

from app.application.services import DocumentService
from app.api.dependencies import get_document_service
from app.utils.validators import validate_file_upload
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Upload and process a document.
    
    Accepts: DOCX, PDF (text-based or scanned), PNG, JPG, TIFF
    
    The document will be processed through the appropriate pipeline:
    - DOCX: Direct parsing
    - Text PDF: PDF text extraction
    - Scanned PDF/Images: OCR pipeline
    
    Returns the processed document with extracted design schema and sections.
    """
    try:
        # Validate file
        extension, mime_type, content = await validate_file_upload(file)
        
        # Process document
        document = await document_service.process_upload(
            content=content,
            filename=file.filename,
        )
        
        # Get complete data
        data = document_service.get_document_data(document.id)
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "message": "Document processed successfully",
                "data": data,
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )


@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Get document with design schema and sections.
    """
    data = document_service.get_document_data(document_id)
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {
        "success": True,
        "data": data,
    }


@router.get("")
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    List all documents with pagination.
    """
    documents, total = document_service.list_documents(
        page=page,
        page_size=page_size,
    )
    
    return {
        "success": True,
        "data": {
            "documents": [d.to_dict() for d in documents],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Delete a document and all associated files.
    """
    success = document_service.delete_document(document_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {
        "success": True,
        "message": "Document deleted successfully",
    }


@router.get("/{document_id}/design-schema")
async def get_design_schema(
    document_id: UUID,
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Get the design schema for a document.
    
    The design schema is immutable and contains all formatting information.
    """
    schema = document_service.get_design_schema(document_id)
    
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Design schema not found"
        )
    
    return {
        "success": True,
        "data": schema.to_dict(),
    }


@router.get("/{document_id}/ocr-metadata")
async def get_ocr_metadata(
    document_id: UUID,
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Get OCR metadata for a scanned document.
    
    Returns None if document was not processed with OCR.
    """
    document = document_service.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    ocr_metadata = document_service.get_ocr_metadata(document_id)
    
    return {
        "success": True,
        "data": ocr_metadata.to_dict() if ocr_metadata else None,
        "message": "No OCR metadata" if not ocr_metadata else None,
    }

