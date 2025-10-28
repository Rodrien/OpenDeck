# Backend Document Processing Pipeline - Implementation Summary

**Date:** 2025-10-25  
**Branch:** feature/user-deck-creation  
**Status:** ✅ Complete

## Overview

Implemented the complete backend document processing pipeline for OpenDeck according to the plan at `.claude/plans/document-upload-deck-generation.md`. Users can now upload documents (PDF, DOCX, PPTX, TXT), which are processed asynchronously by Celery workers to generate AI-powered flashcards with source attribution.

---

## Files Created

### 1. `/backend/app/schemas/flashcard.py`
**Purpose:** Pydantic schemas for AI-generated flashcard data  
**Key Components:**
- `FlashcardData`: Schema for AI-generated flashcards with required source attribution
- `ProcessingResult`: Schema for document processing statistics

**Design Decisions:**
- Enforced source attribution at schema level (required field)
- Included difficulty levels (beginner/intermediate/advanced)
- Added comprehensive field validation

### 2. `/backend/app/services/document_processor.py`
**Purpose:** Orchestrates the document processing pipeline  
**Key Components:**
- `DocumentProcessorService`: Main service class
- `process_documents()`: Processes multiple documents for a deck
- `_extract_document_text()`: Extracts text using DocumentExtractor
- `_create_flashcard_records()`: Persists flashcards to database

**Design Decisions:**
- Async methods for I/O operations (storage access)
- Temporary file handling for document extraction libraries (require file paths)
- Granular error handling - failed documents don't block others
- Automatic deck card count updates
- Comprehensive structured logging throughout

**Dependencies:**
- `DocumentExtractor` (existing) - Text extraction from various formats
- `AIService` (existing) - Flashcard generation via OpenAI/Anthropic
- `StorageService` (existing) - File storage abstraction (local/S3)
- Database repositories for Document, Card, and Deck

### 3. `/backend/app/workers/tasks.py`
**Purpose:** Celery background tasks for async processing  
**Key Components:**
- `process_documents_task()`: Main Celery task with retry logic
- `cleanup_temp_files_task()`: Placeholder for future cleanup operations

**Design Decisions:**
- Exponential backoff retry strategy: 60s * (2^retry_number), max 3 retries
- Task state updates for progress tracking
- AsyncIO integration to call async processor methods
- Proper database session management (created and closed within task)
- Comprehensive error logging with retry tracking

**Configuration:**
- Task routing to dedicated "documents" queue
- Soft time limit: 10 minutes (configurable)
- Hard time limit: 15 minutes (configurable)
- Results expire after 1 hour

### 4. `/backend/app/api/documents.py`
**Purpose:** FastAPI endpoints for document upload and management  
**Key Endpoints:**

#### `POST /api/v1/documents/upload`
- Accepts multipart form data (files + metadata)
- Validates files (count, type, size) before processing
- Creates deck record immediately
- Saves files to storage (local or S3)
- Creates document records with UPLOADED status
- Queues Celery task for background processing
- Returns deck_id, document_ids, and task_id

**Validation Rules:**
- Max 10 files per upload
- Allowed types: PDF, DOCX, PPTX, TXT
- Max file size: 10MB per file
- Max total upload: 50MB
- User authentication required

#### `GET /api/v1/documents/{document_id}`
- Retrieves document details including processing status
- Authorization check (user owns document)

#### `GET /api/v1/documents`
- Lists user's documents with pagination
- Limit: max 100 results

**Design Decisions:**
- Fail-fast validation before any file processing
- Atomic deck creation (all files uploaded or none)
- Clear error messages with specific validation failures
- Immediate response with task ID for frontend polling
- Comprehensive logging for debugging

---

## Files Modified

### 1. `/backend/app/schemas/document.py`
**Changes:**
- Added `DocumentUploadResponse` schema for upload endpoint response
- Includes deck_id, document_ids, task_id, status, and message fields

### 2. `/backend/app/main.py`
**Changes:**
- Imported `documents` router
- Registered documents router with API v1 prefix
- Route: `/api/v1/documents/*`

### 3. `/backend/requirements.txt`
**Changes:**
- Added `tenacity==8.2.3` for AI service retry logic

---

## Architecture & Flow

### Document Upload Flow
```
1. User uploads files via POST /api/v1/documents/upload
2. API validates files (count, type, size)
3. API creates Deck record (status tracked via card_count)
4. API saves files to StorageService (local or S3)
5. API creates Document records (status: UPLOADED)
6. API queues Celery task
7. API returns immediately with task_id
```

