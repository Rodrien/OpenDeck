"""
Unit Tests for AI Providers

Tests the AI provider factory and individual provider implementations.
Uses mocking to avoid actual API calls during testing.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from app.services.ai import (
    get_ai_provider,
    FlashcardData,
    AIProviderError,
    AIValidationError,
)
from app.services.ai.openai_provider import OpenAIProvider
from app.services.ai.anthropic_provider import AnthropicProvider
from app.services.ai.ollama_provider import OllamaProvider


# Sample test data
SAMPLE_DOCUMENT_TEXT = "This is a test document about photosynthesis."
SAMPLE_DOCUMENT_NAME = "biology_chapter1.pdf"
SAMPLE_PAGE_DATA = [(1, "Page 1 content about photosynthesis")]
SAMPLE_JSON_RESPONSE = json.dumps({
    "flashcards": [
        {
            "question": "What is photosynthesis?",
            "answer": "The process by which plants convert light energy into chemical energy.",
            "source": "biology_chapter1.pdf - Page 1"
        }
    ]
})


class TestAIProviderFactory:
    """Test the AI provider factory function."""

    @patch('app.services.ai.factory.settings')
    def test_get_provider_openai(self, mock_settings):
        """Test factory returns OpenAI provider."""
        mock_settings.ai_provider = "openai"
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4"
        mock_settings.ai_timeout_seconds = 60
        mock_settings.ai_max_retries = 3

        provider = get_ai_provider()
        assert isinstance(provider, OpenAIProvider)
        assert provider.provider_name == "openai"

    @patch('app.services.ai.factory.settings')
    def test_get_provider_anthropic(self, mock_settings):
        """Test factory returns Anthropic provider."""
        mock_settings.ai_provider = "anthropic"
        mock_settings.anthropic_api_key = "test-key"
        mock_settings.anthropic_model = "claude-3-sonnet-20240229"
        mock_settings.ai_timeout_seconds = 60
        mock_settings.ai_max_retries = 3

        provider = get_ai_provider()
        assert isinstance(provider, AnthropicProvider)
        assert provider.provider_name == "anthropic"

    @patch('app.services.ai.factory.settings')
    def test_get_provider_ollama(self, mock_settings):
        """Test factory returns Ollama provider."""
        mock_settings.ai_provider = "ollama"
        mock_settings.ollama_base_url = "http://localhost:11434"
        mock_settings.ollama_model = "llama2"
        mock_settings.ollama_timeout_seconds = 120

        provider = get_ai_provider()
        assert isinstance(provider, OllamaProvider)
        assert provider.provider_name == "ollama"

    def test_get_provider_invalid(self):
        """Test factory raises error for invalid provider."""
        with pytest.raises(AIProviderError, match="Unknown AI provider"):
            with patch('app.services.ai.factory.settings') as mock_settings:
                mock_settings.ai_provider = "invalid_provider"
                get_ai_provider()

    @patch('app.services.ai.factory.settings')
    def test_get_provider_override(self, mock_settings):
        """Test factory accepts provider override."""
        # Set default to openai
        mock_settings.ai_provider = "openai"
        mock_settings.ollama_base_url = "http://localhost:11434"
        mock_settings.ollama_model = "llama2"
        mock_settings.ollama_timeout_seconds = 120

        # Override with ollama
        provider = get_ai_provider("ollama")
        assert isinstance(provider, OllamaProvider)


class TestFlashcardData:
    """Test FlashcardData validation."""

    def test_valid_flashcard(self):
        """Test creating valid flashcard."""
        flashcard = FlashcardData(
            question="What is AI?",
            answer="Artificial Intelligence",
            source="doc.pdf - Page 1"
        )
        assert flashcard.question == "What is AI?"
        assert flashcard.answer == "Artificial Intelligence"
        assert flashcard.source == "doc.pdf - Page 1"

    def test_empty_question(self):
        """Test flashcard with empty question raises error."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            FlashcardData(
                question="",
                answer="Some answer",
                source="doc.pdf - Page 1"
            )

    def test_empty_answer(self):
        """Test flashcard with empty answer raises error."""
        with pytest.raises(ValueError, match="Answer cannot be empty"):
            FlashcardData(
                question="Some question?",
                answer="",
                source="doc.pdf - Page 1"
            )

    def test_empty_source(self):
        """Test flashcard with empty source raises error."""
        with pytest.raises(ValueError, match="Source attribution is required"):
            FlashcardData(
                question="Some question?",
                answer="Some answer",
                source=""
            )

    def test_short_source(self):
        """Test flashcard with too short source raises error."""
        with pytest.raises(ValueError, match="Source attribution must include"):
            FlashcardData(
                question="Some question?",
                answer="Some answer",
                source="pg1"  # Too short
            )


