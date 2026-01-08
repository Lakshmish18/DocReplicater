"""
Section Service
Manages content section operations.
"""

from typing import List, Optional, Dict
from uuid import UUID

from app.domain.entities.content_section import ContentSection, SectionType
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SectionService:
    """
    Service for content section management.
    
    Responsibilities:
    - Section CRUD operations
    - Content updates
    - Version management
    """
    
    def __init__(self, document_service):
        self.document_service = document_service
    
    def get_section(
        self, 
        document_id: UUID, 
        section_id: UUID
    ) -> Optional[ContentSection]:
        """Get a specific section by ID."""
        sections = self.document_service.get_sections(document_id)
        for section in sections:
            if section.id == section_id:
                return section
        return None
    
    def update_section_content(
        self,
        document_id: UUID,
        section_id: UUID,
        content: str,
        ai_generated: bool = False
    ) -> Optional[ContentSection]:
        """Update content for a specific section."""
        section = self.get_section(document_id, section_id)
        if not section:
            return None
        
        if not section.editable:
            raise ValueError("Section is not editable")
        
        section.update_content(content, ai_generated)
        logger.info(f"Updated section {section_id}: {len(content)} chars")
        
        return section
    
    def update_section_list(
        self,
        document_id: UUID,
        section_id: UUID,
        list_items: List[str]
    ) -> Optional[ContentSection]:
        """Update list items for a list section."""
        section = self.get_section(document_id, section_id)
        if not section:
            return None
        
        if section.section_type not in [SectionType.BULLET_LIST, SectionType.NUMBERED_LIST]:
            raise ValueError("Section is not a list type")
        
        section.list_items = list_items
        section.version += 1
        
        return section
    
    def update_section_table(
        self,
        document_id: UUID,
        section_id: UUID,
        table_data: List[List[str]]
    ) -> Optional[ContentSection]:
        """Update table data for a table section."""
        section = self.get_section(document_id, section_id)
        if not section:
            return None
        
        if section.section_type != SectionType.TABLE:
            raise ValueError("Section is not a table type")
        
        section.table_data = table_data
        section.version += 1
        
        return section
    
    def reset_section(
        self,
        document_id: UUID,
        section_id: UUID
    ) -> Optional[ContentSection]:
        """Reset section to original content."""
        section = self.get_section(document_id, section_id)
        if not section:
            return None
        
        section.reset_to_original()
        logger.info(f"Reset section {section_id} to original")
        
        return section
    
    def batch_update(
        self,
        document_id: UUID,
        updates: List[Dict]
    ) -> List[ContentSection]:
        """
        Batch update multiple sections.
        
        Args:
            updates: List of {id, content} dictionaries
        """
        updated = []
        
        for update in updates:
            section_id = UUID(update["id"]) if isinstance(update["id"], str) else update["id"]
            content = update.get("content")
            
            if content is not None:
                section = self.update_section_content(
                    document_id, section_id, content
                )
                if section:
                    updated.append(section)
        
        return updated
    
    def get_editable_sections(self, document_id: UUID) -> List[ContentSection]:
        """Get all editable sections for a document."""
        sections = self.document_service.get_sections(document_id)
        return [s for s in sections if s.editable]
    
    def get_ai_enabled_sections(self, document_id: UUID) -> List[ContentSection]:
        """Get all AI-enabled sections for a document."""
        sections = self.document_service.get_sections(document_id)
        return [s for s in sections if s.ai_enabled]
    
    def get_section_statistics(self, document_id: UUID) -> Dict:
        """Get statistics about document sections."""
        sections = self.document_service.get_sections(document_id)
        
        stats = {
            "total": len(sections),
            "editable": sum(1 for s in sections if s.editable),
            "ai_enabled": sum(1 for s in sections if s.ai_enabled),
            "modified": sum(1 for s in sections if s.content != s.original_content),
            "ai_generated": sum(1 for s in sections if s.ai_generated),
            "by_type": {},
            "total_words": 0,
            "total_characters": 0,
        }
        
        for section in sections:
            type_name = section.section_type.value
            stats["by_type"][type_name] = stats["by_type"].get(type_name, 0) + 1
            stats["total_words"] += section.get_word_count()
            stats["total_characters"] += section.get_character_count()
        
        return stats

