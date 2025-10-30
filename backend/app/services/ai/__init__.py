"""
AI Provider Package

Contains AI provider implementations for flashcard generation.
Supports multiple providers: OpenAI, Anthropic, and Ollama.
"""

from app.services.ai.base_provider import (
    AIProvider,
    FlashcardData,
    AIServiceError,
    AIProviderError,
    AIValidationError,
)
from app.services.ai.factory import get_ai_provider

__all__ = [
    "AIProvider",
    "FlashcardData",
    "AIServiceError",
    "AIProviderError",
    "AIValidationError",
    "get_ai_provider",
]
