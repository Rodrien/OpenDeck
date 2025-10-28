"""Document Upload and Management API Endpoints"""

import json
from typing import Annotated, List
from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Query,
    Request,
    status,
)
import structlog
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.models import Deck, Document, DocumentStatus, DifficultyLevel
from app.schemas.document import DocumentUploadResponse, DocumentResponse, DocumentStatusResponse
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

# P0: Rate limiter instance
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/documents", tags=["Documents"])


async def validate_file_content_type(file: UploadFile, file_ext: str) -> None:
    """
    Validate file content matches its extension by checking magic bytes.

    Args:
        file: The uploaded file
        file_ext: The file extension (e.g., 'pdf', 'docx')

    Raises:
        HTTPException: If content type doesn't match extension
    """
    # Mapping of allowed extensions to their expected magic bytes/signatures
    MAGIC_BYTES = {
        "pdf": [b"%PDF"],  # PDF files start with %PDF
        "docx": [b"PK\x03\x04"],  # DOCX is a ZIP file (Office Open XML)
        "pptx": [b"PK\x03\x04"],  # PPTX is also a ZIP file
        "txt": None,  # Plain text has no reliable magic bytes
    }

    expected_signatures = MAGIC_BYTES.get(file_ext)

    # Skip validation for plain text files
    if expected_signatures is None:
        return

    # Read first 4 bytes to check magic number
    try:
        content = await file.read(4)
        await file.seek(0)  # Reset file pointer
    except Exception as e:
        logger.error(
            "failed_to_read_file_header",
            filename=file.filename,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to validate file '{file.filename}'",
        )

    # Check if content matches any expected signature
    is_valid = False
    for signature in expected_signatures:
        if content.startswith(signature):
            is_valid = True
            break

    if not is_valid:
        logger.warning(
            "file_content_type_mismatch",
            filename=file.filename,
            expected_ext=file_ext,
            magic_bytes=content.hex(),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{file.filename}' content does not match extension '.{file_ext}'. "
            f"The file may be corrupted or have an incorrect extension.",
        )


