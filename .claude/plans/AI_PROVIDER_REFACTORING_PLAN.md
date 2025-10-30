# AI Provider Refactoring Plan

**Date**: 2025-10-29
**Status**: Planning
**Branch**: feature/ollama-ai-provider

## Overview

Refactor the AI service architecture to support multiple AI providers (Anthropic, OpenAI, and Ollama) with a clean, extensible design following SOLID principles. This will enable easy addition of new providers and configuration-driven provider selection.

## Current State Analysis

### Existing Implementation
**File**: `backend/app/services/ai_service.py:62-456`

**Issues**:
- Monolithic `AIService` class with if/else branching for OpenAI and Anthropic
- Difficult to test individual providers
- Hard to add new providers without modifying existing code
- Violates Single Responsibility Principle

**What's Already Working**:
- Configuration supports provider selection via `ai_provider` setting
- Document extraction and chunking implemented in `document_extractor.py`
- Source attribution requirement enforced
- Retry logic with tenacity
- Proper error handling and logging

## Proposed Architecture

```
┌─────────────────────────────────────────────┐
│         AIProvider (Protocol/ABC)           │
│  - generate_flashcards()                    │
│  - health_check()                           │
│  - provider_name property                   │
└─────────────────────────────────────────────┘
                    ▲
                    │ implements
        ┌───────────┼───────────┐
        │           │           │
┌───────────┐ ┌───────────┐ ┌───────────┐
│ Anthropic │ │  OpenAI   │ │  Ollama   │
│ Provider  │ │ Provider  │ │ Provider  │
└───────────┘ └───────────┘ └───────────┘
        │           │           │
        └───────────┼───────────┘
                    │
        ┌───────────▼───────────┐
        │  AIProviderFactory    │
        │  - get_provider()     │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ DocumentProcessor     │
        │    Service            │
        └───────────────────────┘
```

### Design Principles

1. **Single Responsibility**: Each provider handles only its specific API
2. **Open/Closed**: Easy to add new providers without modifying existing code
3. **Dependency Inversion**: DocumentProcessor depends on AIProvider interface
4. **Interface Segregation**: Common interface for all providers
5. **Liskov Substitution**: All providers are interchangeable

## Implementation Plan

### 1. Create Provider Interface

**File**: `backend/app/services/ai/base_provider.py`

```python
"""
Base AI Provider Interface

Defines the common contract that all AI providers must implement.
"""

from typing import Protocol, List
from dataclasses import dataclass


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
        if len(self.source.strip()) < 5:
            raise ValueError("Source attribution must include document name and page")


class AIProvider(Protocol):
    """
    Common interface for all AI providers.

    All providers must implement this interface to ensure consistent
    behavior across different AI backends.
    """

    @property
    def provider_name(self) -> str:
        """
        Provider identifier (e.g., 'openai', 'anthropic', 'ollama').

        Returns:
            Provider name as string
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
        ...

    def health_check(self) -> bool:
        """
        Verify provider is accessible and configured correctly.

        Returns:
            True if provider is healthy, False otherwise
        """
        ...
```

### 2. Implement Anthropic Provider

**File**: `backend/app/services/ai/anthropic_provider.py`

**Source**: Extract from `ai_service.py:106-122` and `ai_service.py:232-285`

**Key Features**:
- Use Anthropic's Messages API
- Implement retry logic with tenacity
- Support Claude 3 models (Opus, Sonnet, Haiku)
- Handle streaming responses (optional)
- System prompt + user message format

**Dependencies**:
```python
from anthropic import Anthropic, APIError
from tenacity import retry, stop_after_attempt, wait_exponential
```

### 3. Implement OpenAI Provider

**File**: `backend/app/services/ai/openai_provider.py`

**Source**: Extract from `ai_service.py:89-104` and `ai_service.py:174-230`

**Key Features**:
- Use OpenAI Chat Completions API
- JSON response format enforcement
- Support GPT-4, GPT-3.5-Turbo models
- Implement retry logic
- System + user message format

