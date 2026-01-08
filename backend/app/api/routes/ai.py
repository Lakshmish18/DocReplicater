"""
AI API Routes
Handles AI content generation.
"""

from typing import Optional, Dict
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from app.application.services import AIService
from app.api.dependencies import get_ai_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/documents/{document_id}/ai", tags=["AI"])


class GenerateContentRequest(BaseModel):
    """Request model for AI content generation."""
    section_id: UUID
    prompt: str = Field(..., min_length=1, description="Generation prompt")
    tone: str = Field("professional", description="Desired tone")
    max_length: Optional[int] = Field(None, description="Maximum word count")


class AdjustToneRequest(BaseModel):
    """Request model for tone adjustment."""
    section_id: UUID
    target_tone: str = Field(..., description="Target tone")


class BatchGenerateRequest(BaseModel):
    """Request model for batch generation."""
    section_prompts: Dict[str, str]  # {section_id: prompt}
    tone: str = "professional"


@router.get("/status")
async def get_ai_status(
    ai_service: AIService = Depends(get_ai_service),
):
    """
    Check if AI service is available.
    """
    return {
        "available": ai_service.is_available(),
        "message": "AI service is ready" if ai_service.is_available() else "AI service not configured",
    }


@router.post("/generate")
async def generate_content(
    document_id: UUID,
    request: GenerateContentRequest,
    ai_service: AIService = Depends(get_ai_service),
):
    """
    Generate AI content for a specific section.
    
    The AI will:
    - Generate content appropriate for the section type
    - Respect tone and length constraints
    - Consider context from nearby sections
    
    The section must have ai_enabled=true.
    """
    if not ai_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not available. Configure OPENAI_API_KEY."
        )
    
    try:
        section = ai_service.generate_content(
            document_id=document_id,
            section_id=request.section_id,
            prompt=request.prompt,
            tone=request.tone,
            max_length=request.max_length,
        )
        
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        return {
            "success": True,
            "message": "Content generated successfully",
            "data": section.to_dict(),
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )


@router.post("/suggestions/{section_id}")
async def get_suggestions(
    document_id: UUID,
    section_id: UUID,
    ai_service: AIService = Depends(get_ai_service),
):
    """
    Get AI suggestions for improving section content.
    """
    if not ai_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not available"
        )
    
    try:
        suggestions = ai_service.suggest_improvements(document_id, section_id)
        
        return {
            "success": True,
            "data": {
                "suggestions": suggestions,
            }
        }
        
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )


@router.post("/adjust-tone")
async def adjust_tone(
    document_id: UUID,
    request: AdjustToneRequest,
    ai_service: AIService = Depends(get_ai_service),
):
    """
    Adjust the tone of section content.
    
    Available tones: professional, casual, academic, friendly, formal
    """
    if not ai_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not available"
        )
    
    try:
        section = ai_service.adjust_tone(
            document_id=document_id,
            section_id=request.section_id,
            target_tone=request.target_tone,
        )
        
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        return {
            "success": True,
            "message": f"Tone adjusted to {request.target_tone}",
            "data": section.to_dict(),
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )


@router.post("/batch-generate")
async def batch_generate(
    document_id: UUID,
    request: BatchGenerateRequest,
    ai_service: AIService = Depends(get_ai_service),
):
    """
    Generate content for multiple sections at once.
    """
    if not ai_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not available"
        )
    
    try:
        # Convert string IDs to UUIDs
        section_prompts = {
            UUID(k): v for k, v in request.section_prompts.items()
        }
        
        results = ai_service.batch_generate(
            document_id=document_id,
            section_prompts=section_prompts,
            tone=request.tone,
        )
        
        return {
            "success": True,
            "message": f"Generated content for {len(results)} sections",
            "data": {
                "generated": {str(k): v.to_dict() for k, v in results.items()},
                "count": len(results),
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

