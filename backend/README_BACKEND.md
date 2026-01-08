# Document Design Replicator - Backend

A production-ready Python backend for document processing, OCR, design extraction, and AI content generation.

## Features

- **Multi-Format Support**: DOCX, text-based PDFs, scanned PDFs, and images
- **OCR Pipeline**: Full Tesseract-based OCR with OpenCV preprocessing
- **Design Extraction**: Automatic extraction of styles, formatting, and layout
- **Section-Based Editing**: Edit content while preserving design
- **AI Content Generation**: OpenAI-powered content generation per section
- **Export**: Generate DOCX and PDF with preserved formatting

## Architecture

Clean Architecture with strict separation:

```
backend/
├── app/
│   ├── api/                    # API Layer (Controllers)
│   │   ├── routes/
│   │   │   ├── documents.py
│   │   │   ├── sections.py
│   │   │   ├── export.py
│   │   │   └── ai.py
│   │   └── dependencies.py
│   │
│   ├── application/            # Application Layer (Services)
│   │   └── services/
│   │       ├── document_service.py
│   │       ├── section_service.py
│   │       ├── export_service.py
│   │       └── ai_service.py
│   │
│   ├── domain/                 # Domain Layer (Entities, Schemas)
│   │   ├── entities/
│   │   │   ├── document.py
│   │   │   ├── design_schema.py
│   │   │   ├── content_section.py
│   │   │   └── ocr_metadata.py
│   │   └── schemas/
│   │
│   ├── infrastructure/         # Infrastructure Layer
│   │   ├── database/
│   │   ├── parsers/           # DOCX, PDF parsers
│   │   ├── ocr/               # OCR engine, preprocessor
│   │   ├── generators/        # DOCX, PDF generators
│   │   ├── ai/                # OpenAI client
│   │   └── storage/           # File storage
│   │
│   ├── utils/
│   ├── config.py
│   └── main.py
│
├── requirements.txt
└── README_BACKEND.md
```

## Setup

### Prerequisites

- Python 3.10+
- Tesseract OCR (for scanned documents)
- OpenAI API key (for AI features)

### Install Tesseract

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### Install Python Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Configuration

Create `.env` file:

```env
# Application
APP_NAME=Document Design Replicator
DEBUG=True
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///./docreplicate.db

# OpenAI
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4

# OCR
TESSERACT_PATH=/usr/local/bin/tesseract  # Optional, if not in PATH
OCR_LANGUAGE=eng
OCR_DPI=300

# File Storage
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs
MAX_FILE_SIZE=52428800  # 50MB

# Security
SECRET_KEY=your-secret-key-change-in-production
```

### Run the Server

```bash
# Development
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/upload` | Upload and process document |
| GET | `/api/v1/documents` | List all documents |
| GET | `/api/v1/documents/{id}` | Get document with schema and sections |
| DELETE | `/api/v1/documents/{id}` | Delete document |
| GET | `/api/v1/documents/{id}/design-schema` | Get design schema |
| GET | `/api/v1/documents/{id}/ocr-metadata` | Get OCR metadata |

### Sections

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/documents/{id}/sections` | Get all sections |
| GET | `/api/v1/documents/{id}/sections/editable` | Get editable sections |
| GET | `/api/v1/documents/{id}/sections/{section_id}` | Get specific section |
| PUT | `/api/v1/documents/{id}/sections/{section_id}` | Update section content |
| POST | `/api/v1/documents/{id}/sections/{section_id}/reset` | Reset to original |
| POST | `/api/v1/documents/{id}/sections/batch-update` | Batch update sections |

### Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/{id}/export` | Generate export |
| GET | `/api/v1/documents/{id}/export/download/{format}` | Download export |

### AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/documents/{id}/ai/status` | Check AI availability |
| POST | `/api/v1/documents/{id}/ai/generate` | Generate content for section |
| POST | `/api/v1/documents/{id}/ai/suggestions/{section_id}` | Get improvement suggestions |
| POST | `/api/v1/documents/{id}/ai/adjust-tone` | Adjust content tone |
| POST | `/api/v1/documents/{id}/ai/batch-generate` | Batch generate content |

## Document Processing Pipeline

### 1. Upload & Classification

```
File Upload → MIME Validation → Type Detection → Pipeline Routing
```

Detects:
- DOCX files
- Text-based PDFs
- Scanned PDFs (image-only)
- Image files (PNG, JPG, TIFF)

### 2. OCR Pipeline (for scanned documents)

```
Image → Preprocessing → OCR → Layout Analysis → Structure
```

Preprocessing steps:
- Grayscale conversion
- Adaptive thresholding
- Noise removal
- Deskewing
- Resolution normalization

### 3. Design Extraction

Extracts:
- Page setup (dimensions, margins)
- Style tokens (fonts, sizes, colors)
- Heading hierarchy
- Color palette

### 4. Content Sections

Creates editable sections:
- Title, headings, paragraphs
- Lists (bullet, numbered)
- Tables
- Images with captions

### 5. Export

Regenerates document with:
- Original design schema
- Updated content
- Preserved formatting

## AI Content Generation

Rules:
- Operates per section only
- Never modifies design
- Respects section type constraints
- Context-aware (nearby sections)

Example:
```python
{
    "section_id": "uuid",
    "prompt": "Write an introduction about machine learning",
    "tone": "professional",
    "max_length": 200
}
```

## Database Models

- **User**: Authentication and document ownership
- **Document**: Uploaded document metadata
- **DesignSchema**: Immutable design information
- **ContentSection**: Editable content units
- **OCRMetadata**: OCR processing results
- **DocumentVersion**: Version history

## Error Handling

- Structured JSON error responses
- OCR confidence warnings
- Graceful fallbacks for parsing failures
- Comprehensive logging

## Testing

```bash
pytest tests/
```

## Production Considerations

1. **Database**: Switch from SQLite to PostgreSQL
2. **Storage**: Use S3 or similar for file storage
3. **Authentication**: Implement proper auth (JWT)
4. **Rate Limiting**: Add rate limiting for API
5. **Caching**: Add Redis for caching
6. **Background Tasks**: Use Celery for OCR processing
7. **Monitoring**: Add Prometheus/Grafana

## License

MIT

