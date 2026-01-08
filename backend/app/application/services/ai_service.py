"""
AI Service
Manages AI content generation operations.
"""

from typing import Optional, List, Dict
from uuid import UUID

from app.domain.entities.content_section import ContentSection
from app.infrastructure.ai import OpenAIClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AIService:
    """
    Service for AI content generation.
    
    Rules:
    - Operates per section only
    - Never modifies design
    - Respects section constraints
    """
    
    def __init__(self, document_service, section_service):
        self.document_service = document_service
        self.section_service = section_service
        self.ai_client = OpenAIClient()
    
    def is_available(self) -> bool:
        """Check if AI service is available."""
        return self.ai_client.is_available()
    
    def generate_content(
        self,
        document_id: UUID,
        section_id: UUID,
        prompt: str,
        tone: str = "professional",
        max_length: Optional[int] = None,
    ) -> Optional[ContentSection]:
        """
        Generate AI content for a specific section.
        
        Args:
            document_id: Document UUID
            section_id: Target section UUID
            prompt: User's generation prompt
            tone: Desired tone
            max_length: Maximum word count
            
        Returns:
            Updated ContentSection or None
        """
        if not self.is_available():
            raise RuntimeError("AI service not available")
        
        # Get section
        section = self.section_service.get_section(document_id, section_id)
        if not section:
            logger.error(f"Section not found: {section_id}")
            return None
        
        if not section.ai_enabled:
            raise ValueError("AI generation not enabled for this section")
        
        # Build context from nearby sections
        context = self._build_context(document_id, section)
        
        # Generate content
        generated = self.ai_client.generate_content(
            section=section,
            prompt=prompt,
            context=context,
            tone=tone,
            max_length=max_length,
        )
        
        # Update section
        section.update_content(generated, ai_generated=True)
        section.ai_prompt_used = prompt
        
        logger.info(f"AI generated content for section {section_id}")
        return section
    
    def suggest_improvements(
        self,
        document_id: UUID,
        section_id: UUID,
    ) -> List[str]:
        """
        Get AI suggestions for improving section content.
        
        Returns:
            List of improvement suggestions
        """
        if not self.is_available():
            raise RuntimeError("AI service not available")
        
        section = self.section_service.get_section(document_id, section_id)
        if not section:
            return ["Section not found"]
        
        context = self._build_context(document_id, section)
        return self.ai_client.suggest_improvements(section, context)
    
    def adjust_tone(
        self,
        document_id: UUID,
        section_id: UUID,
        target_tone: str,
    ) -> Optional[ContentSection]:
        """
        Adjust the tone of section content.
        
        Args:
            document_id: Document UUID
            section_id: Section UUID
            target_tone: Target tone (professional, casual, academic, etc.)
            
        Returns:
            Updated section
        """
        if not self.is_available():
            raise RuntimeError("AI service not available")
        
        section = self.section_service.get_section(document_id, section_id)
        if not section:
            return None
        
        adjusted = self.ai_client.adjust_tone(section, target_tone)
        section.update_content(adjusted, ai_generated=True)
        
        return section
    
    def _build_context(
        self, 
        document_id: UUID, 
        current_section: ContentSection
    ) -> Dict:
        """Build context from document and nearby sections."""
        sections = self.document_service.get_sections(document_id)
        document = self.document_service.get_document(document_id)
        
        # Get nearby sections
        current_idx = None
        for idx, s in enumerate(sections):
            if s.id == current_section.id:
                current_idx = idx
                break
        
        nearby = []
        if current_idx is not None:
            # Get 2 sections before and after
            start = max(0, current_idx - 2)
            end = min(len(sections), current_idx + 3)
            
            for idx in range(start, end):
                if idx != current_idx:
                    nearby.append(sections[idx].content)
        
        context = {
            "nearby_sections": nearby,
            "document_type": document.document_type.value if document else None,
            "total_sections": len(sections),
        }
        
        return context
    
    def batch_generate(
        self,
        document_id: UUID,
        section_prompts: Dict[UUID, str],
        tone: str = "professional",
    ) -> Dict[UUID, ContentSection]:
        """
        Generate content for multiple sections.
        
        Args:
            section_prompts: Dict mapping section_id to prompt
            tone: Desired tone for all sections
            
        Returns:
            Dict mapping section_id to updated section
        """
        results = {}
        
        for section_id, prompt in section_prompts.items():
            try:
                section = self.generate_content(
                    document_id, section_id, prompt, tone
                )
                if section:
                    results[section_id] = section
            except Exception as e:
                logger.error(f"Failed to generate for section {section_id}: {e}")
        
        return results

