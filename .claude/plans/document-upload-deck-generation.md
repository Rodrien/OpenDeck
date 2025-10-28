# Document Upload & Deck Generation - Implementation Plan

**Status**: In Progress
**Branch**: `feature/user-deck-creation`
**Date Created**: 2025-10-20

## Architecture Overview

**Flow**: User uploads documents → Storage (Local/S3) → Background processing queue (Celery/SQS) → AI service processes files → Flashcards generated → Deck created

---

## Phase 1: Core Upload Infrastructure ✓ IN PROGRESS

### Frontend (Angular + PrimeNG)

#### 1. Create Document Upload Component
- **Location**: `opendeck-portal/src/app/pages/flashcards/deck-upload/`
- **Component**: `deck-upload.component.ts`
- **Template**: `deck-upload.component.html`
- **Features**:
  - PrimeNG `FileUpload` component with:
    - Multi-file support (max 10 files)
    - File type validation (PDF, DOCX, PPTX, TXT)
    - File size validation (10MB per file, 50MB total)
    - Progress tracking for each file
    - Preview of selected files with remove option

#### 2. Upload Form Fields
- **Deck Metadata Inputs**:
  - Title (required) - `pInputText`
  - Description (optional) - `pTextarea`
  - Category/Subject (required) - `pDropdown`
  - Difficulty level - `pDropdown` (beginner/intermediate/advanced)
- **File Upload Area** - `pFileUpload`
- **Submit Button** - `pButton` (disabled until validation passes)

#### 3. Upload Service
- **Location**: `src/app/services/document.service.ts`
- **Methods**:
  ```typescript
  uploadDocuments(files: File[], metadata: DeckMetadata): Observable<UploadResponse>
  getProcessingStatus(documentIds: string[]): Observable<DocumentStatus[]>
  pollProcessingStatus(documentIds: string[]): Observable<DocumentStatus[]>
  getDocumentById(id: string): Observable<Document>
  ```

### Backend (FastAPI)

#### 4. File Upload API Endpoint
```
POST /api/v1/documents/upload
```
- **Request**: Multipart form data
  - `files`: List of files (up to 10)
  - `metadata`: JSON string with deck metadata
- **Response**:
  ```json
  {
    "deck_id": "uuid",
    "document_ids": ["uuid1", "uuid2"],
    "status": "queued",
    "message": "Documents uploaded successfully. Processing started."
  }
  ```
- **Validation**:
  - File count (max 10)
  - File types (PDF, DOCX, PPTX, TXT)
  - File sizes (10MB per file, 50MB total)
  - User authentication required

#### 5. File Storage Strategy

**Phase 1 (Current - Local Storage)**:
- **Path**: `/tmp/opendeck/documents/{user_id}/{deck_id}/`
- **Filename Format**: `{timestamp}_{sanitized_original_name}`
- **Pros**: Simple, no external dependencies
- **Cons**: Not persistent, doesn't scale
- **Use Case**: Development and testing

**Phase 2 (AWS S3 - Production)**:
- **Bucket Structure**: `opendeck-documents/{env}/{user_id}/{deck_id}/`
- **Features**:
  - Use presigned URLs for secure uploads
  - Lifecycle policies: Move to Glacier after 90 days, delete after 1 year
  - Server-side encryption (SSE-S3 or SSE-KMS)
- **Pros**: Scalable, durable, CDN-ready
- **Migration Path**: Swap StorageService implementation, no business logic changes

#### 6. Storage Abstraction Layer

**Location**: `backend/app/services/storage_service.py`

```python
from abc import ABC, abstractmethod
from fastapi import UploadFile

class StorageService(ABC):
    """Abstract storage interface for file operations."""

    @abstractmethod
    async def upload_file(self, file: UploadFile, path: str) -> str:
        """Upload file and return storage path."""
        pass

    @abstractmethod
    async def get_file(self, path: str) -> bytes:
        """Retrieve file contents."""
        pass

    @abstractmethod
    async def delete_file(self, path: str) -> bool:
        """Delete file from storage."""
        pass

    @abstractmethod
    async def get_file_url(self, path: str, expiration: int = 3600) -> str:
        """Get temporary URL for file access."""
        pass

class LocalStorageService(StorageService):
    """Local filesystem storage implementation."""
    # Implementation for local development

class S3StorageService(StorageService):
    """AWS S3 storage implementation."""
    # Implementation for production (boto3)
```

