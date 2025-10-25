"""Document Upload and Management API Endpoints"""

from typing import List
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    status,
)
import structlog

from app.core.models import Deck, Document, DocumentStatus, DifficultyLevel
from app.schemas.document import DocumentUploadResponse, DocumentResponse
from app.api.dependencies import (
    CurrentUser,
    DeckRepoDepends,
    DocumentRepoDepends,
)
from app.db.base import get_db
from app.services.storage_service import get_storage_service, StorageService
from app.workers.tasks import process_documents_task
from app.config import settings
from sqlalchemy.orm import Session

logger = structlog.get_logger()

router = APIRouter(prefix="/documents", tags=["Documents"])


def validate_upload_files(files: List[UploadFile]) -> None:
    """
    Validate uploaded files against configuration limits.

    Args:
        files: List of uploaded files

    Raises:
        HTTPException: If validation fails
    """
    # Check file count
    if len(files) > settings.max_files_per_upload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {settings.max_files_per_upload} files allowed per upload. "
            f"You uploaded {len(files)} files.",
        )

    if len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required",
        )

    total_size = 0
    allowed_extensions = settings.allowed_file_types_list

    for file in files:
        # Check file type
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All files must have a filename",
            )

        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '.{file_ext}' not allowed. "
                f"Allowed types: {', '.join(allowed_extensions)}",
            )

        # Check individual file size
        if file.size and file.size > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' exceeds maximum size of "
                f"{settings.max_file_size_mb}MB",
            )

        total_size += file.size or 0

    # Check total upload size
    if total_size > settings.max_total_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Total upload size exceeds maximum of {settings.max_total_upload_size_mb}MB",
        )

    logger.info(
        "upload_validation_passed",
        file_count=len(files),
        total_size_mb=round(total_size / (1024 * 1024), 2),
    )


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_documents(
    files: List[UploadFile] = File(..., description="Documents to upload (max 10)"),
    title: str = Form(..., min_length=1, max_length=200, description="Deck title"),
    description: str = Form(default="", max_length=1000, description="Deck description"),
    category: str = Form(..., min_length=1, max_length=100, description="Deck category/subject"),
    difficulty: DifficultyLevel = Form(..., description="Deck difficulty level"),
    current_user: CurrentUser = Depends(),
    deck_repo: DeckRepoDepends = Depends(),
    document_repo: DocumentRepoDepends = Depends(),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> DocumentUploadResponse:
    """
    Upload documents and create a new deck with AI-generated flashcards.

    **Workflow:**
    1. Validate files (count, type, size)
    2. Create deck record with status PENDING
    3. Save files to storage (local or S3)
    4. Create document records
    5. Queue background processing task
    6. Return immediately with deck ID and task ID

    **Validation Rules:**
    - Maximum 10 files per upload
    - Allowed file types: PDF, DOCX, PPTX, TXT
    - Maximum file size: 10MB per file
    - Maximum total upload size: 50MB
    - User must be authenticated

    **Response:**
    - `deck_id`: ID of the created deck
    - `document_ids`: List of document IDs
    - `task_id`: Celery task ID for tracking processing status
    - `status`: "queued" (processing starts in background)

    **Processing:**
    - Files are processed asynchronously by Celery worker
    - Check processing status using GET /documents/{document_id}/status
    - Flashcards appear in deck once processing completes
    """
    logger.info(
        "document_upload_started",
        user_id=current_user.id,
        file_count=len(files),
        title=title,
        category=category,
    )

    # Validate uploaded files
    validate_upload_files(files)

    try:
        # Create deck record with PENDING status (implicitly via card_count=0)
        deck = Deck(
            id="",  # Will be generated by repository
            user_id=current_user.id,
            title=title,
            description=description,
            category=category,
            difficulty=difficulty,
            card_count=0,  # Will be updated after processing
        )

        created_deck = deck_repo.create(deck)
        logger.info(
            "deck_created",
            deck_id=created_deck.id,
            title=title,
            user_id=current_user.id,
        )

        # Save files to storage and create document records
        document_ids = []

        for file in files:
            try:
                # Upload file to storage
                file_path = await storage.upload_file(
                    file=file,
                    user_id=current_user.id,
                    deck_id=created_deck.id,
                )

                # Create document record
                document = Document(
                    id="",  # Will be generated by repository
                    user_id=current_user.id,
                    filename=file.filename,
                    file_path=file_path,
                    status=DocumentStatus.UPLOADED,
                    deck_id=created_deck.id,
                )

                created_document = document_repo.create(document)
                document_ids.append(created_document.id)

                logger.info(
                    "document_uploaded",
                    document_id=created_document.id,
                    filename=file.filename,
                    file_path=file_path,
                    deck_id=created_deck.id,
                )

            except Exception as e:
                logger.error(
                    "file_upload_failed",
                    filename=file.filename,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                # Continue with other files but log the error
                # Consider whether to fail entire upload or continue
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload file '{file.filename}': {str(e)}",
                )

        # Queue background processing task
        task = process_documents_task.delay(
            deck_id=created_deck.id,
            document_ids=document_ids,
            user_id=current_user.id,
        )

        logger.info(
            "processing_task_queued",
            task_id=task.id,
            deck_id=created_deck.id,
            document_count=len(document_ids),
        )

        return DocumentUploadResponse(
            deck_id=created_deck.id,
            document_ids=document_ids,
            task_id=task.id,
            status="queued",
            message=f"Documents uploaded successfully. Processing {len(document_ids)} document(s).",
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            "document_upload_failed",
            user_id=current_user.id,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document upload: {str(e)}",
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: CurrentUser = Depends(),
    document_repo: DocumentRepoDepends = Depends(),
) -> DocumentResponse:
    """
    Get document details by ID.

    Args:
        document_id: Document identifier
        current_user: Authenticated user
        document_repo: Document repository dependency

    Returns:
        Document details including processing status

    Raises:
        HTTPException: If document not found or access denied
    """
    document = document_repo.get(document_id, current_user.id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return DocumentResponse.model_validate(document)


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    current_user: CurrentUser = Depends(),
    document_repo: DocumentRepoDepends = Depends(),
    limit: int = 100,
    offset: int = 0,
) -> List[DocumentResponse]:
    """
    List user's documents.

    Args:
        current_user: Authenticated user
        document_repo: Document repository dependency
        limit: Maximum number of results (1-100)
        offset: Pagination offset

    Returns:
        List of documents
    """
    documents = document_repo.list(
        user_id=current_user.id,
        limit=min(limit, 100),
        offset=offset,
    )

    return [DocumentResponse.model_validate(doc) for doc in documents]
