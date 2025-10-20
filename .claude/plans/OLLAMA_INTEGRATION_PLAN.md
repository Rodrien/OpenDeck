# Ollama Integration Architecture Plan

## Current State Analysis

Your backend already has excellent foundations:
- **Document model** with status tracking (UPLOADED, PROCESSING, COMPLETED, FAILED) at backend/app/core/models.py:22-28
- **Celery/Redis configuration** ready in backend/app/config.py:77-78 (currently commented)
- **Workers directory** structure at backend/app/workers/
- **Storage configuration** for local and S3 at backend/app/config.py:71-74

## Architecture Overview

```
┌─────────────────┐
│  Angular Frontend│
│   (Upload UI)   │
└────────┬────────┘
         │ HTTP POST
         ▼
┌─────────────────┐
│  FastAPI Backend│
│  /api/v1/docs   │◄──────────┐
└────────┬────────┘           │
         │                    │ POST flashcards
         │ Enqueue task       │
         ▼                    │
┌─────────────────┐           │
│  Redis Queue    │           │
└────────┬────────┘           │
         │                    │
         │ Pull jobs          │
         ▼                    │
┌─────────────────┐           │
│  Celery Worker  │           │
│  (Linux/Mac)    │           │
└────────┬────────┘           │
         │                    │
         │ HTTP POST          │
         ▼                    │
┌─────────────────┐           │
│ Ollama Service  │           │
│ (Windows + GPU) │───────────┘
│  Custom Model   │
└─────────────────┘
```

## Implementation Plan

### Phase 1: Infrastructure Setup

**1. Install Dependencies**

Uncomment in backend/requirements.txt:
```python
celery==5.3.4
redis==5.0.1

# For document processing:
PyPDF2==3.0.1
python-docx==1.1.0
python-pptx==0.6.23  # For PowerPoint
Pillow==10.1.0       # For image extraction

# For Ollama communication:
httpx==0.26.0  # Already in requirements
```

**2. Environment Configuration**

Add to `.env`:
```bash
# Redis/Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Ollama Configuration
OLLAMA_HOST=http://your-windows-machine-ip:11434
OLLAMA_MODEL=your-custom-model-name
OLLAMA_TIMEOUT=300  # 5 minutes for large documents
OLLAMA_MAX_RETRIES=3

# Document Processing
MAX_DOCUMENT_SIZE_MB=50
SUPPORTED_FORMATS=pdf,docx,pptx,txt
```

**3. Update Configuration File**

Add to backend/app/config.py:
```python
# Ollama Configuration
ollama_host: str = "http://localhost:11434"
ollama_model: str = "flashcard-generator"
ollama_timeout: int = 300
ollama_max_retries: int = 3

# Document Processing
max_document_size_mb: int = 50
supported_formats: str = "pdf,docx,pptx,txt"
```

### Phase 2: Core Components

**1. Document Upload API**

Create `backend/app/api/documents.py`:
```python
from fastapi import APIRouter, UploadFile, Depends, HTTPException, File
from app.workers.tasks import process_document_task
from app.api.dependencies import get_current_user_id
from app.config import settings
import uuid
from pathlib import Path

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    deck_title: str | None = None
):
    """
    Upload a document for flashcard generation.

    Workflow:
    1. Validate file type and size
    2. Save to storage (local or S3)
    3. Create Document record (status=UPLOADED)
    4. Enqueue Celery task for processing
    """
    # 1. Validate file
    file_ext = Path(file.filename).suffix.lower()
    supported = settings.supported_formats.split(',')
    if file_ext.replace('.', '') not in supported:
        raise HTTPException(400, f"Unsupported file type. Supported: {supported}")

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset
    max_size = settings.max_document_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(400, f"File too large. Max size: {settings.max_document_size_mb}MB")

    # 2. Save file
    document_id = str(uuid.uuid4())
    file_path = Path(settings.storage_path) / user_id / f"{document_id}{file_ext}"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'wb') as f:
        f.write(await file.read())

    # 3. Create Document record
    # (Use your repository pattern to create document in database)

    # 4. Enqueue Celery task
    task = process_document_task.delay(document_id, user_id, deck_title)

    return {
        "document_id": document_id,
        "task_id": str(task.id),
        "status": "queued",
        "filename": file.filename
    }

@router.get("/{document_id}/status")
async def get_processing_status(
    document_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get the current processing status of a document."""
    # Fetch document from database and return status
    # (Use your repository pattern)
    pass
```

