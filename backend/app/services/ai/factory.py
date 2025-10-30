"""
AI Provider Factory

Creates the appropriate AI provider instance based on configuration.
Enables dependency injection and configuration-driven provider selection.
"""

from typing import Optional
import structlog

from app.config import settings
from app.services.ai.base_provider import AIProvider, AIProviderError

logger = structlog.get_logger()


def get_ai_provider(provider_name: Optional[str] = None) -> AIProvider:
    """
    Factory function to instantiate correct AI provider.

    This function creates the appropriate provider based on configuration,
    enabling easy switching between OpenAI, Anthropic, and Ollama without
    code changes - just update environment variables.

    Args:
        provider_name: Optional override for provider selection.
                      If None, uses settings.ai_provider.
                      Valid values: 'openai', 'anthropic', 'ollama'

    Returns:
        Configured AIProvider instance (OpenAIProvider, AnthropicProvider, or OllamaProvider)

    Raises:
        AIProviderError: If provider is unknown or configuration is invalid
        ImportError: If required provider package is not installed
        ValueError: If provider credentials are missing

    Examples:
        # Use configured provider from environment
        provider = get_ai_provider()

        # Override to use specific provider
        provider = get_ai_provider("ollama")

        # Generate flashcards
        flashcards = provider.generate_flashcards(...)
    """
    provider = provider_name or settings.ai_provider

    logger.info("initializing_ai_provider", provider=provider)

    try:
        if provider == "anthropic":
            from app.services.ai.anthropic_provider import AnthropicProvider

            return AnthropicProvider()

        elif provider == "openai":
            from app.services.ai.openai_provider import OpenAIProvider

            return OpenAIProvider()

        elif provider == "ollama":
            from app.services.ai.ollama_provider import OllamaProvider

            return OllamaProvider()

        else:
            raise AIProviderError(
                f"Unknown AI provider: '{provider}'. "
                f"Supported providers: 'openai', 'anthropic', 'ollama'. "
                f"Set AI_PROVIDER environment variable to one of these values."
            )

    except ImportError as e:
        logger.error(
            "ai_provider_import_failed",
            provider=provider,
            error=str(e),
        )
        raise AIProviderError(
            f"Failed to import {provider} provider. "
            f"Make sure required package is installed. "
            f"Error: {str(e)}"
        )

    except ValueError as e:
        logger.error(
            "ai_provider_config_invalid",
            provider=provider,
            error=str(e),
        )
        raise AIProviderError(
            f"Invalid configuration for {provider} provider: {str(e)}"
        )

    except Exception as e:
        logger.error(
            "ai_provider_initialization_failed",
            provider=provider,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise


# Convenience function for backward compatibility
def get_ai_service(provider: Optional[str] = None):
    """
    Legacy alias for get_ai_provider.

    Deprecated: Use get_ai_provider() instead.

    Args:
        provider: Optional provider name

    Returns:
        AIProvider instance
    """
    logger.warning(
        "deprecated_function_call",
        function="get_ai_service",
        use_instead="get_ai_provider",
    )
    return get_ai_provider(provider)