class TestOpenAIProvider:
    """Test OpenAI provider implementation."""

    @patch('app.services.ai.openai_provider.OpenAI')
    @patch('app.services.ai.openai_provider.settings')
    def test_openai_initialization(self, mock_settings, mock_openai_class):
        """Test OpenAI provider initialization."""
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4"
        mock_settings.ai_timeout_seconds = 60
        mock_settings.ai_max_retries = 3

        provider = OpenAIProvider()
        assert provider.provider_name == "openai"
        assert provider.model == "gpt-4"

    @patch('app.services.ai.openai_provider.settings')
    def test_openai_missing_api_key(self, mock_settings):
        """Test OpenAI provider fails without API key."""
        mock_settings.openai_api_key = None

        with pytest.raises(ValueError, match="OpenAI API key is required"):
            OpenAIProvider()


class TestAnthropicProvider:
    """Test Anthropic provider implementation."""

    @patch('app.services.ai.anthropic_provider.Anthropic')
    @patch('app.services.ai.anthropic_provider.settings')
    def test_anthropic_initialization(self, mock_settings, mock_anthropic_class):
        """Test Anthropic provider initialization."""
        mock_settings.anthropic_api_key = "test-key"
        mock_settings.anthropic_model = "claude-3-sonnet-20240229"
        mock_settings.ai_timeout_seconds = 60
        mock_settings.ai_max_retries = 3

        provider = AnthropicProvider()
        assert provider.provider_name == "anthropic"
        assert provider.model == "claude-3-sonnet-20240229"

    @patch('app.services.ai.anthropic_provider.settings')
    def test_anthropic_missing_api_key(self, mock_settings):
        """Test Anthropic provider fails without API key."""
        mock_settings.anthropic_api_key = None

        with pytest.raises(ValueError, match="Anthropic API key is required"):
            AnthropicProvider()


