"""
API Dependencies
Dependency injection for services.
"""

from functools import lru_cache

from app.application.services import DocumentService, SectionService, ExportService, AIService


# Service singletons
_document_service = None
_section_service = None
_export_service = None
_ai_service = None


def get_document_service() -> DocumentService:
    """Get document service instance."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service


def get_section_service() -> SectionService:
    """Get section service instance."""
    global _section_service
    if _section_service is None:
        _section_service = SectionService(get_document_service())
    return _section_service


def get_export_service() -> ExportService:
    """Get export service instance."""
    global _export_service
    if _export_service is None:
        _export_service = ExportService(get_document_service())
    return _export_service


def get_ai_service() -> AIService:
    """Get AI service instance."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService(
            get_document_service(),
            get_section_service()
        )
    return _ai_service

