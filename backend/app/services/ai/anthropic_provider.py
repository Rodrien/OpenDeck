"""
Anthropic Provider Implementation

Integrates with Anthropic's Messages API for flashcard generation.
Supports Claude 3 models (Opus, Sonnet, Haiku).
"""

from typing import List
import json
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.services.ai.base_provider import (
    FlashcardData,
    AIProvider,
    AIProviderError,
    AIValidationError,
)
from app.services.ai.prompts import build_system_prompt, build_user_prompt

logger = structlog.get_logger()


class AnthropicProvider:
    """
    Anthropic AI provider for flashcard generation.

    Uses Anthropic's Messages API with Claude 3 models.
    Includes automatic retry logic and comprehensive error handling.
    """

    def __init__(self):
        """
        Initialize Anthropic provider.

        Raises:
            ImportError: If anthropic package is not installed
            ValueError: If API key is not configured
        """
        try:
            from anthropic import Anthropic, APIError

            self.AnthropicError = APIError
        except ImportError:
            raise ImportError(
                "anthropic is required for Anthropic provider. "
                "Install with: pip install anthropic"
            )

        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key is required (ANTHROPIC_API_KEY)")

        self.client = Anthropic(
            api_key=settings.anthropic_api_key, timeout=settings.ai_timeout_seconds
        )
        self.model = settings.anthropic_model
        self.max_retries = settings.ai_max_retries

        logger.info(
            "anthropic_provider_initialized",
            model=self.model,
            max_retries=self.max_retries,
        )

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "anthropic"

    def health_check(self) -> bool:
        """
        Check if Anthropic API is accessible.

        Returns:
            True if API is reachable and credentials are valid
        """
        try:
            # Simple API call to verify connectivity
            # Use a minimal message to check authentication
            self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
            )
            logger.info("anthropic_health_check_passed")
            return True
        except Exception as e:
            logger.error("anthropic_health_check_failed", error=str(e))
            return False

    def generate_flashcards(
        self,
        document_text: str,
        document_name: str,
        page_data: List[tuple[int, str]],
        max_cards: int = 20,
    ) -> List[FlashcardData]:
        """
        Generate flashcards using Anthropic API.

        Args:
            document_text: Full document text
            document_name: Name of the source document
            page_data: List of (page_number, page_text) tuples
            max_cards: Maximum number of flashcards to generate

        Returns:
            List of FlashcardData with source attribution

        Raises:
            AIProviderError: If Anthropic API call fails
            AIValidationError: If response parsing/validation fails
        """
        logger.info(
            "generating_flashcards_anthropic",
            document_name=document_name,
            pages=len(page_data),
            max_cards=max_cards,
        )

        try:
            flashcards = self._generate_with_retry(
                document_text, document_name, page_data, max_cards
            )

            logger.info(
                "anthropic_generation_success",
                document_name=document_name,
                flashcards_generated=len(flashcards),
            )

            return flashcards

        except Exception as e:
            logger.error(
                "anthropic_generation_failed",
                document_name=document_name,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    def _generate_with_retry(
        self,
        document_text: str,
        document_name: str,
        page_data: List[tuple[int, str]],
        max_cards: int,
    ) -> List[FlashcardData]:
        """
        Generate flashcards with automatic retry logic.

        Args:
            document_text: Full document text
            document_name: Name of the source document
            page_data: List of (page_number, page_text) tuples
            max_cards: Maximum number of flashcards

        Returns:
            List of FlashcardData

        Raises:
            AIProviderError: If API call fails after retries
        """
        system_prompt = build_system_prompt(document_name, max_cards)
        user_prompt = build_user_prompt(document_text, page_data)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Extract text from response
            content = response.content[0].text
            flashcards = self._parse_response(content, document_name)

            return flashcards

        except self.AnthropicError as e:
            logger.error("anthropic_api_error", error=str(e))
            raise AIProviderError(f"Anthropic API error: {str(e)}")
        except Exception as e:
            logger.error("anthropic_generation_error", error=str(e))
            raise

    def _parse_response(
        self, response_text: str, document_name: str
    ) -> List[FlashcardData]:
        """
        Parse Anthropic JSON response into FlashcardData objects.

        Args:
            response_text: JSON response from Anthropic
            document_name: Name of source document for validation

        Returns:
            List of validated FlashcardData

        Raises:
            AIValidationError: If parsing or validation fails
        """
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error("json_parse_error", error=str(e), response=response_text[:500])
            raise AIValidationError(f"Failed to parse JSON response: {str(e)}")

        if "flashcards" not in data:
            raise AIValidationError("Response missing 'flashcards' field")

        flashcards = []
        for i, card_data in enumerate(data["flashcards"]):
            try:
                # Validate required fields
                if "question" not in card_data:
                    logger.warning(
                        "flashcard_missing_question", index=i, data=card_data
                    )
                    continue
                if "answer" not in card_data:
                    logger.warning("flashcard_missing_answer", index=i, data=card_data)
                    continue
                if "source" not in card_data or not card_data["source"].strip():
                    logger.warning(
                        "flashcard_missing_source", index=i, data=card_data
                    )
                    # Add default source if missing (shouldn't happen with good prompts)
                    card_data["source"] = f"{document_name} - Page Unknown"

                # Validate source includes document name
                source = card_data["source"].strip()
                if document_name.lower() not in source.lower():
                    # Add document name if missing
                    source = f"{document_name} - {source}"

                flashcard = FlashcardData(
                    question=card_data["question"].strip(),
                    answer=card_data["answer"].strip(),
                    source=source,
                )
                flashcards.append(flashcard)

            except Exception as e:
                logger.warning(
                    "flashcard_validation_failed",
                    index=i,
                    error=str(e),
                    data=card_data,
                )
                # Skip invalid flashcards
                continue

        if not flashcards:
            raise AIValidationError("No valid flashcards generated")

        logger.info(
            "flashcards_parsed",
            total=len(data.get("flashcards", [])),
            valid=len(flashcards),
        )

        return flashcards
