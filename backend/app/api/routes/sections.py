"""
Section API Routes
Handles content section operations.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from app.application.services import SectionService
from app.api.dependencies import get_document_service, get_section_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/documents/{document_id}/sections", tags=["Sections"])


class SectionUpdateRequest(BaseModel):
    """Request model for updating section content."""
    content: Optional[str] = None
    list_items: Optional[List[str]] = None
    table_data: Optional[List[List[str]]] = None


class BatchUpdateRequest(BaseModel):
    """Request model for batch section updates."""
    sections: List[dict]  # [{id, content}, ...]


@router.get("")
async def get_sections(
    document_id: UUID,
    section_service: SectionService = Depends(get_section_service),
):
    """
    Get all content sections for a document.
    """
    sections = section_service.document_service.get_sections(document_id)
    
    if not sections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or has no sections"
        )
    
    return {
        "success": True,
        "data": {
            "sections": [s.to_dict() for s in sections],
            "total": len(sections),
        }
    }


@router.get("/editable")
async def get_editable_sections(
    document_id: UUID,
    section_service: SectionService = Depends(get_section_service),
):
    """
    Get only editable sections.
    """
    sections = section_service.get_editable_sections(document_id)
    
    return {
        "success": True,
        "data": {
            "sections": [s.to_dict() for s in sections],
            "total": len(sections),
        }
    }


@router.get("/statistics")
async def get_section_statistics(
    document_id: UUID,
    section_service: SectionService = Depends(get_section_service),
):
    """
    Get statistics about document sections.
    """
    stats = section_service.get_section_statistics(document_id)
    
    return {
        "success": True,
        "data": stats,
    }


@router.get("/{section_id}")
async def get_section(
    document_id: UUID,
    section_id: UUID,
    section_service: SectionService = Depends(get_section_service),
):
    """
    Get a specific section by ID.
    """
    section = section_service.get_section(document_id, section_id)
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    return {
        "success": True,
        "data": section.to_dict(),
    }


@router.put("/{section_id}")
async def update_section(
    document_id: UUID,
    section_id: UUID,
    request: SectionUpdateRequest,
    section_service: SectionService = Depends(get_section_service),
):
    """
    Update section content.
    
    Only the content can be modified - design/formatting is preserved.
    """
    try:
        section = None
        
        if request.content is not None:
            section = section_service.update_section_content(
                document_id, section_id, request.content
            )
        elif request.list_items is not None:
            section = section_service.update_section_list(
                document_id, section_id, request.list_items
            )
        elif request.table_data is not None:
            section = section_service.update_section_table(
                document_id, section_id, request.table_data
            )
        
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        return {
            "success": True,
            "message": "Section updated successfully",
            "data": section.to_dict(),
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{section_id}/reset")
async def reset_section(
    document_id: UUID,
    section_id: UUID,
    section_service: SectionService = Depends(get_section_service),
):
    """
    Reset section to original content.
    """
    section = section_service.reset_section(document_id, section_id)
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    return {
        "success": True,
        "message": "Section reset to original",
        "data": section.to_dict(),
    }


@router.post("/batch-update")
async def batch_update_sections(
    document_id: UUID,
    request: BatchUpdateRequest,
    section_service: SectionService = Depends(get_section_service),
):
    """
    Update multiple sections at once.
    
    Request body: {"sections": [{"id": "uuid", "content": "..."}, ...]}
    """
    try:
        updated = section_service.batch_update(document_id, request.sections)
        
        return {
            "success": True,
            "message": f"Updated {len(updated)} sections",
            "data": {
                "updated": [s.to_dict() for s in updated],
                "count": len(updated),
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

