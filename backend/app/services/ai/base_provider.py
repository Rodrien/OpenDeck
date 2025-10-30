"""
Base AI Provider Interface

Defines the common contract that all AI providers must implement.
This ensures consistent behavior across different AI backends.
"""

from typing import Protocol, List
from dataclasses import dataclass


@dataclass
class FlashcardData:
    """
    Data structure for generated flashcard.

    CRITICAL: All flashcards MUST include source attribution per CLAUDE.md.
    This is a requirement to ensure users can verify and corroborate information.
    """

    question: str
    answer: str
    source: str  # REQUIRED: "DocumentName.pdf - Page X, Section Y"

    def __post_init__(self):
        """Validate flashcard data on initialization."""
        if not self.question or not self.question.strip():
            raise ValueError("Question cannot be empty")
        if not self.answer or not self.answer.strip():
            raise ValueError("Answer cannot be empty")
        if not self.source or not self.source.strip():
            raise ValueError("Source attribution is required")
        # Validate source includes meaningful reference
        if len(self.source.strip()) < 5:
            raise ValueError("Source attribution must include document name and page")


class AIServiceError(Exception):
    """Base exception for AI service errors."""

    pass


class AIProviderError(AIServiceError):
    """Exception for AI provider API errors."""

    pass


class AIValidationError(AIServiceError):
    """Exception for validation errors in AI responses."""

    pass


class AIProvider(Protocol):
    """
    Common interface for all AI providers.

    All providers must implement this protocol to ensure consistent
    behavior and interchangeability across different AI backends.

    Supported providers:
    - OpenAI (GPT-4, GPT-3.5-Turbo)
    - Anthropic (Claude 3 Opus, Sonnet, Haiku)
    - Ollama (local models: llama2, mistral, etc.)
    """

    @property
    def provider_name(self) -> str:
        """
        Provider identifier.

        Returns:
            Provider name as string (e.g., 'openai', 'anthropic', 'ollama')
        """
        ...

    def generate_flashcards(
        self,
        document_text: str,
        document_name: str,
        page_data: List[tuple[int, str]],
        max_cards: int = 20,
    ) -> List[FlashcardData]:
        """
        Generate flashcards from document text.

        This is the primary method all providers must implement. It takes
        document content and generates educational flashcards with proper
        source attribution.

        Args:
            document_text: Full document text to generate flashcards from
            document_name: Name of the source document for attribution
            page_data: List of (page_number, page_text) tuples for source tracking
            max_cards: Maximum number of flashcards to generate (default: 20)

        Returns:
            List of FlashcardData objects with questions, answers, and sources

        Raises:
            AIServiceError: If generation fails for any reason
            AIProviderError: If the AI provider API encounters an error
            AIValidationError: If the generated content fails validation
        """
        ...

    def health_check(self) -> bool:
        """
        Verify provider is accessible and configured correctly.

        This method should check:
        - API credentials are valid (if applicable)
        - Service endpoint is reachable
        - Basic functionality is working

        Returns:
            True if provider is healthy and ready, False otherwise
        """
        ...
