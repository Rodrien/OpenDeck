"""
Shared Prompt Templates for AI Providers

Contains reusable prompt templates and builders for flashcard generation.
These prompts are shared across all AI providers to ensure consistent output.
"""

from typing import List
import structlog

logger = structlog.get_logger()


def build_system_prompt(document_name: str, max_cards: int) -> str:
    """
    Build system prompt for AI model.

    This prompt instructs the AI to generate high-quality flashcards with
    proper source attribution, which is critical per CLAUDE.md requirements.

    Args:
        document_name: Name of the source document
        max_cards: Maximum number of flashcards to generate

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


def build_user_prompt(
    document_text: str, page_data: List[tuple[int, str]]
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
    original_length = len(document_text)
    if original_length > max_chars:
        document_text = document_text[:max_chars] + "\n\n[Document truncated...]"
        logger.warning(
            "document_truncated",
            original_chars=original_length,
            truncated_to=max_chars,
            chars_removed=original_length - max_chars,
            message=f"Document truncated from {original_length} to {max_chars} characters to fit within token limits"
        )

    # Include page information for better source attribution
    page_info = "\n".join(
        [f"Page {num}: {len(text)} characters" for num, text in page_data[:10]]
    )

    return f"""Document Information:
{page_info}

Document Content:
{document_text}

Please generate flashcards from this document. Remember to include precise source attribution (page number) for each flashcard."""