**Dependencies**:
```python
from openai import OpenAI, OpenAIError
from tenacity import retry, stop_after_attempt, wait_exponential
```

### 4. Implement Ollama Provider

**File**: `backend/app/services/ai/ollama_provider.py`

**New Implementation**

**Key Features**:
- HTTP client for Ollama REST API
- Support custom local models
- Chunking for large documents
- Streaming response support
- Context window management

**Ollama API Integration**:

```python
"""
Ollama Provider Implementation

Integrates with locally-hosted Ollama models via HTTP API.
"""

import requests
import json
from typing import List
import structlog

from app.config import settings
from app.services.ai.base_provider import FlashcardData, AIProvider

logger = structlog.get_logger()


class OllamaProvider(AIProvider):
    """
    Ollama AI provider for local model inference.

    Connects to Ollama server running on localhost (or configured URL).
    Supports any model available in Ollama (llama2, mistral, etc.).
    """

    def __init__(self):
        """Initialize Ollama provider."""
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout_seconds
        self.max_context_tokens = 4096  # Default, adjust based on model

    @property
    def provider_name(self) -> str:
        return "ollama"

    def health_check(self) -> bool:
        """Check if Ollama server is accessible."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error("ollama_health_check_failed", error=str(e))
            return False

    def generate_flashcards(
        self,
        document_text: str,
        document_name: str,
        page_data: List[tuple[int, str]],
        max_cards: int = 20,
    ) -> List[FlashcardData]:
        """Generate flashcards using Ollama model."""

        # Check if document needs chunking
        if self._needs_chunking(document_text):
            return self._generate_with_chunking(
                document_text, document_name, page_data, max_cards
            )
        else:
            return self._generate_single(
                document_text, document_name, page_data, max_cards
            )

    def _generate_single(
        self,
        document_text: str,
        document_name: str,
        page_data: List[tuple[int, str]],
        max_cards: int,
    ) -> List[FlashcardData]:
        """Generate flashcards in single API call."""

        system_prompt = self._build_system_prompt(document_name, max_cards)
        user_prompt = self._build_user_prompt(document_text, page_data)

        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.7,
                "num_predict": 4000,
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            response_text = result.get("response", "")

            # Parse and validate flashcards
            flashcards = self._parse_response(response_text, document_name)

            logger.info(
                "ollama_generation_success",
                document_name=document_name,
                flashcards_generated=len(flashcards),
            )

            return flashcards

        except Exception as e:
            logger.error("ollama_generation_failed", error=str(e))
            raise

    def _needs_chunking(self, text: str) -> bool:
        """Check if document exceeds context window."""
        # Rough approximation: 4 chars per token
        estimated_tokens = len(text) / 4
        return estimated_tokens > (self.max_context_tokens * 0.7)

    def _generate_with_chunking(
        self,
        document_text: str,
        document_name: str,
        page_data: List[tuple[int, str]],
        max_cards: int,
    ) -> List[FlashcardData]:
        """Generate flashcards by processing document in chunks."""

        # Split document into manageable chunks
        chunks = self._chunk_document(document_text, page_data)

        all_flashcards = []
        cards_per_chunk = max(1, max_cards // len(chunks))

        for chunk_text, chunk_pages in chunks:
            flashcards = self._generate_single(
                chunk_text,
                document_name,
                chunk_pages,
                cards_per_chunk
            )
            all_flashcards.extend(flashcards)

            if len(all_flashcards) >= max_cards:
                break

        return all_flashcards[:max_cards]

    # ... additional helper methods
```

**API Endpoint**: `POST {ollama_base_url}/api/generate`

**Request Format**:
```json
{
  "model": "llama2",
  "prompt": "System prompt + user prompt",
  "stream": false,
  "format": "json",
  "options": {
    "temperature": 0.7
  }
}
```

**Response Format**:
```json
{
  "model": "llama2",
  "created_at": "2023-08-04T19:22:45.499127Z",
  "response": "{\"flashcards\": [...]}",
  "done": true
}
```