class TestOllamaProvider:
    """Test Ollama provider implementation."""

    @patch('app.services.ai.ollama_provider.settings')
    def test_ollama_initialization(self, mock_settings):
        """Test Ollama provider initialization."""
        mock_settings.ollama_base_url = "http://localhost:11434"
        mock_settings.ollama_model = "llama2"
        mock_settings.ollama_timeout_seconds = 120

        provider = OllamaProvider()
        assert provider.provider_name == "ollama"
        assert provider.model == "llama2"
        assert provider.base_url == "http://localhost:11434"

    @patch('app.services.ai.ollama_provider.requests.get')
    @patch('app.services.ai.ollama_provider.settings')
    def test_ollama_health_check_success(self, mock_settings, mock_get):
        """Test Ollama health check passes."""
        mock_settings.ollama_base_url = "http://localhost:11434"
        mock_settings.ollama_model = "llama2"
        mock_settings.ollama_timeout_seconds = 120

        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "llama2"}]
        }
        mock_get.return_value = mock_response

        provider = OllamaProvider()
        assert provider.health_check() is True

    @patch('app.services.ai.ollama_provider.requests.get')
    @patch('app.services.ai.ollama_provider.settings')
    def test_ollama_health_check_failure(self, mock_settings, mock_get):
        """Test Ollama health check fails when server unreachable."""
        mock_settings.ollama_base_url = "http://localhost:11434"
        mock_settings.ollama_model = "llama2"
        mock_settings.ollama_timeout_seconds = 120

        # Mock connection error
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Connection refused")

        provider = OllamaProvider()
        assert provider.health_check() is False

    @patch('app.services.ai.ollama_provider.settings')
    def test_ollama_needs_chunking(self, mock_settings):
        """Test document chunking detection."""
        mock_settings.ollama_base_url = "http://localhost:11434"
        mock_settings.ollama_model = "llama2"
        mock_settings.ollama_timeout_seconds = 120

        provider = OllamaProvider()

        # Small document doesn't need chunking
        small_text = "x" * 1000
        assert provider._needs_chunking(small_text) is False

        # Large document needs chunking
        large_text = "x" * 20000
        assert provider._needs_chunking(large_text) is True

    @patch('app.services.ai.ollama_provider.requests.post')
    @patch('app.services.ai.ollama_provider.settings')
    def test_ollama_generate_flashcards(self, mock_settings, mock_post):
        """Test Ollama flashcard generation."""
        mock_settings.ollama_base_url = "http://localhost:11434"
        mock_settings.ollama_model = "llama2"
        mock_settings.ollama_timeout_seconds = 120

        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": SAMPLE_JSON_RESPONSE,
            "done": True
        }
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        flashcards = provider.generate_flashcards(
            document_text=SAMPLE_DOCUMENT_TEXT,
            document_name=SAMPLE_DOCUMENT_NAME,
            page_data=SAMPLE_PAGE_DATA,
            max_cards=50
        )

        assert len(flashcards) == 1
        assert flashcards[0].question == "What is photosynthesis?"
        assert "biology_chapter1.pdf" in flashcards[0].source


class TestProviderResponseParsing:
    """Test response parsing across all providers."""

    @patch('app.services.ai.ollama_provider.settings')
    def test_parse_valid_response(self, mock_settings):
        """Test parsing valid JSON response."""
        mock_settings.ollama_base_url = "http://localhost:11434"
        mock_settings.ollama_model = "llama2"
        mock_settings.ollama_timeout_seconds = 120

        provider = OllamaProvider()
        flashcards = provider._parse_response(
            SAMPLE_JSON_RESPONSE,
            SAMPLE_DOCUMENT_NAME
        )

        assert len(flashcards) == 1
        assert flashcards[0].question == "What is photosynthesis?"

    @patch('app.services.ai.ollama_provider.settings')
    def test_parse_invalid_json(self, mock_settings):
        """Test parsing invalid JSON raises error."""
        mock_settings.ollama_base_url = "http://localhost:11434"
        mock_settings.ollama_model = "llama2"
        mock_settings.ollama_timeout_seconds = 120

        provider = OllamaProvider()

        with pytest.raises(AIValidationError, match="Failed to parse JSON"):
            provider._parse_response("not valid json", SAMPLE_DOCUMENT_NAME)

    @patch('app.services.ai.ollama_provider.settings')
    def test_parse_missing_flashcards_field(self, mock_settings):
        """Test parsing response missing flashcards field."""
        mock_settings.ollama_base_url = "http://localhost:11434"
        mock_settings.ollama_model = "llama2"
        mock_settings.ollama_timeout_seconds = 120

        provider = OllamaProvider()

        with pytest.raises(AIValidationError, match="missing 'flashcards' field"):
            provider._parse_response('{"data": []}', SAMPLE_DOCUMENT_NAME)

    @patch('app.services.ai.ollama_provider.settings')
    def test_parse_empty_flashcards(self, mock_settings):
        """Test parsing response with no valid flashcards."""
        mock_settings.ollama_base_url = "http://localhost:11434"
        mock_settings.ollama_model = "llama2"
        mock_settings.ollama_timeout_seconds = 120

        provider = OllamaProvider()

        with pytest.raises(AIValidationError, match="No valid flashcards generated"):
            provider._parse_response('{"flashcards": []}', SAMPLE_DOCUMENT_NAME)