**2. Celery Configuration**

Create `backend/app/workers/celery_app.py`:
```python
from celery import Celery
from app.config import settings

celery_app = Celery(
    "opendeck",
    broker=settings.celery_broker_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max
    task_soft_time_limit=540,  # 9 minutes warning
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.workers'])
```

**3. Document Processing Task**

Create `backend/app/workers/tasks.py`:
```python
from celery import Task
from app.workers.celery_app import celery_app
from app.workers.ollama_client import OllamaClient
from app.workers.document_processor import DocumentProcessor
from app.config import settings
from app.core.models import DocumentStatus
import structlog

logger = structlog.get_logger()

class CallbackTask(Task):
    """Base task with callbacks for status updates."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        document_id = args[0]
        logger.error("task_failed", document_id=document_id, error=str(exc))
        # Update Document status to FAILED
        # update_document_status(document_id, DocumentStatus.FAILED, error_message=str(exc))

@celery_app.task(base=CallbackTask, bind=True, name="process_document")
def process_document_task(self, document_id: str, user_id: str, deck_title: str = None):
    """
    Main task for processing documents with Ollama.

    Workflow:
    1. Fetch document from database
    2. Extract text from document
    3. Send to Ollama for flashcard generation
    4. Create deck and cards via API
    5. Update document status
    """
    logger.info("processing_document_started", document_id=document_id)

    try:
        # 1. Update status to PROCESSING
        # document = get_document(document_id)
        # update_document_status(document_id, DocumentStatus.PROCESSING)

        # 2. Extract document text
        processor = DocumentProcessor()
        # document_path = document.file_path
        # filename = document.filename
        # extracted_text = processor.extract_text(document_path, filename)

        # 3. Send to Ollama
        ollama = OllamaClient(
            host=settings.ollama_host,
            model=settings.ollama_model,
            timeout=settings.ollama_timeout
        )

        # flashcards = ollama.generate_flashcards(
        #     text=extracted_text,
        #     filename=filename,
        #     user_context={"deck_title": deck_title}
        # )

        # 4. Create deck via internal API
        # deck_id = create_deck_with_cards(
        #     user_id=user_id,
        #     title=deck_title or f"Flashcards from {filename}",
        #     cards=flashcards,
        #     document_id=document_id
        # )

        # 5. Update document status
        # update_document_status(
        #     document_id,
        #     DocumentStatus.COMPLETED,
        #     deck_id=deck_id
        # )

        logger.info("processing_document_completed", document_id=document_id)
        # return {"status": "success", "deck_id": deck_id}

    except Exception as e:
        logger.error("processing_document_failed", document_id=document_id, error=str(e))
        # update_document_status(
        #     document_id,
        #     DocumentStatus.FAILED,
        #     error_message=str(e)
        # )
        raise

@celery_app.task(bind=True, name="health_check")
def health_check_task(self):
    """Simple health check task for Celery."""
    return {"status": "healthy", "worker_id": self.request.hostname}
```

**4. Ollama Client**