### 5. Create Provider Factory

**File**: `backend/app/services/ai/factory.py`

```python
"""
AI Provider Factory

Creates the appropriate AI provider instance based on configuration.
"""

from typing import Optional
import structlog

from app.config import settings
from app.services.ai.base_provider import AIProvider
from app.services.ai.anthropic_provider import AnthropicProvider
from app.services.ai.openai_provider import OpenAIProvider
from app.services.ai.ollama_provider import OllamaProvider

logger = structlog.get_logger()


class AIProviderError(Exception):
    """Exception for AI provider errors."""
    pass


def get_ai_provider(provider_name: Optional[str] = None) -> AIProvider:
    """
    Factory function to instantiate correct AI provider.

    Args:
        provider_name: Optional override for provider selection.
                      If None, uses settings.ai_provider.

    Returns:
        Configured AIProvider instance

    Raises:
        AIProviderError: If provider is unknown or configuration is invalid
    """
    provider = provider_name or settings.ai_provider

    logger.info("initializing_ai_provider", provider=provider)

    try:
        if provider == "anthropic":
            return AnthropicProvider()
        elif provider == "openai":
            return OpenAIProvider()
        elif provider == "ollama":
            return OllamaProvider()
        else:
            raise AIProviderError(
                f"Unknown AI provider: {provider}. "
                f"Supported providers: anthropic, openai, ollama"
            )
    except Exception as e:
        logger.error(
            "ai_provider_initialization_failed",
            provider=provider,
            error=str(e)
        )
        raise
```

### 6. Update Configuration

**File**: `backend/app/config.py`

**Changes**:
```python
# AI Services
ai_provider: Literal["openai", "anthropic", "ollama"] = "openai"

# OpenAI Configuration
openai_api_key: str | None = None
openai_model: str = "gpt-4"

# Anthropic Configuration
anthropic_api_key: str | None = None
anthropic_model: str = "claude-3-sonnet-20240229"

# Ollama Configuration (NEW)
ollama_base_url: str = "http://localhost:11434"
ollama_model: str = "llama2"
ollama_timeout_seconds: int = 120

# Common AI Settings
ai_max_retries: int = 3
ai_timeout_seconds: int = 60
```

**Environment Variables** (`.env`):
```bash
# AI Provider Selection
AI_PROVIDER=ollama  # or 'openai', 'anthropic'

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT_SECONDS=120
```

### 7. Update Document Processor Service

**File**: `backend/app/services/document_processor.py`

**Changes**:
```python
from app.services.ai.factory import get_ai_provider
from app.services.ai.base_provider import AIProvider

class DocumentProcessorService:
    def __init__(
        self,
        session: Session,
        storage: StorageService,
        ai_provider: AIProvider | None = None,
        extractor: DocumentExtractor | None = None,
    ):
        self.session = session
        self.storage = storage
        self.ai_provider = ai_provider or get_ai_provider()  # Use factory
        self.extractor = extractor or DocumentExtractor()
        # ... rest of initialization
```

### 8. Shared Prompt Building

**File**: `backend/app/services/ai/prompts.py`

Extract common prompt building logic:

```python
"""
Shared Prompt Templates for AI Providers

Contains reusable prompt templates and builders for flashcard generation.
"""

def build_system_prompt(document_name: str, max_cards: int) -> str:
    """Build system prompt for AI model."""
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


def build_user_prompt(
    document_text: str,
    page_data: List[tuple[int, str]]
) -> str:
    """Build user prompt with document content."""
    # Truncate if document is very long
    max_chars = 15000
    if len(document_text) > max_chars:
        document_text = document_text[:max_chars] + "\n\n[Document truncated...]"

    # Include page information
    page_info = "\n".join(
        [f"Page {num}: {len(text)} characters" for num, text in page_data[:10]]
    )

    return f"""Document Information:
{page_info}

Document Content:
{document_text}

Please generate flashcards from this document. Remember to include precise source attribution (page number) for each flashcard."""
```

## File Structure