**Configuration**: Use factory pattern to select storage backend based on `settings.storage_backend`

#### 7. Document Processing Workflow - QUEUE BASED (Option B) ✓ SELECTED

**Architecture**: Celery + Redis/SQS

**Components**:
- **Celery Worker**: Background task processor
- **Broker**: Redis (local/development) or SQS (AWS/production)
- **Result Backend**: Redis for task status tracking

**Setup Files**:
- `backend/app/workers/celery_app.py` - Celery configuration
- `backend/app/workers/tasks.py` - Task definitions
- `backend/app/workers/__init__.py` - Worker initialization

**Task Flow**:
```python
# app/workers/tasks.py
from app.workers.celery_app import celery_app

@celery_app.task(bind=True, max_retries=3)
def process_documents_task(self, deck_id: str, document_ids: list[str]):
    """
    Celery task to process uploaded documents and generate flashcards.

    Args:
        deck_id: UUID of the deck being created
        document_ids: List of document UUIDs to process

    Retries: 3 attempts with exponential backoff
    """
    try:
        # Update task status
        self.update_state(state='PROCESSING', meta={'current': 0, 'total': len(document_ids)})

        # Process documents
        processor = DocumentProcessorService()
        result = await processor.process_documents(deck_id, document_ids)

        return {
            'status': 'completed',
            'deck_id': deck_id,
            'cards_generated': result.total_cards
        }
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

**API Integration**:
```python
# app/api/documents.py
@router.post("/upload")
async def upload_documents(
    files: list[UploadFile],
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form(...),
    difficulty: str = Form(...),
    current_user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
    db: Session = Depends(get_db)
):
    # 1. Validate files
    validate_upload_request(files)

    # 2. Create deck record (status: PENDING)
    deck = create_deck(user_id=current_user.id, title=title, ...)

    # 3. Save files to storage
    document_ids = []
    for file in files:
        path = await storage.upload_file(file, f"{current_user.id}/{deck.id}/{file.filename}")
        doc = create_document(user_id=current_user.id, deck_id=deck.id, file_path=path)
        document_ids.append(doc.id)

    # 4. Queue processing task
    task = process_documents_task.delay(deck.id, document_ids)

    # 5. Return response immediately
    return {
        "deck_id": deck.id,
        "document_ids": document_ids,
        "task_id": task.id,
        "status": "queued"
    }
```

**Benefits of Queue-based Approach**:
- ✓ Retry logic with exponential backoff
- ✓ Task status tracking and progress updates
- ✓ Distributed processing (multiple workers)
- ✓ Rate limiting and throttling
- ✓ Easy migration to SQS for AWS deployment
- ✓ Failure isolation (failed tasks don't block API)

#### 8. Document Processing Service

**Location**: `backend/app/services/document_processor.py`

**Responsibilities**:
1. Extract text from documents (PDF, DOCX, PPTX, TXT)
2. Send content to AI service
3. Parse AI-generated flashcards
4. Create card records with source attribution
5. Update deck statistics
6. Handle errors and update document status

**Libraries**:
- `PyPDF2` or `pdfplumber` - PDF text extraction
- `python-docx` - Word document parsing
- `python-pptx` - PowerPoint parsing

**Implementation**:
```python
class DocumentProcessorService:
    def __init__(self, storage: StorageService, ai: AIService):
        self.storage = storage
        self.ai = ai

    async def process_documents(
        self,
        deck_id: str,
        document_ids: list[str]
    ) -> ProcessingResult:
        """Process documents and generate flashcards."""

        total_cards = 0

        for doc_id in document_ids:
            try:
                # Update status to PROCESSING
                doc = update_document_status(doc_id, DocumentStatus.PROCESSING)

                # Extract text content
                content = await self._extract_text(doc)

                # Generate flashcards via AI
                flashcards = await self.ai.generate_flashcards(
                    content=content,
                    document_name=doc.filename,
                    deck_id=deck_id
                )

                # Create card records
                for card_data in flashcards:
                    create_card(
                        deck_id=deck_id,
                        question=card_data.question,
                        answer=card_data.answer,
                        source=card_data.source  # CRITICAL: Source attribution
                    )
                    total_cards += 1

                # Mark document as completed
                update_document_status(doc_id, DocumentStatus.COMPLETED)

            except Exception as e:
                # Mark document as failed
                update_document_status(
                    doc_id,
                    DocumentStatus.FAILED,
                    error_message=str(e)
                )
                logger.error(f"Failed to process document {doc_id}: {e}")

        # Update deck card count
        update_deck_card_count(deck_id, total_cards)

        return ProcessingResult(total_cards=total_cards)

    async def _extract_text(self, document: Document) -> str:
        """Extract text from document based on file type."""
        file_bytes = await self.storage.get_file(document.file_path)

        if document.filename.endswith('.pdf'):
            return extract_pdf_text(file_bytes)
        elif document.filename.endswith('.docx'):
            return extract_docx_text(file_bytes)
        elif document.filename.endswith('.pptx'):
            return extract_pptx_text(file_bytes)
        elif document.filename.endswith('.txt'):
            return file_bytes.decode('utf-8')
        else:
            raise ValueError(f"Unsupported file type: {document.filename}")