Create `backend/app/workers/ollama_client.py`:
```python
import httpx
from typing import List, Dict
import structlog
import json

logger = structlog.get_logger()

class OllamaClient:
    """Client for communicating with Ollama API."""

    def __init__(self, host: str, model: str, timeout: int = 300):
        self.host = host.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def generate_flashcards(
        self,
        text: str,
        filename: str,
        user_context: Dict = None
    ) -> List[Dict]:
        """
        Generate flashcards from document text.

        Args:
            text: Extracted document text with page markers
            filename: Original document filename
            user_context: Optional user preferences (deck_title, etc.)

        Returns:
            List of flashcard dicts with:
            - question: str
            - answer: str
            - source: str (e.g., "Biology101.pdf - Page 5")
            - topics: List[str] (optional)
        """
        prompt = self._build_prompt(text, filename, user_context or {})

        logger.info("ollama_generation_started", filename=filename, model=self.model)

        try:
            response = self.client.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",  # Request structured JSON output
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                }
            )
            response.raise_for_status()

            result = response.json()
            flashcards = self._parse_response(result["response"], filename)

            logger.info("ollama_generation_complete",
                       card_count=len(flashcards),
                       filename=filename)

            return flashcards

        except httpx.HTTPError as e:
            logger.error("ollama_request_failed", error=str(e), filename=filename)
            raise
        except Exception as e:
            logger.error("ollama_unexpected_error", error=str(e), filename=filename)
            raise

    def _build_prompt(self, text: str, filename: str, context: Dict) -> str:
        """Build the prompt for Ollama with source attribution requirements."""
        deck_title = context.get('deck_title', 'Study Materials')

        return f"""You are an expert at creating educational flashcards from course materials.

Document: {filename}
Deck Title: {deck_title}

Content:
{text}

Generate comprehensive flashcards following these rules:
1. Each flashcard must have a clear, concise question and a detailed, accurate answer
2. CRITICAL: Include precise source attribution in format "{{filename}} - Page {{page}}, Section {{section}}"
3. Extract key concepts, definitions, formulas, relationships, and important facts
4. Create questions that test understanding, not just memorization
5. Ensure answers are self-contained and don't require referring to the source
6. Identify relevant topics/tags for each card

Format your output as a JSON array with this exact structure:
[
  {{
    "question": "What is...",
    "answer": "A detailed explanation...",
    "source": "{filename} - Page 5, Section 2.1",
    "topics": ["Biology", "Cell Structure"]
  }},
  ...
]

Generate 10-30 high-quality flashcards covering all major concepts in the document.
Focus on creating cards that will genuinely help students learn and retain the material.
"""

    def _parse_response(self, response: str, filename: str) -> List[Dict]:
        """Parse Ollama response and validate structure."""
        try:
            # Try direct JSON parsing
            flashcards = json.loads(response)
        except json.JSONDecodeError:
            # Fallback: extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```json\s*(\[.*?\])\s*```', response, re.DOTALL)
            if json_match:
                flashcards = json.loads(json_match.group(1))
            else:
                # Try to find array in response
                array_match = re.search(r'\[.*\]', response, re.DOTALL)
                if array_match:
                    flashcards = json.loads(array_match.group(0))
                else:
                    logger.error("failed_to_parse_ollama_response", response=response[:500])
                    raise ValueError("Could not parse flashcards from Ollama response")

        # Validate each flashcard
        validated = []
        for i, card in enumerate(flashcards):
            if self._validate_card(card):
                # Ensure source includes filename if missing
                if filename not in card['source']:
                    card['source'] = f"{filename} - {card['source']}"
                validated.append(card)
            else:
                logger.warning("invalid_card_skipped", card_index=i, card=card)

        if not validated:
            raise ValueError("No valid flashcards generated")

        return validated

    def _validate_card(self, card: Dict) -> bool:
        """Ensure card has required fields and source attribution."""
        required = ["question", "answer", "source"]
        has_required = all(field in card and card[field] for field in required)

        if not has_required:
            return False

        # Validate minimum lengths
        if len(card['question']) < 5 or len(card['answer']) < 5:
            return False

        # Validate source format
        if len(card['source']) < 5:
            return False

        return True

    def check_health(self) -> Dict:
        """Check if Ollama service is accessible."""
        try:
            response = self.client.get(f"{self.host}/api/tags", timeout=5)
            response.raise_for_status()
            return {"status": "healthy", "models": response.json()}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
```

**5. Document Processor**