### Background Processing Flow
```
1. Celery worker picks up task from "documents" queue
2. Task updates state to PROCESSING
3. For each document:
   a. Update document status to PROCESSING
   b. Retrieve file from storage
   c. Extract text (DocumentExtractor)
   d. Generate flashcards (AIService)
   e. Create Card records in database
   f. Update document status to COMPLETED or FAILED
4. Update deck card_count
5. Task returns ProcessingResult
```

### Error Handling
- **File Validation Errors:** Immediate HTTP 400 response
- **Storage Errors:** HTTP 500, logged, no retry
- **Processing Errors:** Document marked FAILED, other documents continue
- **AI Errors:** Retried up to 3 times via tenacity in AIService
- **Task Errors:** Retried up to 3 times with exponential backoff

---

## Key Design Principles

### 1. Source Attribution (CRITICAL)
- All flashcards MUST include source field per CLAUDE.md requirements
- Format: "DocumentName.pdf - Page X, Section Y"
- Validated at multiple levels:
  - Pydantic schema (FlashcardData)
  - Domain model (Card.__post_init__)
  - AI service parsing (adds default if missing)
  - Database constraint (NOT NULL)

### 2. Separation of Concerns
- **Storage Layer:** Abstract interface (local/S3)
- **Extraction Layer:** DocumentExtractor handles all file formats
- **AI Layer:** AIService handles OpenAI/Anthropic providers
- **Processing Layer:** DocumentProcessorService orchestrates
- **Task Layer:** Celery handles async execution
- **API Layer:** FastAPI handles HTTP, validation, routing

### 3. Dependency Injection
- All services accept dependencies via constructor
- FastAPI Depends() for request-scoped dependencies
- Factory functions for service creation
- Easy to mock for testing

### 4. Async/Await Patterns
- Storage operations are async (I/O bound)
- Document processing is async (calls storage)
- Celery tasks use asyncio.run() to execute async code
- Proper session management in sync/async boundary

### 5. Structured Logging
- All services use structlog
- Contextual information in every log (user_id, deck_id, document_id)
- Error types and retry counts logged
- Performance metrics (file sizes, processing times)

---

## Database Schema

### Existing Models (No Changes Required)
- `DeckModel`: Stores deck metadata, card_count tracks processing
- `DocumentModel`: Tracks upload and processing status
- `CardModel`: Stores flashcards with required source field
- `UserModel`: User authentication

### Status Tracking
```python
class DocumentStatus(Enum):
    UPLOADED = "uploaded"      # File saved to storage
    PROCESSING = "processing"  # Celery task running
    COMPLETED = "completed"    # Flashcards generated
    FAILED = "failed"          # Processing error
```

---

## Configuration (via Environment Variables)

### Storage
- `STORAGE_BACKEND`: "local" or "s3"
- `STORAGE_PATH`: "/tmp/opendeck/documents" (local only)
- `MAX_FILE_SIZE_MB`: 10
- `MAX_TOTAL_UPLOAD_SIZE_MB`: 50
- `MAX_FILES_PER_UPLOAD`: 10
- `ALLOWED_FILE_TYPES`: "pdf,docx,pptx,txt"

### Celery
- `CELERY_BROKER_URL`: "redis://localhost:6379/0"
- `CELERY_RESULT_BACKEND`: "redis://localhost:6379/0"
- `CELERY_TASK_SOFT_TIME_LIMIT`: 600 (10 minutes)
- `CELERY_TASK_TIME_LIMIT`: 900 (15 minutes)

### AI Services
- `AI_PROVIDER`: "openai" or "anthropic"
- `OPENAI_API_KEY`: API key (optional for mock mode)
- `OPENAI_MODEL`: "gpt-4"
- `ANTHROPIC_API_KEY`: API key (optional for mock mode)
- `ANTHROPIC_MODEL`: "claude-3-sonnet-20240229"
- `AI_MAX_RETRIES`: 3
- `AI_TIMEOUT_SECONDS`: 60

---

## Testing Strategy

### Unit Tests (TODO)
- `test_flashcard_schemas.py`: Validate FlashcardData, ProcessingResult
- `test_document_processor.py`: Mock storage, AI, repos
- `test_celery_tasks.py`: Mock processor, test retry logic
- `test_document_api.py`: Test validation, error cases

### Integration Tests (TODO)
- End-to-end upload flow with test files
- Celery task execution (requires Redis)
- Storage operations (local and S3 mocked)
- AI service with mocked API responses

### Load Tests (TODO)
- 10 concurrent uploads
- Large file handling (10MB)
- Queue processing under load

---

## Known Limitations & Future Work

