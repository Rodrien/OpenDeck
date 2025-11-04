"""
Ollama Provider Implementation

Integrates with locally-hosted Ollama models via HTTP API.
Supports any model available in Ollama (llama2, mistral, phi, etc.).
"""

from typing import List, Tuple
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


class OllamaProvider:
    """
    Ollama AI provider for local model inference.

    Connects to Ollama server running on localhost (or configured URL).
    Supports any model available in Ollama model library.

    Features:
    - No API costs (runs locally)
    - Privacy-preserving (data stays local)
    - Automatic chunking for large documents
    - Context window management
    """

    def __init__(self):
        """
        Initialize Ollama provider.

        Uses configuration from settings for base URL and model selection.
        """
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout_seconds
        # Context window varies by model; using conservative default
        # llama2: 4096, mistral: 8192, llama3: 8192
        self.max_context_tokens = 4096

        logger.info(
            "ollama_provider_initialized",
            base_url=self.base_url,
            model=self.model,
            timeout=self.timeout,
        )

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "ollama"

    def health_check(self) -> bool:
        """
        Check if Ollama server is accessible and model is available.

        Returns:
            True if Ollama server is running and model is available
        """
        try:
            # Check if Ollama server is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                logger.error(
                    "ollama_server_unreachable", status_code=response.status_code
                )
                return False

            # Check if configured model is available
            models_data = response.json()
            available_models = [m["name"] for m in models_data.get("models", [])]

            if self.model not in available_models:
                logger.warning(
                    "ollama_model_not_found",
                    model=self.model,
                    available_models=available_models,
                )
                return False

            logger.info("ollama_health_check_passed", model=self.model)
            return True

        except requests.exceptions.RequestException as e:
            logger.error("ollama_health_check_failed", error=str(e))
            return False
        except Exception as e:
            logger.error(
                "ollama_health_check_error", error=str(e), error_type=type(e).__name__
            )
            return False

    def generate_flashcards(
        self,
        document_text: str,
        document_name: str,
        page_data: List[tuple[int, str]],
        max_cards: int = 20,
    ) -> List[FlashcardData]:
        """
        Generate flashcards using Ollama model.

        Automatically chunks large documents to fit within model's context window.

        Args:
            document_text: Full document text
            document_name: Name of the source document
            page_data: List of (page_number, page_text) tuples
            max_cards: Maximum number of flashcards to generate

        Returns:
            List of FlashcardData with source attribution

        Raises:
            AIProviderError: If Ollama API call fails
            AIValidationError: If response parsing/validation fails
        """
        logger.info(
            "generating_flashcards_ollama",
            document_name=document_name,
            pages=len(page_data),
            max_cards=max_cards,
            model=self.model,
        )

        try:
            # Check if document needs chunking
            if self._needs_chunking(document_text):
                flashcards = self._generate_with_chunking(
                    document_text, document_name, page_data, max_cards
                )
            else:
                flashcards = self._generate_single(
                    document_text, document_name, page_data, max_cards
                )

            logger.info(
                "ollama_generation_success",
                document_name=document_name,
                flashcards_generated=len(flashcards),
            )

            return flashcards

        except Exception as e:
            logger.error(
                "ollama_generation_failed",
                document_name=document_name,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def _needs_chunking(self, text: str) -> bool:
        """
        Check if document exceeds context window.

        Args:
            text: Document text to check

        Returns:
            True if document needs to be chunked
        """
        # Rough approximation: 4 characters per token
        estimated_tokens = len(text) / 4
        # Use 70% of context window to leave room for prompts and response
        max_allowed = self.max_context_tokens * 0.7
        needs_chunking = estimated_tokens > max_allowed

        if needs_chunking:
            logger.info(
                "document_needs_chunking",
                estimated_tokens=int(estimated_tokens),
                max_allowed=int(max_allowed),
            )

        return needs_chunking

    def _chunk_document(
        self, document_text: str, page_data: List[tuple[int, str]]
    ) -> List[Tuple[str, List[tuple[int, str]]]]:
        """
        Split document into chunks that fit within context window.

        Args:
            document_text: Full document text
            page_data: List of (page_number, page_text) tuples

        Returns:
            List of (chunk_text, chunk_pages) tuples
        """
        chunks = []
        max_chunk_chars = int(self.max_context_tokens * 0.7 * 4)  # tokens to chars

        current_chunk_text = []
        current_chunk_pages = []
        current_size = 0

        for page_num, page_text in page_data:
            page_size = len(page_text)

            # If adding this page would exceed chunk size, start new chunk
            if current_size + page_size > max_chunk_chars and current_chunk_text:
                chunks.append(
                    ("\n\n".join(current_chunk_text), current_chunk_pages.copy())
                )
                current_chunk_text = []
                current_chunk_pages = []
                current_size = 0

            current_chunk_text.append(page_text)
            current_chunk_pages.append((page_num, page_text))
            current_size += page_size

        # Add remaining chunk
        if current_chunk_text:
            chunks.append(("\n\n".join(current_chunk_text), current_chunk_pages))

        logger.info(
            "document_chunked",
            total_chunks=len(chunks),
            avg_chunk_size=sum(len(c[0]) for c in chunks) // len(chunks)
            if chunks
            else 0,
        )

        return chunks

    def _generate_with_chunking(
        self,
        document_text: str,
        document_name: str,
        page_data: List[tuple[int, str]],
        max_cards: int,
    ) -> List[FlashcardData]:
        """
        Generate flashcards by processing document in chunks.

        Args:
            document_text: Full document text
            document_name: Name of the source document
            page_data: List of (page_number, page_text) tuples
            max_cards: Maximum total flashcards to generate

        Returns:
            Combined list of flashcards from all chunks
        """
        chunks = self._chunk_document(document_text, page_data)
        all_flashcards = []

        # Distribute cards across chunks
        cards_per_chunk = max(1, max_cards // len(chunks))

        for i, (chunk_text, chunk_pages) in enumerate(chunks, 1):
            logger.info(
                "processing_chunk",
                chunk=i,
                total_chunks=len(chunks),
                chunk_pages=len(chunk_pages),
            )

            try:
                flashcards = self._generate_single(
                    chunk_text, document_name, chunk_pages, cards_per_chunk
                )
                all_flashcards.extend(flashcards)

                # Stop if we've reached max cards
                if len(all_flashcards) >= max_cards:
                    break

            except Exception as e:
                logger.warning(
                    "chunk_processing_failed", chunk=i, error=str(e), continue_anyway=True
                )
                # Continue with other chunks even if one fails
                continue

        return all_flashcards[:max_cards]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException,)),
        reraise=True,
    )
    def _generate_single(
        self,
        document_text: str,
        document_name: str,
        page_data: List[tuple[int, str]],
        max_cards: int,
    ) -> List[FlashcardData]:
        """
        Generate flashcards in single API call with retry logic.

        Args:
            document_text: Document text (or chunk)
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

        # Combine prompts for Ollama (it doesn't have separate system/user)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.7, "num_predict": 4000},
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/generate", json=payload, timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            response_text = result.get("response", "")

            if not response_text:
                raise AIProviderError("Empty response from Ollama")

            # Parse and validate flashcards
            flashcards = parse_flashcard_response(response_text, document_name)

            return flashcards

        except requests.exceptions.RequestException as e:
            logger.error("ollama_request_failed", error=str(e))
            raise AIProviderError(f"Ollama API request failed: {str(e)}")
        except Exception as e:
            logger.error("ollama_generation_error", error=str(e))
            raise