Create `backend/app/workers/document_processor.py`:
```python
from pathlib import Path
import PyPDF2
import docx
from pptx import Presentation
import structlog

logger = structlog.get_logger()

class DocumentProcessor:
    """Extract text from various document formats."""

    def extract_text(self, file_path: str, filename: str) -> str:
        """
        Extract text from document based on file type.

        Args:
            file_path: Full path to the document
            filename: Original filename (used to determine type)

        Returns:
            Extracted text with page/slide markers
        """
        suffix = Path(filename).suffix.lower()

        extractors = {
            '.pdf': self._extract_pdf,
            '.docx': self._extract_docx,
            '.pptx': self._extract_pptx,
            '.txt': self._extract_txt,
        }

        extractor = extractors.get(suffix)
        if not extractor:
            raise ValueError(f"Unsupported file type: {suffix}")

        logger.info("extracting_text", filename=filename, type=suffix)

        try:
            text = extractor(file_path)
            logger.info("text_extracted", filename=filename, length=len(text))
            return text
        except Exception as e:
            logger.error("extraction_failed", filename=filename, error=str(e))
            raise

    def _extract_pdf(self, path: str) -> str:
        """Extract text from PDF with page numbers."""
        text_parts = []
        try:
            with open(path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                total_pages = len(reader.pages)

                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    if text.strip():  # Only include non-empty pages
                        text_parts.append(f"[Page {page_num} of {total_pages}]\n{text}\n")

                logger.info("pdf_extracted", total_pages=total_pages)
        except Exception as e:
            logger.error("pdf_extraction_error", error=str(e))
            raise

        return "\n".join(text_parts)

    def _extract_docx(self, path: str) -> str:
        """Extract text from Word document."""
        try:
            doc = docx.Document(path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]

            # Also extract from tables
            table_text = []
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text for cell in row.cells]
                    table_text.append(" | ".join(row_text))

            if table_text:
                paragraphs.append("\n[Tables]\n" + "\n".join(table_text))

            logger.info("docx_extracted", paragraphs=len(paragraphs))
            return "\n\n".join(paragraphs)
        except Exception as e:
            logger.error("docx_extraction_error", error=str(e))
            raise

    def _extract_pptx(self, path: str) -> str:
        """Extract text from PowerPoint."""
        try:
            prs = Presentation(path)
            text_parts = []

            for slide_num, slide in enumerate(prs.slides, 1):
                slide_text = []
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_text.append(shape.text)

                if slide_text:
                    text_parts.append(
                        f"[Slide {slide_num} of {len(prs.slides)}]\n" +
                        "\n".join(slide_text)
                    )

            logger.info("pptx_extracted", total_slides=len(prs.slides))
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error("pptx_extraction_error", error=str(e))
            raise

    def _extract_txt(self, path: str) -> str:
        """Extract text from plain text file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            logger.info("txt_extracted", length=len(content))
            return content
        except UnicodeDecodeError:
            # Try with different encoding
            with open(path, 'r', encoding='latin-1') as f:
                content = f.read()
            logger.warning("txt_extracted_with_fallback_encoding")
            return content
```

**6. Task Monitoring API**

Add to `backend/app/api/tasks.py`:
```python
from fastapi import APIRouter
from app.workers.celery_app import celery_app

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """
    Check Celery task status.

    Returns:
        - task_id: The task identifier
        - status: PENDING, STARTED, SUCCESS, FAILURE, RETRY
        - result: Task result if completed
        - error: Error message if failed
    """
    task = celery_app.AsyncResult(task_id)

    response = {
        "task_id": task_id,
        "status": task.status,
        "ready": task.ready(),
    }

    if task.ready():
        if task.successful():
            response["result"] = task.result
        elif task.failed():
            response["error"] = str(task.info)

    return response

@router.get("/")
async def list_active_tasks():
    """List all active tasks."""
    # This requires celery events to be enabled
    inspect = celery_app.control.inspect()

    return {
        "active": inspect.active(),
        "scheduled": inspect.scheduled(),
        "reserved": inspect.reserved(),
    }
```

**7. Health Check Endpoint**

