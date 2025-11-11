"""
Spaced Repetition Service

Implements the SuperMemo 2 (SM-2) algorithm for optimal flashcard review scheduling.
The SM-2 algorithm adjusts review intervals based on user performance to maximize retention.

Reference: https://www.supermemo.com/en/archives1990-2015/english/ol/sm2
"""

from datetime import datetime, timedelta
from typing import Tuple


class SM2Algorithm:
    """
    SuperMemo 2 spaced repetition algorithm.

    The SM-2 algorithm calculates optimal review intervals based on:
    - Quality of recall (0-5 rating)
    - Current ease factor (difficulty multiplier)
    - Previous interval
    - Number of successful repetitions

    Quality ratings:
    - 0: Complete blackout (total failure)
    - 1: Incorrect response; correct one seemed familiar
    - 2: Incorrect response; correct one remembered
    - 3: Correct response with serious difficulty
    - 4: Correct response after hesitation
    - 5: Perfect response (immediate recall)

    Correct answers: quality >= 3
    Incorrect answers: quality < 3
    """

    # Minimum ease factor to prevent cards from becoming too difficult
    MIN_EASE_FACTOR: float = 1.3

    # Default ease factor for new cards
    DEFAULT_EASE_FACTOR: float = 2.5

    @staticmethod
    def calculate_next_interval(
        quality: int,
        ease_factor: float,
        interval_days: int,
        repetitions: int,
    ) -> Tuple[float, int, int]:
        """
        Calculate next review parameters based on SM-2 algorithm.

        Args:
            quality: User's recall quality rating (0-5)
                - 0-2: Incorrect answer (restart learning)
                - 3-5: Correct answer (increase interval)
            ease_factor: Current ease factor (minimum 1.3)
            interval_days: Days since last review
            repetitions: Number of consecutive successful reviews

        Returns:
            Tuple of (new_ease_factor, new_interval_days, new_repetitions)

        Raises:
            ValueError: If quality is not between 0 and 5

        Example:
            >>> SM2Algorithm.calculate_next_interval(quality=4, ease_factor=2.5, interval_days=1, repetitions=1)
            (2.5, 6, 2)

            >>> SM2Algorithm.calculate_next_interval(quality=2, ease_factor=2.5, interval_days=6, repetitions=2)
            (2.18, 1, 0)
        """
        if not (0 <= quality <= 5):
            raise ValueError(f"Quality must be between 0 and 5, got {quality}")

        if ease_factor < SM2Algorithm.MIN_EASE_FACTOR:
            ease_factor = SM2Algorithm.MIN_EASE_FACTOR

        # Calculate new ease factor
        # Formula: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        # This adjusts ease factor based on recall quality
        new_ease = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        new_ease = max(SM2Algorithm.MIN_EASE_FACTOR, new_ease)

        # Determine interval and repetitions based on recall quality
        if quality < 3:
            # Incorrect answer - reset to learning phase
            new_reps = 0
            new_interval = 1  # Review again tomorrow
        else:
            # Correct answer - increase interval
            new_reps = repetitions + 1

            if new_reps == 1:
                # First successful review
                new_interval = 1
            elif new_reps == 2:
                # Second successful review
                new_interval = 6
            else:
                # Subsequent reviews - multiply previous interval by ease factor
                new_interval = round(interval_days * new_ease)

        return new_ease, new_interval, new_reps

    @staticmethod
    def get_next_review_date(interval_days: int, from_date: datetime | None = None) -> datetime:
        """
        Calculate the next review date based on interval.

        Args:
            interval_days: Number of days until next review
            from_date: Base date for calculation (defaults to current UTC time)

        Returns:
            DateTime when the card should next be reviewed

        Example:
            >>> SM2Algorithm.get_next_review_date(6)
            datetime.datetime(2025, 11, 10, 12, 0, 0)  # 6 days from now
        """
        if from_date is None:
            from_date = datetime.utcnow()

        return from_date + timedelta(days=interval_days)

    @staticmethod
    def is_due_for_review(next_review_date: datetime | None) -> bool:
        """
        Check if a card is due for review.

        Args:
            next_review_date: Scheduled review date (None means never reviewed)

        Returns:
            True if card should be reviewed now, False otherwise

        Example:
            >>> SM2Algorithm.is_due_for_review(None)
            True

            >>> past_date = datetime.utcnow() - timedelta(days=1)
            >>> SM2Algorithm.is_due_for_review(past_date)
            True

            >>> future_date = datetime.utcnow() + timedelta(days=1)
            >>> SM2Algorithm.is_due_for_review(future_date)
            False
        """
        if next_review_date is None:
            # Never reviewed before - always due
            return True

        return next_review_date <= datetime.utcnow()

    @staticmethod
    def get_quality_from_correct(correct: bool, difficulty: str = "normal") -> int:
        """
        Convert a simple correct/incorrect answer to a quality rating.

        This is a helper for simpler UIs that don't ask for granular quality ratings.

        Args:
            correct: Whether the answer was correct
            difficulty: User's perceived difficulty ('easy', 'normal', 'hard')

        Returns:
            Quality rating (0-5)

        Example:
            >>> SM2Algorithm.get_quality_from_correct(True, 'easy')
            5

            >>> SM2Algorithm.get_quality_from_correct(True, 'hard')
            3

            >>> SM2Algorithm.get_quality_from_correct(False)
            0
        """
        if not correct:
            return 0  # Complete failure

        # Map difficulty to quality rating
        difficulty_map = {
            "easy": 5,  # Perfect response
            "normal": 4,  # Good response with slight hesitation
            "hard": 3,  # Correct but with serious difficulty
        }

        return difficulty_map.get(difficulty.lower(), 4)
