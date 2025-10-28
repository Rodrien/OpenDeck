"""
AI Service for Flashcard Generation

Integrates with OpenAI and Anthropic APIs to generate flashcards from document text.
Implements prompt engineering and ensures source attribution for all generated content.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import json
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings

logger = structlog.get_logger()


@dataclass
class FlashcardData:
    """
    Data structure for generated flashcard.

    CRITICAL: All flashcards MUST include source attribution per CLAUDE.md.
    """

    question: str
    answer: str
    source: str  # REQUIRED: "DocumentName.pdf - Page X, Section Y"

    def __post_init__(self):
        """Validate flashcard data."""
        if not self.question or not self.question.strip():
            raise ValueError("Question cannot be empty")
        if not self.answer or not self.answer.strip():
            raise ValueError("Answer cannot be empty")
        if not self.source or not self.source.strip():
            raise ValueError("Source attribution is required")
        # Validate source includes document reference
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


class AIService:
    """
    AI service for flashcard generation.

    Supports OpenAI and Anthropic providers with automatic retry logic.
    """

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize AI service.

        Args:
            provider: AI provider ('openai' or 'anthropic'). Uses settings if not provided.
        """
        self.provider = provider or settings.ai_provider
        self.max_retries = settings.ai_max_retries
        self.timeout = settings.ai_timeout_seconds

        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "anthropic":
            self._init_anthropic()
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")

        logger.info("ai_service_initialized", provider=self.provider)

    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI, OpenAIError
            self.OpenAIError = OpenAIError
        except ImportError:
            raise ImportError(
                "openai is required for OpenAI provider. "
                "Install with: pip install openai"
            )

        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required")

        self.client = OpenAI(api_key=settings.openai_api_key, timeout=self.timeout)
        self.model = settings.openai_model

    def _init_anthropic(self):
        """Initialize Anthropic client."""
        try:
            from anthropic import Anthropic, APIError
            self.AnthropicError = APIError
        except ImportError:
            raise ImportError(
                "anthropic is required for Anthropic provider. "
                "Install with: pip install anthropic"
            )

        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key is required")

        self.client = Anthropic(api_key=settings.anthropic_api_key, timeout=self.timeout)
        self.model = settings.anthropic_model

    def generate_flashcards(
        self,
        document_text: str,
        document_name: str,
        page_data: List[tuple[int, str]],
        max_cards: int = 20,
    ) -> List[FlashcardData]:
        """
        Generate flashcards from document text.

        Args:
            document_text: Full document text
            document_name: Name of the source document
            page_data: List of (page_number, page_text) tuples
            max_cards: Maximum number of flashcards to generate

        Returns:
            List of FlashcardData with source attribution

        Raises:
            AIServiceError: If generation fails
        """
        logger.info(
            "generating_flashcards",
            document_name=document_name,
            pages=len(page_data),
            max_cards=max_cards,
            provider=self.provider,
        )

        try:
            if self.provider == "openai":
                return self._generate_with_openai(
                    document_text, document_name, page_data, max_cards
                )
            elif self.provider == "anthropic":
                return self._generate_with_anthropic(
                    document_text, document_name, page_data, max_cards
                )
            else:
                raise AIProviderError(f"Unsupported provider: {self.provider}")

        except Exception as e:
            logger.error(
                "flashcard_generation_failed",
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
    def _generate_with_openai(
        self,
        document_text: str,
        document_name: str,
        page_data: List[tuple[int, str]],
        max_cards: int,
    ) -> List[FlashcardData]:
        """
        Generate flashcards using OpenAI API.

        Args:
            document_text: Full document text
            document_name: Name of the source document
            page_data: List of (page_number, page_text) tuples
            max_cards: Maximum number of flashcards

        Returns:
            List of FlashcardData
        """
        system_prompt = self._build_system_prompt(document_name, max_cards)
        user_prompt = self._build_user_prompt(document_text, page_data)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            flashcards = self._parse_response(content, document_name)

            logger.info(
                "openai_generation_success",
                document_name=document_name,
                flashcards_generated=len(flashcards),
            )

            return flashcards

        except self.OpenAIError as e:
            logger.error("openai_api_error", error=str(e))
            raise AIProviderError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            logger.error("openai_generation_error", error=str(e))
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    def _generate_with_anthropic(
        self,
        document_text: str,
        document_name: str,
        page_data: List[tuple[int, str]],
        max_cards: int,
    ) -> List[FlashcardData]:
        """
        Generate flashcards using Anthropic API.

        Args:
            document_text: Full document text
            document_name: Name of the source document
            page_data: List of (page_number, page_text) tuples
            max_cards: Maximum number of flashcards

        Returns:
            List of FlashcardData
        """
        system_prompt = self._build_system_prompt(document_name, max_cards)
        user_prompt = self._build_user_prompt(document_text, page_data)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            content = response.content[0].text
            flashcards = self._parse_response(content, document_name)

            logger.info(
                "anthropic_generation_success",
                document_name=document_name,
                flashcards_generated=len(flashcards),
            )

            return flashcards

        except self.AnthropicError as e:
            logger.error("anthropic_api_error", error=str(e))
            raise AIProviderError(f"Anthropic API error: {str(e)}")
        except Exception as e:
            logger.error("anthropic_generation_error", error=str(e))
            raise

    def _build_system_prompt(self, document_name: str, max_cards: int) -> str:
        """
        Build system prompt for AI model.

        Args:
            document_name: Name of the source document
            max_cards: Maximum number of flashcards

        Returns:
            System prompt string
        """
        return f"""You are an expert educational content creator specializing in generating high-quality flashcards from academic materials.

Your task is to analyze the provided document and create up to {max_cards} flashcards that:
1. Focus on key concepts, definitions, and important relationships
2. Use clear, concise language appropriate for the subject matter
3. Include precise source attribution for EVERY flashcard

CRITICAL SOURCE ATTRIBUTION REQUIREMENT:
- Every flashcard MUST include a "source" field
- Format: "{document_name} - Page X" or "{document_name} - Page X, Section Y"
- The source must reference the specific page where the information appears
- This is MANDATORY and non-negotiable

Output Format:
Return a JSON object with a "flashcards" array. Each flashcard must have:
- "question": Clear, focused question
- "answer": Comprehensive but concise answer
- "source": REQUIRED precise reference to document page/section

Example:
{{
    "flashcards": [
        {{
            "question": "What is photosynthesis?",
            "answer": "The process by which plants convert light energy into chemical energy (glucose) using carbon dioxide and water, releasing oxygen as a byproduct.",
            "source": "{document_name} - Page 12, Section 3.2"
        }}
    ]
}}

Quality Guidelines:
- Focus on understanding, not memorization
- Create questions at different difficulty levels
- Ensure answers are accurate and complete
- Avoid overly broad or vague questions
- Each flashcard should be self-contained"""

    def _build_user_prompt(
        self, document_text: str, page_data: List[tuple[int, str]]
    ) -> str:
        """
        Build user prompt with document content.

        Args:
            document_text: Full document text
            page_data: List of (page_number, page_text) tuples

        Returns:
            User prompt string
        """
        # Truncate if document is very long (to stay within token limits)
        max_chars = 15000
        if len(document_text) > max_chars:
            document_text = document_text[:max_chars] + "\n\n[Document truncated...]"

        # Include page information for better source attribution
        page_info = "\n".join(
            [f"Page {num}: {len(text)} characters" for num, text in page_data[:10]]
        )

        return f"""Document Information:
{page_info}

Document Content:
{document_text}

Please generate flashcards from this document. Remember to include precise source attribution (page number) for each flashcard."""

    def _parse_response(
        self, response_text: str, document_name: str
    ) -> List[FlashcardData]:
        """
        Parse AI response into FlashcardData objects.

        Args:
            response_text: JSON response from AI
            document_name: Name of source document

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


def get_ai_service(provider: Optional[str] = None) -> AIService:
    """
    Factory function for AI service.

    Args:
        provider: Optional provider override

    Returns:
        AIService instance
    """
    return AIService(provider=provider)
