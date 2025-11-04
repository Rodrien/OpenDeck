"""
Document Processor Service

Orchestrates document processing pipeline:
1. Extract text from documents
2. Generate flashcards via AI
3. Create database records
4. Update deck statistics
"""

from typing import List
from datetime import datetime
import structlog

from app.core.models import Document, DocumentStatus, Card
from app.schemas.flashcard import ProcessingResult
from app.services.document_extractor import DocumentExtractor
from app.services.ai import get_ai_provider, AIProvider
from app.services.ai.base_provider import FlashcardData
from app.db.postgres_repo import PostgresDocumentRepo, PostgresCardRepo, PostgresDeckRepo
from app.services.storage_service import StorageService
from sqlalchemy.orm import Session

logger = structlog.get_logger()


class DocumentProcessorService:
    """
    Service for processing documents and generating flashcards.

    Coordinates between text extraction, AI generation, and persistence layers.
    """

    def __init__(
        self,
        session: Session,
        storage: StorageService,
        ai_provider: AIProvider | None = None,
        extractor: DocumentExtractor | None = None,
    ):
        """
        Initialize document processor.

        Args:
            session: Database session
            storage: Storage service for file access
            ai_provider: AI provider for flashcard generation (uses factory if None)
            extractor: Document text extractor
        """
        self.session = session
        self.storage = storage
        self.ai_provider = ai_provider or get_ai_provider()
        self.extractor = extractor or DocumentExtractor()
        self.document_repo = PostgresDocumentRepo(session)
        self.card_repo = PostgresCardRepo(session)
        self.deck_repo = PostgresDeckRepo(session)

    async def process_documents(
        self,
        deck_id: str,
        document_ids: List[str],
        user_id: str,
    ) -> ProcessingResult:
        """
        Process documents and generate flashcards for a deck.

        Args:
            deck_id: ID of the deck to add flashcards to
            document_ids: List of document IDs to process
            user_id: User ID for authorization

        Returns:
            ProcessingResult with statistics

        Raises:
            ValueError: If deck or documents not found
        """
        logger.info(
            "processing_documents_started",
            deck_id=deck_id,
            document_count=len(document_ids),
            user_id=user_id,
        )

        total_cards = 0
        successful_documents = 0
        failed_documents = 0

        for doc_id in document_ids:
            try:
                # Get document record
                document = self.document_repo.get(doc_id, user_id)
                if not document:
                    logger.error(
                        "document_not_found",
                        document_id=doc_id,
                        user_id=user_id,
                    )
                    failed_documents += 1
                    continue

                # P1: Idempotency check - skip if already processed or processing
                if document.status == DocumentStatus.COMPLETED:
                    logger.warning(
                        "document_already_completed",
                        document_id=doc_id,
                        filename=document.filename,
                        message="Skipping already completed document (idempotency check)",
                    )
                    successful_documents += 1  # Count as successful since it's done
                    continue

                if document.status == DocumentStatus.PROCESSING:
                    logger.warning(
                        "document_already_processing",
                        document_id=doc_id,
                        filename=document.filename,
                        message="Document already being processed (idempotency check)",
                    )
                    continue

                # Update status to PROCESSING
                document.mark_processing()
                self.document_repo.update(document)
                self.session.commit()

                logger.info(
                    "processing_document",
                    document_id=doc_id,
                    filename=document.filename,
                    file_path=document.file_path,
                )

                # Extract text from document
                extraction_result = await self._extract_document_text(document)

                # Generate flashcards via AI provider
                flashcards = self.ai_provider.generate_flashcards(
                    document_text=extraction_result.text,
                    document_name=document.filename,
                    page_data=extraction_result.pages,
                    max_cards=20,
                )

                # Create flashcard records
                cards_created = self._create_flashcard_records(
                    deck_id=deck_id,
                    flashcards=flashcards,
                )

                total_cards += cards_created

                # Mark document as completed
                document.mark_completed(deck_id)
                self.document_repo.update(document)
                self.session.commit()

                successful_documents += 1

                logger.info(
                    "document_processed_successfully",
                    document_id=doc_id,
                    filename=document.filename,
                    cards_generated=cards_created,
                )

            except Exception as e:
                logger.error(
                    "document_processing_failed",
                    document_id=doc_id,
                    error=str(e),
                    error_type=type(e).__name__,
                )

                # Mark document as failed
                try:
                    document = self.document_repo.get(doc_id, user_id)
                    if document:
                        document.mark_failed(str(e))
                        self.document_repo.update(document)
                        self.session.commit()
                except Exception as update_error:
                    logger.error(
                        "failed_to_update_document_status",
                        document_id=doc_id,
                        error=str(update_error),
                    )

                failed_documents += 1

        # Update deck card count
        if total_cards > 0:
            try:
                deck = self.deck_repo.get(deck_id, user_id)
                if deck:
                    deck.card_count = deck.card_count + total_cards
                    self.deck_repo.update(deck)
                    self.session.commit()

                    logger.info(
                        "deck_card_count_updated",
                        deck_id=deck_id,
                        new_card_count=deck.card_count,
                    )
            except Exception as e:
                logger.error(
                    "failed_to_update_deck_card_count",
                    deck_id=deck_id,
                    error=str(e),
                )

        result = ProcessingResult(
            total_cards=total_cards,
            successful_documents=successful_documents,
            failed_documents=failed_documents,
            deck_id=deck_id,
        )

        logger.info(
            "processing_documents_completed",
            deck_id=deck_id,
            total_cards=total_cards,
            successful_documents=successful_documents,
            failed_documents=failed_documents,
        )

        return result

    async def _extract_document_text(self, document: Document):
        """
        Extract text from document file.

        Args:
            document: Document domain object

        Returns:
            ExtractionResult with text and page data

        Raises:
            Exception: If extraction fails
        """
        # Get file from storage
        file_bytes = await self.storage.get_file(document.file_path)

        # Save to temporary file for extraction (document libraries need file paths)
        import tempfile
        import os

        # Create temp file with correct extension
        suffix = os.path.splitext(document.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        try:
            # Extract text
            extraction_result = self.extractor.extract(temp_path)

            logger.info(
                "text_extracted",
                document_id=document.id,
                filename=document.filename,
                pages=len(extraction_result.pages),
                chars=len(extraction_result.text),
            )

            return extraction_result

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(
                    "failed_to_delete_temp_file",
                    temp_path=temp_path,
                    error=str(e),
                )

    def _create_flashcard_records(
        self,
        deck_id: str,
        flashcards: List[FlashcardData],
    ) -> int:
        """
        Create flashcard database records from FlashcardData objects.

        Args:
            deck_id: ID of the deck
            flashcards: List of FlashcardData objects from AI service

        Returns:
            Number of cards created
        """
        cards_created = 0

        for flashcard_data in flashcards:
            try:
                # Create Card domain object
                card = Card(
                    id="",  # Will be generated by repository
                    deck_id=deck_id,
                    question=flashcard_data.question,
                    answer=flashcard_data.answer,
                    source=flashcard_data.source,
                    source_url=None,
                )

                # Persist to database
                self.card_repo.create(card)
                cards_created += 1

            except Exception as e:
                logger.error(
                    "failed_to_create_flashcard",
                    deck_id=deck_id,
                    question_preview=flashcard_data.question[:50],
                    error=str(e),
                )
                # Continue with other flashcards
                continue

        # Commit all cards at once
        self.session.commit()

        logger.info(
            "flashcards_created",
            deck_id=deck_id,
            cards_created=cards_created,
        )

        return cards_created


# Dependency injection factory
def get_document_processor(
    session: Session,
    storage: StorageService,
) -> DocumentProcessorService:
    """
    Factory function for document processor service.

    Args:
        session: Database session
        storage: Storage service

    Returns:
        DocumentProcessorService instance
    """
    return DocumentProcessorService(
        session=session,
        storage=storage,
    )
