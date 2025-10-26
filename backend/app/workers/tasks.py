"""
Celery Background Tasks

Defines asynchronous tasks for document processing and flashcard generation.
"""

from typing import List
import structlog

from app.workers.celery_app import celery_app
from app.services.document_processor import DocumentProcessorService
from app.services.storage_service import get_storage_service
from app.db.base import SessionLocal

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3, name="app.workers.tasks.process_documents_task")
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

        # Process documents - handle async properly
        # Create new event loop for async operations in Celery task
        # This avoids conflicts with existing event loops
        import asyncio

        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, create a new one for this task
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            # No event loop exists, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                processor.process_documents(
                    deck_id=deck_id,
                    document_ids=document_ids,
                    user_id=user_id,
                )
            )
        finally:
            # Only close if we created a new loop
            if not loop.is_running():
                loop.close()

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


@celery_app.task(name="app.workers.tasks.cleanup_temp_files_task")
def cleanup_temp_files_task() -> dict:
    """
    Periodic task to clean up temporary files and failed uploads.

    This task runs on a schedule (e.g., daily) to:
    1. Remove orphaned temporary files
    2. Clean up failed document uploads
    3. Delete old processing logs

    Returns:
        Dict with cleanup statistics
    """
    logger.info("cleanup_task_started")

    try:
        # TODO: Implement cleanup logic
        # - Find documents with status=FAILED older than 7 days
        # - Delete associated files from storage
        # - Remove database records

        logger.info("cleanup_task_completed", files_deleted=0)

        return {
            "status": "completed",
            "files_deleted": 0,
        }

    except Exception as e:
        logger.error(
            "cleanup_task_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        return {
            "status": "failed",
            "error": str(e),
        }
