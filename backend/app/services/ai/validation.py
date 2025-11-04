"""
Shared validation utilities for AI provider responses.

Contains common parsing and validation logic used across all AI providers.
"""

from typing import List
import json
import structlog

from app.services.ai.base_provider import FlashcardData, AIValidationError

logger = structlog.get_logger()


def parse_flashcard_response(
    response_text: str,
    document_name: str,
) -> List[FlashcardData]:
    """
    Parse AI provider JSON response into FlashcardData objects.

    This shared function ensures consistent validation and error handling
    across all AI providers (OpenAI, Anthropic, Ollama).

    Args:
        response_text: JSON response from AI provider
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