```
backend/app/services/ai/
├── __init__.py
├── base_provider.py          # AIProvider protocol, FlashcardData
├── prompts.py                # Shared prompt templates
├── anthropic_provider.py     # Anthropic implementation
├── openai_provider.py        # OpenAI implementation
├── ollama_provider.py        # Ollama implementation
└── factory.py                # Provider factory
```

## Migration Strategy

### Phase 1: Setup (No Breaking Changes)
1. Create new `backend/app/services/ai/` directory
2. Implement base provider interface
3. Create shared prompt utilities
4. Keep existing `ai_service.py` functional

### Phase 2: Provider Implementation
1. Implement AnthropicProvider (extract from existing code)
2. Implement OpenAIProvider (extract from existing code)
3. Implement OllamaProvider (new)
4. Create factory
5. Add unit tests for each provider

### Phase 3: Integration
1. Update DocumentProcessor to use factory
2. Run integration tests
3. Test with all three providers
4. Verify flashcard generation quality

### Phase 4: Cleanup
1. Deprecate old `ai_service.py`
2. Remove unused code
3. Update documentation
4. Update CLAUDE.md with new architecture

## Testing Strategy

### Unit Tests

**Test File**: `backend/tests/unit/services/ai/test_providers.py`

```python
def test_anthropic_provider_generates_flashcards():
    """Test Anthropic provider generates valid flashcards."""
    provider = AnthropicProvider()
    flashcards = provider.generate_flashcards(...)
    assert len(flashcards) > 0
    assert all(card.source for card in flashcards)

def test_openai_provider_generates_flashcards():
    """Test OpenAI provider generates valid flashcards."""
    # Similar test for OpenAI

def test_ollama_provider_generates_flashcards():
    """Test Ollama provider generates valid flashcards."""
    # Similar test for Ollama

def test_factory_returns_correct_provider():
    """Test factory returns correct provider based on config."""
    # Test factory logic
```

### Integration Tests

**Test File**: `backend/tests/integration/test_document_processing.py`

```python
@pytest.mark.parametrize("provider", ["openai", "anthropic", "ollama"])
def test_document_processing_with_provider(provider):
    """Test document processing with each provider."""
    # Test end-to-end with each provider
```

## Rollout Plan

1. **Local Development**: Test Ollama integration locally
2. **Staging**: Deploy with all three providers enabled
3. **Production**: Start with existing providers, add Ollama as optional
4. **Monitoring**: Track generation quality and performance by provider

## Benefits

### Immediate Benefits
- Clean separation of concerns
- Easy to test individual providers
- Support for local Ollama models (no API costs)
- Configuration-driven provider selection

### Long-term Benefits
- Easy to add new providers (Google Gemini, Cohere, etc.)
- Can run multiple providers in parallel for comparison
- Provider-specific optimizations without affecting others
- Better error isolation

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Ollama not running locally | Health check before processing, fallback to other provider |
| Different quality across providers | Add quality metrics, provider-specific prompt tuning |
| Breaking existing functionality | Comprehensive integration tests, gradual rollout |
| Performance differences | Monitor and optimize per-provider, timeout configuration |

## Success Criteria

- [ ] All three providers implement AIProvider interface
- [ ] Factory correctly instantiates providers based on config
- [ ] DocumentProcessor works with all providers
- [ ] All existing tests pass
- [ ] New provider-specific tests added
- [ ] Ollama generates flashcards locally
- [ ] Source attribution maintained across all providers
- [ ] Documentation updated

## Timeline Estimate

- **Phase 1 (Setup)**: 1-2 hours
- **Phase 2 (Implementation)**: 4-6 hours
- **Phase 3 (Integration)**: 2-3 hours
- **Phase 4 (Cleanup)**: 1-2 hours
- **Total**: ~8-13 hours

## References

- Current implementation: `backend/app/services/ai_service.py`
- Ollama API docs: https://github.com/ollama/ollama/blob/main/docs/api.md
- Clean Architecture principles: CLAUDE.md
- Configuration: `backend/app/config.py`