```

#### 9. AI Integration Service

**Location**: `backend/app/services/ai_service.py`

**Provider Support**:
- OpenAI (GPT-4, GPT-4 Turbo)
- Anthropic Claude (Claude 3 Sonnet, Opus)
- Future: AWS Bedrock, Cohere

**Prompt Engineering**:
```python
FLASHCARD_GENERATION_PROMPT = """
You are an expert educational content creator. Generate high-quality flashcards from the provided document content.

Requirements:
1. Create clear, concise question-answer pairs
2. Focus on key concepts, definitions, and important facts
3. Include source attribution for EVERY card (document name, page number, section)
4. Organize by difficulty: beginner → intermediate → advanced
5. Aim for {target_cards} flashcards

Document: {document_name}
Content:
{content}

Return JSON array:
[
  {
    "question": "What is...",
    "answer": "...",
    "source": "{document_name} - Page 5, Section 2.1",
    "difficulty": "beginner"
  }
]
"""
```

**Implementation**:
```python
class AIService:
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        # Initialize API client based on settings

    async def generate_flashcards(
        self,
        content: str,
        document_name: str,
        deck_id: str,
        target_cards: int = 20
    ) -> list[FlashcardData]:
        """Generate flashcards from document content using AI."""

        prompt = FLASHCARD_GENERATION_PROMPT.format(
            document_name=document_name,
            content=content[:10000],  # Limit content size
            target_cards=target_cards
        )

        if self.provider == "openai":
            response = await self._call_openai(prompt)
        elif self.provider == "anthropic":
            response = await self._call_anthropic(prompt)

        # Parse and validate response
        flashcards = self._parse_flashcards(response)

        # Validate source attribution
        for card in flashcards:
            if not card.source or document_name not in card.source:
                raise ValueError("Missing or invalid source attribution")

        return flashcards
```

---

## Phase 2: Real-time Updates & UI

### 10. WebSocket/SSE for Progress Updates
- Implement Server-Sent Events (SSE) endpoint
- Frontend subscribes to processing events
- Real-time progress: "Processing document 2 of 5... Generated 15 cards"

### 11. Status Polling API
```
GET /api/v1/documents/{document_id}/status
GET /api/v1/decks/{deck_id}/processing-status
GET /api/v1/tasks/{task_id}/status  # Celery task status
```

---

## Phase 3: Enhanced Features

### 12. Document Preview
- Extract first page/section as preview
- Show in upload confirmation dialog

### 13. Batch Operations
- Add more documents to existing deck
- Re-process failed documents
- Bulk delete

### 14. Document Management
- List user's uploaded documents
- Delete documents
- Download original files
- View processing history

---

## Database Migrations

### Required Alembic Migration
```python
# 20251020_add_document_indexes.py
def upgrade():
    op.create_index('ix_documents_status', 'documents', ['status'])
    op.create_index('ix_documents_deck_id', 'documents', ['deck_id'])
    op.create_index('ix_documents_user_id_status', 'documents', ['user_id', 'status'])
