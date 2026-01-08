"""
Document Design Replicator - Main Application
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.api.routes import documents_router, sections_router, export_router, ai_router
from app.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug: {settings.DEBUG}")
    logger.info("=" * 60)
    
    # Ensure directories exist
    settings.setup_directories()
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    Document Design Replicator API
    
    A comprehensive backend for extracting document design and enabling content replacement.
    
    ## Features
    
    - **Document Upload**: Support for DOCX, PDF (text and scanned), and images
    - **Design Extraction**: Automatically extracts formatting, styles, and layout
    - **OCR Processing**: Full OCR pipeline for scanned documents
    - **Section Editing**: Edit content while preserving design
    - **AI Generation**: Generate section content using OpenAI
    - **Export**: Export to DOCX or PDF with preserved formatting
    
    ## Workflow
    
    1. Upload a document
    2. Review extracted design schema and sections
    3. Edit section content (manually or with AI)
    4. Export the document with new content and original design
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation error",
            "details": exc.errors(),
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred",
        }
    )


# Include routers
app.include_router(documents_router, prefix="/api/v1")
app.include_router(sections_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")


# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