Add to `backend/app/api/health.py`:
```python
from app.workers.ollama_client import OllamaClient
from app.config import settings

@router.get("/health/ollama")
async def ollama_health():
    """Check Ollama service health."""
    try:
        client = OllamaClient(
            host=settings.ollama_host,
            model=settings.ollama_model,
            timeout=5
        )
        health = client.check_health()
        return health
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@router.get("/health/celery")
async def celery_health():
    """Check Celery worker health."""
    from app.workers.celery_app import celery_app

    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()

        if stats:
            return {"status": "healthy", "workers": list(stats.keys())}
        else:
            return {"status": "unhealthy", "error": "No workers available"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Phase 3: Deployment & Running

**1. Start Redis**
```bash
# Using Docker
docker run -d -p 6379:6379 --name opendeck-redis redis:7-alpine

# Or using Homebrew (Mac)
brew install redis
brew services start redis
```

**2. Start Ollama on Windows Machine**
```bash
# On Windows machine:
ollama serve

# Load your custom model:
ollama pull your-custom-model

# Or create from Modelfile:
ollama create flashcard-generator -f Modelfile
```

**3. Start Celery Worker**
```bash
cd backend

# Development (single worker, auto-reload)
celery -A app.workers.celery_app worker --loglevel=info --concurrency=2 --pool=solo

# Production (multiple workers)
celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
```

**4. Start FastAPI Backend**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**5. Monitor Celery (Optional)**
```bash
# Flower - Celery monitoring tool
pip install flower
celery -A app.workers.celery_app flower --port=5555
# Access at http://localhost:5555
```

### Phase 4: Frontend Integration

**1. Upload Component (Angular)**
```typescript
// document-upload.service.ts
export class DocumentUploadService {
  uploadDocument(file: File, deckTitle?: string): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (deckTitle) {
      formData.append('deck_title', deckTitle);
    }

    return this.http.post<UploadResponse>(
      `${this.apiUrl}/documents/upload`,
      formData
    );
  }

  checkStatus(documentId: string): Observable<DocumentStatus> {
    return this.http.get<DocumentStatus>(
      `${this.apiUrl}/documents/${documentId}/status`
    );
  }

  pollStatus(documentId: string): Observable<DocumentStatus> {
    return interval(2000).pipe(
      switchMap(() => this.checkStatus(documentId)),
      takeWhile(status =>
        status.status === 'UPLOADED' || status.status === 'PROCESSING',
        true  // Include final status
      )
    );
  }
}
```

**2. Upload Component Template**
```html
<!-- document-upload.component.html -->
<div class="upload-container">
  <p-fileUpload
    mode="advanced"
    [customUpload]="true"
    (uploadHandler)="onUpload($event)"
    [multiple]="false"
    accept=".pdf,.docx,.pptx,.txt"
    [maxFileSize]="52428800"
    chooseLabel="Select Document"
    uploadLabel="Generate Flashcards">
  </p-fileUpload>

  <div *ngIf="uploadStatus" class="status-indicator">
    <p-progressBar
      *ngIf="uploadStatus.status === 'PROCESSING'"
      mode="indeterminate">
    </p-progressBar>

    <p-message
      *ngIf="uploadStatus.status === 'COMPLETED'"
      severity="success"
      text="Flashcards generated successfully!">
    </p-message>

    <p-message
      *ngIf="uploadStatus.status === 'FAILED'"
      severity="error"
      [text]="uploadStatus.error_message">
    </p-message>
  </div>