```

---

## Security Considerations

### File Upload Security
- ✓ Validate MIME types server-side (don't trust client)
- ✓ Scan for malware (ClamAV integration - future)
- ✓ Strict file size limits (10MB per file, 50MB total)
- ✓ Sanitize filenames (remove special characters, path traversal)
- ✓ Rate limiting per user (max 5 uploads per hour)
- ✓ Authenticated uploads only

### Storage Security
**Local Storage**:
- File permissions (600 for files, 700 for directories)
- User isolation (separate directories)

**S3 Storage**:
- Use IAM roles, not access keys
- Encrypt files at rest (SSE-S3 or SSE-KMS)
- Presigned URLs with short expiration (1 hour)
- CORS policies for browser uploads
- Bucket policies to restrict access

---

## Infrastructure Requirements

### Development Environment
```yaml
# docker-compose.yml additions
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data

celery_worker:
  build: ./backend
  command: celery -A app.workers.celery_app worker --loglevel=info
  depends_on:
    - redis
    - db
  volumes:
    - ./backend/app:/app/app
```

### Production Environment (AWS)
- **Compute**: ECS/Fargate for API and Celery workers
- **Queue**: Amazon SQS (broker) + ElastiCache Redis (result backend)
- **Storage**: S3 for documents
- **Database**: RDS PostgreSQL
- **Monitoring**: CloudWatch, DataDog
- **Scaling**: Auto-scaling based on queue depth

---

## Testing Strategy

### Unit Tests
- Storage service tests (mock file operations)
- Document processor tests (mock AI calls)
- AI service tests (mock API responses)
- Celery task tests (mock dependencies)

### Integration Tests
- End-to-end upload flow
- Document processing pipeline
- Error handling and retries
- File type validation

### Load Tests
- Concurrent uploads (10 users, 10 files each)
- Large file handling (10MB files)
- Queue processing under load

---

## Monitoring & Observability

### Metrics
- Upload success/failure rates
- Processing time per document
- Queue depth and latency
- AI API response times
- Storage usage

### Logging
- Structured logging (JSON format)
- Log levels: DEBUG (dev), INFO (prod)
- Contextual logging (user_id, deck_id, document_id, task_id)

### Alerts
- Failed processing tasks (> 10% failure rate)
- High queue depth (> 100 pending tasks)
- AI API errors
- Storage quota warnings

---

## Implementation Timeline

### Week 1: Infrastructure Setup
- ✓ Storage abstraction layer
- ✓ Celery configuration
- ✓ Redis setup
- ✓ Basic upload API
- ✓ Local storage implementation

### Week 2: Processing Pipeline
- Document text extraction
- AI service integration
- Celery tasks
- Error handling and retries

### Week 3: Frontend & UX
- Upload component
- File validation
- Progress tracking
- Status polling

### Week 4: Testing & Refinement
- Unit and integration tests
- Load testing
- Bug fixes
- Documentation

---

## Future Enhancements

### Phase 4: Advanced Features
- OCR for scanned documents/images
- Multi-language support
- Custom AI prompts per deck
- Collaborative deck creation
- Version control for flashcards

### Phase 5: AWS Migration
- S3 storage
- SQS + Lambda for processing
- Cognito for authentication
- CloudFront CDN
- Cost optimization

---

## Success Metrics

### MVP Goals (Phase 1)
- Users can upload up to 10 documents
- System generates flashcards within 5 minutes
- 95% upload success rate
- Source attribution on all cards

### Production Goals (Phase 2-3)
- 99.9% uptime
- < 1 minute average processing time
- Support 1000+ concurrent users
- < $0.10 per deck in processing costs

---

## References

- [OpenDeck Project Documentation](../CLAUDE.md)
- [Celery Documentation](https://docs.celeryq.dev/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
- [PrimeNG FileUpload](https://primeng.org/fileupload)
