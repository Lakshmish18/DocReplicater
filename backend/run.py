#!/usr/bin/env python
"""
Run script for Document Design Replicator Backend.
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("=" * 60)
    print(f"Starting {settings.APP_NAME}")
    print(f"Version: {settings.APP_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print("=" * 60)
    print(f"\nServer: http://{settings.HOST}:{settings.PORT}")
    print(f"API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"ReDoc: http://{settings.HOST}:{settings.PORT}/redoc")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