async def validate_upload_files(files: List[UploadFile]) -> None:
    """
    Validate uploaded files against configuration limits and content types.

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

        # Extract file extension (handle cases like "file.name.pdf")
        file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '.{file_ext}' not allowed. "
                f"Allowed types: {', '.join(allowed_extensions)}",
            )

        # Validate file content matches extension (magic bytes validation)
        await validate_file_content_type(file, file_ext)

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
@limiter.limit("5/hour")  # P0: Rate limiting - 5 uploads per hour per IP
async def upload_documents(
    request: Request,  # Required for slowapi rate limiting
    current_user: CurrentUser,
    deck_repo: DeckRepoDepends,
    document_repo: DocumentRepoDepends,
    files: Annotated[List[UploadFile], File(description="Documents to upload (max 10)")],
    metadata: Annotated[str, Form(description="JSON string containing deck metadata (title, description, category, difficulty)")],
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
    # Parse metadata JSON
    try:
        metadata_dict = json.loads(metadata)
    except json.JSONDecodeError as e:
        logger.error(
            "invalid_metadata_json",
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid metadata JSON: {str(e)}",
        )

    # Extract and validate metadata fields
    title = metadata_dict.get("title", "").strip()
    description = metadata_dict.get("description", "").strip()
    category = metadata_dict.get("category", "").strip()
    difficulty_str = metadata_dict.get("difficulty", "").strip()

    if not title or len(title) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title is required and must be between 1-200 characters",
        )

    if len(description) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Description must not exceed 1000 characters",
        )

    if not category or len(category) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category is required and must be between 1-100 characters",
        )

    # Validate difficulty level
    try:
        difficulty = DifficultyLevel(difficulty_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid difficulty level. Must be one of: {', '.join([d.value for d in DifficultyLevel])}",
        )

    logger.info(
        "document_upload_started",
        user_id=current_user.id,
        file_count=len(files),
        title=title,
        category=category,
    )

    # Validate uploaded files
    await validate_upload_files(files)

    # P0: Transaction management for rollback on failure
    created_deck = None
    document_ids = []
    uploaded_file_paths = []

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
        db.commit()  # Commit deck creation

        logger.info(
            "deck_created",
            deck_id=created_deck.id,
            title=title,
            user_id=current_user.id,
        )

        # Save files to storage and create document records
        for file in files:
            try:
                # Upload file to storage
                file_path = await storage.upload_file(
                    file=file,
                    user_id=current_user.id,
                    deck_id=created_deck.id,
                )
                uploaded_file_paths.append(file_path)

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
                # Fail entire upload if any file fails
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload file '{file.filename}': {str(e)}",
                )

        # Commit all document records
        db.commit()

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
        # P0: Rollback on failure
        db.rollback()

        # Clean up uploaded files from storage
        for file_path in uploaded_file_paths:
            try:
                await storage.delete_file(file_path)
                logger.info("cleanup_uploaded_file", file_path=file_path)
            except Exception as cleanup_error:
                logger.warning(
                    "cleanup_file_failed",
                    file_path=file_path,
                    error=str(cleanup_error)
                )

        # Delete the deck if it was created
        if created_deck:
            try:
                deck_repo.delete(created_deck.id)
                db.commit()
                logger.info("cleanup_orphaned_deck", deck_id=created_deck.id)
            except Exception as deck_cleanup_error:
                logger.warning(
                    "cleanup_deck_failed",
                    deck_id=created_deck.id,
                    error=str(deck_cleanup_error)
                )

        # Re-raise the HTTP exception
        raise

    except Exception as e:
        # P0: Rollback on unexpected errors
        db.rollback()

        # Clean up uploaded files
        for file_path in uploaded_file_paths:
            try:
                await storage.delete_file(file_path)
                logger.info("cleanup_uploaded_file", file_path=file_path)
            except Exception as cleanup_error:
                logger.warning(
                    "cleanup_file_failed",
                    file_path=file_path,
                    error=str(cleanup_error)
                )

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


@router.get("/status", response_model=List[DocumentStatusResponse])
async def get_documents_status(
    current_user: CurrentUser,
    document_repo: DocumentRepoDepends,
    document_ids: Annotated[str, Query(description="Comma-separated document IDs")],
) -> List[DocumentStatusResponse]:
    """
    Get processing status of multiple documents by IDs.

    This endpoint is used by the frontend to poll document processing status.

    Args:
        document_ids: Comma-separated list of document UUIDs
        current_user: Authenticated user
        document_repo: Document repository dependency

    Returns:
        List of document status information

    Example:
        GET /documents/status?document_ids=uuid1,uuid2,uuid3
    """
    # Split and clean document IDs
    ids_list = [doc_id.strip() for doc_id in document_ids.split(",") if doc_id.strip()]

    if not ids_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one document ID is required",
        )

    if len(ids_list) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 document IDs allowed per request",
        )

    # Validate UUIDs
    valid_ids = []
    for doc_id in ids_list:
        try:
            UUID(doc_id)
            valid_ids.append(doc_id)
        except ValueError:
            logger.warning(
                "invalid_uuid_in_status_request",
                user_id=current_user.id,
                invalid_id=doc_id,
            )
            # Skip invalid UUIDs instead of failing the entire request
            continue

    if not valid_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid document IDs provided",
        )

    # Fetch documents by IDs with authorization check
    documents = document_repo.get_by_ids(valid_ids, current_user.id)

    logger.info(
        "documents_status_retrieved",
        user_id=current_user.id,
        requested_count=len(valid_ids),
        found_count=len(documents),
    )

    return [
        DocumentStatusResponse(
            id=doc.id,
            status=doc.status,
            deck_id=doc.deck_id,
            error_message=doc.error_message,
            processed_at=doc.processed_at,
        )
        for doc in documents
    ]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: CurrentUser,
    document_repo: DocumentRepoDepends,
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
    current_user: CurrentUser,
    document_repo: DocumentRepoDepends,
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