### Current Limitations
1. **Mock AI Mode**: If API keys not configured, returns 3-5 mock flashcards
2. **No Progress Updates**: Frontend must poll task status (SSE/WebSocket planned)
3. **No Partial Retry**: Failed documents require re-uploading entire batch
4. **Limited File Formats**: Only PDF, DOCX, PPTX, TXT supported
5. **No OCR**: Scanned PDFs/images not processed
6. **No Cleanup Job**: cleanup_temp_files_task is a placeholder

### Future Enhancements (Phase 2+)
- [ ] Server-Sent Events (SSE) for real-time progress
- [ ] Partial retry for failed documents
- [ ] OCR support for scanned documents
- [ ] Multi-language support
- [ ] Custom AI prompts per deck
- [ ] Document preview extraction
- [ ] Batch operations (add to existing deck)
- [ ] AWS S3 migration
- [ ] AWS SQS instead of Redis
- [ ] CloudWatch monitoring
- [ ] Auto-scaling based on queue depth

---

## Dependencies Added

```txt
# Already in requirements.txt
fastapi==0.109.0
celery==5.3.4
redis==5.0.1
openai==1.6.1
anthropic==0.8.1
pdfplumber==0.11.0
python-docx==1.1.0
python-pptx==0.6.23
structlog==24.1.0
sqlalchemy==2.0.25
pydantic==2.5.3

# Added
tenacity==8.2.3  # Retry logic for AI services
```

---

## Deployment Checklist

### Development Environment
- [x] Redis running (docker-compose.yml)
- [x] Celery worker running: `celery -A app.workers.celery_app worker --loglevel=info`
- [x] Database migrations applied
- [x] Environment variables configured (.env)
- [x] Storage path created (/tmp/opendeck/documents)

### Production Environment (TODO)
- [ ] Configure AWS S3 bucket
- [ ] Set up SQS queue
- [ ] Deploy Celery workers to ECS/Fargate
- [ ] Configure auto-scaling
- [ ] Set up CloudWatch alarms
- [ ] Enable API rate limiting
- [ ] Configure CORS for production frontend
- [ ] Set up secrets manager for API keys

---

## API Examples

### Upload Documents
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer <token>" \
  -F "title=Biology 101" \
  -F "description=Cell biology flashcards" \
  -F "category=Biology" \
  -F "difficulty=beginner" \
  -F "files=@biology_chapter1.pdf" \
  -F "files=@biology_chapter2.pdf"

# Response
{
  "deck_id": "123e4567-e89b-12d3-a456-426614174000",
  "document_ids": [
    "223e4567-e89b-12d3-a456-426614174001",
    "323e4567-e89b-12d3-a456-426614174002"
  ],
  "task_id": "424e4567-e89b-12d3-a456-426614174003",
  "status": "queued",
  "message": "Documents uploaded successfully. Processing 2 document(s)."
}
```

### Check Document Status
```bash
curl -X GET "http://localhost:8000/api/v1/documents/223e4567-e89b-12d3-a456-426614174001" \
  -H "Authorization: Bearer <token>"

# Response
{
  "id": "223e4567-e89b-12d3-a456-426614174001",
  "user_id": "user123",
  "filename": "biology_chapter1.pdf",
  "file_path": "user123/deck123/20251025_123456_biology_chapter1.pdf",
  "status": "completed",
  "deck_id": "123e4567-e89b-12d3-a456-426614174000",
  "processed_at": "2025-10-25T12:35:00Z",
  "error_message": null,
  "created_at": "2025-10-25T12:34:00Z",
  "updated_at": "2025-10-25T12:35:00Z"
}
```

---

## Success Metrics

### MVP Goals (Achieved)
- ✅ Users can upload up to 10 documents per request
- ✅ System processes documents asynchronously
- ✅ All flashcards include source attribution
- ✅ Proper error handling and retry logic
- ✅ Supports multiple file formats (PDF, DOCX, PPTX, TXT)
- ✅ Configurable for local development and future AWS deployment

### Next Steps
- Frontend integration (Angular component)
- Task status polling endpoint
- Comprehensive test suite
- Performance benchmarking
- Production deployment preparation

---

## Conclusion

The backend document processing pipeline is fully implemented and ready for frontend integration. The architecture follows clean code principles with proper separation of concerns, comprehensive error handling, and full support for the required file formats. The system is designed to scale from local development (Redis + local storage) to production (SQS + S3) with minimal code changes.

All flashcards include mandatory source attribution as per CLAUDE.md requirements, ensuring users can verify and corroborate AI-generated content.