</div>
```

### Phase 5: Monitoring & Error Handling

**1. Comprehensive Logging**
```python
# Add to all components
logger.info("operation_name", key1=value1, key2=value2)
logger.error("error_name", error=str(e), context=context)
```

**2. Retry Configuration**
```python
@celery_app.task(
    bind=True,
    autoretry_for=(httpx.HTTPError, ConnectionError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_jitter=True
)
def process_document_task(self, ...):
    # Task implementation
    pass
```

**3. Dead Letter Queue**
```python
# In celery_app.py
celery_app.conf.task_reject_on_worker_lost = True
celery_app.conf.task_acks_late = True

# Failed tasks will be requeued unless max_retries reached
```

**4. Monitoring Dashboard**
Use Flower for real-time monitoring:
- Task execution times
- Success/failure rates
- Worker health
- Queue lengths

**5. Alerts & Notifications**
```python
# In tasks.py - send user notification on completion
def notify_user(user_id: str, document_id: str, status: str):
    # Send email, push notification, or WebSocket message
    pass
```

### Key Considerations

#### Network Configuration
- Ensure Windows machine is accessible from worker machine (same network or VPN)
- Configure Windows Firewall to allow port 11434 (Ollama default)
- For production, use reverse proxy (nginx) with authentication in front of Ollama
- Consider static IP or hostname for Windows machine

#### Security
- Add API key authentication to Ollama endpoint (reverse proxy with auth)
- Validate uploaded files thoroughly:
  - File type (MIME type, not just extension)
  - File size limits
  - Virus scanning (ClamAV integration)
  - Content validation (not executable, not malicious)
- Sanitize file paths to prevent directory traversal attacks
- Store files with UUID names, not user-provided names
- Use separate storage for uploaded vs processed documents
- Implement rate limiting on upload endpoint

#### Performance Optimization
- **Batching**: Group small documents together for efficient processing
- **GPU Utilization**: Configure Ollama to use GPU on Windows machine
- **Concurrency**: Set Celery concurrency based on:
  - Ollama model capacity
  - Available memory
  - GPU memory
- **Chunking**: For large documents (>100 pages), split into chunks
- **Caching**: Cache extracted text to avoid re-extraction on retries
- **Priority Queue**: Implement task prioritization for premium users

#### Error Handling & Recovery
- Implement comprehensive error logging with context
- Store partial results on timeout (e.g., cards generated before failure)
- Implement circuit breaker for Ollama service
- Dead letter queue for repeatedly failed tasks
- User notifications:
  - Email on completion/failure
  - Real-time updates via WebSocket
  - Status page showing processing progress

#### Testing Strategy
- Unit tests for each component (processor, client, task)
- Integration tests for full pipeline
- Load testing with multiple concurrent uploads
- Test with various document formats and sizes
- Test failure scenarios (Ollama down, network issues, malformed responses)

#### Production Deployment
- Use process manager (systemd, supervisor) for Celery workers
- Configure multiple Celery workers for redundancy
- Set up Redis persistence (RDB + AOF)
- Use Redis Sentinel or Cluster for high availability
- Monitor Ollama resource usage (CPU, GPU, memory)
- Set up log aggregation (ELK stack, CloudWatch)
- Configure alerts for:
  - High queue length
  - Worker failures
  - Ollama downtime
  - High error rates

#### Scalability
- Horizontal scaling: Add more Celery workers as needed
- Vertical scaling: Increase worker concurrency
- Multiple Ollama instances behind load balancer
- Use SQS instead of Redis for better AWS integration (Phase 3)
- Consider GPU queue management for multiple simultaneous requests

### Example Workflow

1. **User uploads document** via Angular frontend
2. **FastAPI receives file**, validates, saves to storage
3. **Document record created** in database with status=UPLOADED
4. **Celery task enqueued** with document_id
5. **Celery worker picks up task**, updates status=PROCESSING
6. **Worker extracts text** from document with page markers
7. **Worker sends text to Ollama** with structured prompt
8. **Ollama generates flashcards** with source attribution
9. **Worker creates deck and cards** via internal API calls
10. **Worker updates document** with status=COMPLETED, deck_id
11. **User receives notification** and can view new flashcards

### Next Steps

1. Uncomment Celery dependencies in requirements.txt
2. Create the worker components (celery_app.py, tasks.py, ollama_client.py, document_processor.py)
3. Update configuration with Ollama settings
4. Create document upload API endpoint
5. Set up Redis and test Celery connectivity
6. Test with sample documents
7. Build frontend upload component
8. Implement monitoring and error handling
9. Deploy to production environment

This architecture provides a robust, scalable foundation for AI-powered flashcard generation while maintaining clean separation of concerns and enabling future enhancements.