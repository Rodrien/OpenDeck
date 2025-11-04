"""
Anthropic Provider Implementation

Integrates with Anthropic's Messages API for flashcard generation.
Supports Claude 3 models (Opus, Sonnet, Haiku).
"""

from typing import List
import json
import requests
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
from app.services.ai.validation import parse_flashcard_response

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
        Check if Anthropic API configuration is valid.

        Note: This performs a basic configuration check rather than an actual API call
        to avoid unnecessary costs. Authentication errors will be caught on first actual use.

        Returns:
            True if API configuration appears valid
        """
        try:
            # Basic validation: check if API key is configured
            if not settings.anthropic_api_key or len(settings.anthropic_api_key) < 10:
                logger.error("anthropic_health_check_failed", reason="Invalid API key")
                return False

            # Check if model is configured
            if not self.model:
                logger.error("anthropic_health_check_failed", reason="Model not configured")
                return False

            logger.info("anthropic_health_check_passed", note="Configuration validated")
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
        retry=retry_if_exception_type((
            requests.exceptions.RequestException,
            json.JSONDecodeError,
        )),
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
            flashcards = parse_flashcard_response(content, document_name)

            return flashcards

        except self.AnthropicError as e:
            logger.error("anthropic_api_error", error=str(e))
            raise AIProviderError(f"Anthropic API error: {str(e)}")
        except Exception as e:
            logger.error("anthropic_generation_error", error=str(e))
            raise
