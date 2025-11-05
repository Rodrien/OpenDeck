"""
Celery Background Tasks

Defines asynchronous tasks for document processing and flashcard generation.
"""

from typing import List, Dict, Any
import structlog
import asyncio
from celery.exceptions import SoftTimeLimitExceeded
from uuid import UUID

from app.workers.celery_app import celery_app
from app.services.document_processor import DocumentProcessorService
from app.services.storage_service import get_storage_service
from app.db.base import SessionLocal
from app.core.models import DocumentStatus

logger = structlog.get_logger()


@celery_app.task(
    bind=True,
    max_retries=3,
    name="app.workers.tasks.process_documents_task",
    # TOOD: Adjust time limits based on expected document sizes and or make defaults configurable
    soft_time_limit=1200,  # 10x2 minutes soft limit (P1: graceful timeout)
    time_limit=1320,       # 11x2 minutes hard limit
)
def process_documents_task(
    self,
    deck_id: str,
    document_ids: List[str],
    user_id: str,
) -> dict:
    """
    Celery task to process uploaded documents and generate flashcards.

    This task:
    1. Extracts text from each document
    2. Generates flashcards using AI
    3. Creates card records in the database
    4. Updates document processing status
    5. Updates deck card count

    Args:
        self: Celery task instance (bind=True)
        deck_id: UUID of the deck being created/updated
        document_ids: List of document UUIDs to process
        user_id: User ID for authorization and context

    Returns:
        Dict with processing results:
        {
            "status": "completed" | "failed",
            "deck_id": str,
            "cards_generated": int,
            "successful_documents": int,
            "failed_documents": int,
        }

    Retries:
        - Max retries: 3
        - Exponential backoff: 60s * (2 ** retry_number)
        - Retries on: All exceptions except validation errors
    """
    logger.info(
        "celery_task_started",
        task_id=self.request.id,
        deck_id=deck_id,
        document_count=len(document_ids),
        user_id=user_id,
    )

    # Update task state to show progress
    self.update_state(
        state="PROCESSING",
        meta={
            "current": 0,
            "total": len(document_ids),
            "status": "Starting document processing...",
        },
    )

    # Create database session
    db = SessionLocal()

    try:
        # Initialize services
        storage = get_storage_service()
        processor = DocumentProcessorService(
            session=db,
            storage=storage,
        )

        # Process documents - use asyncio.run() (P0: simplified event loop handling)
        # This is the recommended approach for running async code in Celery tasks
        result = asyncio.run(
            processor.process_documents(
                deck_id=deck_id,
                document_ids=document_ids,
                user_id=user_id,
            )
        )

        logger.info(
            "celery_task_completed",
            task_id=self.request.id,
            deck_id=deck_id,
            cards_generated=result.total_cards,
            successful_documents=result.successful_documents,
            failed_documents=result.failed_documents,
        )

        return {
            "status": "completed",
            "deck_id": deck_id,
            "cards_generated": result.total_cards,
            "successful_documents": result.successful_documents,
            "failed_documents": result.failed_documents,
        }

    except SoftTimeLimitExceeded:
        # P1: Gracefully handle timeout
        logger.error(
            "celery_task_timeout",
            task_id=self.request.id,
            deck_id=deck_id,
            message="Task timeout - marking documents as failed",
        )

        # Mark all documents as failed due to timeout
        from app.db.postgres_repo import PostgresDocumentRepo

        document_repo = PostgresDocumentRepo(db)
        for doc_id in document_ids:
            try:
                doc = document_repo.get(UUID(doc_id))
                if doc and doc.status == DocumentStatus.PROCESSING:
                    doc.mark_failed("Processing timeout exceeded (10 minutes)")
                    document_repo.update(doc)
            except Exception as e:
                logger.warning(
                    "failed_to_update_document_on_timeout",
                    document_id=doc_id,
                    error=str(e),
                )

        db.commit()

        # Retry with backoff
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=SoftTimeLimitExceeded(), countdown=countdown)

    except Exception as exc:
        logger.error(
            "celery_task_failed",
            task_id=self.request.id,
            deck_id=deck_id,
            error=str(exc),
            error_type=type(exc).__name__,
            retry_count=self.request.retries,
        )

        # Update task state to show failure
        self.update_state(
            state="FAILURE",
            meta={
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
        )

        # Retry with exponential backoff
        # countdown = 60 seconds * (2 ^ retry_number)
        countdown = 60 * (2 ** self.request.retries)

        logger.info(
            "celery_task_retrying",
            task_id=self.request.id,
            retry_count=self.request.retries + 1,
            countdown=countdown,
        )

        raise self.retry(exc=exc, countdown=countdown)

    finally:
        # Always close the database session
        db.close()


@celery_app.task(
    bind=True,
    max_retries=3,
    name="app.workers.tasks.cleanup_orphaned_files_task"
)
def cleanup_orphaned_files_task(self) -> Dict[str, Any]:
    """
    P1: Periodic task to clean up orphaned files from failed uploads.

    This task runs on a schedule (e.g., daily) to:
    1. Find documents with status=FAILED older than retention period
    2. Delete associated files from storage
    3. Update document records

    Returns:
        Dict with cleanup statistics:
        {
            "status": "completed" | "failed",
            "files_deleted": int,
            "errors": int
        }
    """
    from datetime import datetime, timedelta
    from app.db.postgres_repo import PostgresDocumentRepo

    logger.info("cleanup_task_started", task_id=self.request.id)

    db = SessionLocal()
    cleaned_count = 0
    error_count = 0
    retention_days = 7  # Keep failed files for 7 days

    try:
        storage = get_storage_service()
        document_repo = PostgresDocumentRepo(db)

        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # Find failed documents older than retention period
        # Query directly since we may not have a find_by_status method
        from app.db.models import Document as DocumentDB

        failed_docs = db.query(DocumentDB).filter(
            DocumentDB.status == DocumentStatus.FAILED.value,
            DocumentDB.created_at < cutoff_date
        ).all()

        logger.info(
            "cleanup_found_documents",
            count=len(failed_docs),
            cutoff_date=cutoff_date.isoformat()
        )

        # Process each failed document
        for db_doc in failed_docs:
            try:
                # Delete file from storage
                asyncio.run(storage.delete_file(db_doc.storage_path))

                # Mark in database (could soft delete or mark as cleaned)
                db_doc.status = "CLEANED"
                cleaned_count += 1

                logger.info(
                    "cleanup_file_deleted",
                    document_id=str(db_doc.id),
                    filename=db_doc.filename
                )

            except FileNotFoundError:
                # File already deleted, just update status
                db_doc.status = "CLEANED"
                cleaned_count += 1
                logger.warning(
                    "cleanup_file_not_found",
                    document_id=str(db_doc.id),
                    storage_path=db_doc.storage_path
                )

            except Exception as e:
                error_count += 1
                logger.error(
                    "cleanup_file_error",
                    document_id=str(db_doc.id),
                    error=str(e),
                    error_type=type(e).__name__
                )

        # Commit all changes
        db.commit()

        logger.info(
            "cleanup_task_completed",
            task_id=self.request.id,
            files_deleted=cleaned_count,
            errors=error_count
        )

        return {
            "status": "completed",
            "files_deleted": cleaned_count,
            "errors": error_count
        }

    except Exception as e:
        db.rollback()
        logger.error(
            "cleanup_task_failed",
            task_id=self.request.id,
            error=str(e),
            error_type=type(e).__name__,
        )

        # Retry with backoff
        countdown = 300  # 5 minutes
        raise self.retry(exc=e, countdown=countdown)

    finally:
        db.close()
