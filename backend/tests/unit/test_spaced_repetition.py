"""
Unit Tests for Spaced Repetition (SM-2 Algorithm)

Tests the SuperMemo 2 algorithm implementation for flashcard scheduling.
"""

import pytest
from datetime import datetime, timedelta
from app.services.spaced_repetition import SM2Algorithm


class TestSM2CalculateNextInterval:
    """Test SM2Algorithm.calculate_next_interval method."""

    def test_first_correct_review(self):
        """Test first successful review (quality >= 3)."""
        # First correct review should set interval to 1 day
        new_ease, new_interval, new_reps = SM2Algorithm.calculate_next_interval(
            quality=4,
            ease_factor=2.5,
            interval_days=0,
            repetitions=0,
        )

        assert new_reps == 1
        assert new_interval == 1
        assert new_ease == 2.5  # Ease factor should remain same for quality=4

    def test_second_correct_review(self):
        """Test second successful review."""
        # Second correct review should set interval to 6 days
        new_ease, new_interval, new_reps = SM2Algorithm.calculate_next_interval(
            quality=4,
            ease_factor=2.5,
            interval_days=1,
            repetitions=1,
        )

        assert new_reps == 2
        assert new_interval == 6
        assert new_ease == 2.5

    def test_third_correct_review(self):
        """Test third successful review (interval multiplied by ease factor)."""
        new_ease, new_interval, new_reps = SM2Algorithm.calculate_next_interval(
            quality=4,
            ease_factor=2.5,
            interval_days=6,
            repetitions=2,
        )

        assert new_reps == 3
        assert new_interval == round(6 * 2.5)  # 15 days
        assert new_ease == 2.5

    def test_incorrect_answer_resets_learning(self):
        """Test that quality < 3 resets the learning process."""
        # Even after multiple successful reviews, failing resets everything
        new_ease, new_interval, new_reps = SM2Algorithm.calculate_next_interval(
            quality=2,  # Incorrect
            ease_factor=2.7,
            interval_days=15,
            repetitions=3,
        )

        assert new_reps == 0  # Reset to beginning
        assert new_interval == 1  # Back to 1 day
        # Ease factor should decrease
        assert new_ease < 2.7

    def test_quality_zero_complete_failure(self):
        """Test quality=0 (complete blackout)."""
        new_ease, new_interval, new_reps = SM2Algorithm.calculate_next_interval(
            quality=0,
            ease_factor=2.5,
            interval_days=6,
            repetitions=2,
        )

        assert new_reps == 0
        assert new_interval == 1
        # Ease factor should significantly decrease
        expected_ease = 2.5 + (0.1 - (5 - 0) * (0.08 + (5 - 0) * 0.02))
        assert new_ease == max(1.3, expected_ease)

    def test_quality_five_perfect_recall(self):
        """Test quality=5 (perfect recall)."""
        new_ease, new_interval, new_reps = SM2Algorithm.calculate_next_interval(
            quality=5,
            ease_factor=2.5,
            interval_days=6,
            repetitions=2,
        )

        assert new_reps == 3
        # Ease factor should increase for quality=5
        expected_ease = 2.5 + (0.1 - (5 - 5) * (0.08 + (5 - 5) * 0.02))
        assert new_ease == expected_ease
        assert new_ease > 2.5

    def test_ease_factor_minimum_limit(self):
        """Test that ease factor never goes below 1.3."""
        # Start with minimum ease factor and give poor quality
        new_ease, _, _ = SM2Algorithm.calculate_next_interval(
            quality=0,
            ease_factor=1.3,
            interval_days=1,
            repetitions=1,
        )

        assert new_ease >= SM2Algorithm.MIN_EASE_FACTOR
        assert new_ease == 1.3

    def test_quality_three_minimum_correct(self):
        """Test quality=3 (correct with serious difficulty)."""
        new_ease, new_interval, new_reps = SM2Algorithm.calculate_next_interval(
            quality=3,
            ease_factor=2.5,
            interval_days=0,
            repetitions=0,
        )

        # Quality=3 is still correct, so should proceed
        assert new_reps == 1
        assert new_interval == 1
        # But ease factor should decrease slightly
        expected_ease = 2.5 + (0.1 - (5 - 3) * (0.08 + (5 - 3) * 0.02))
        assert new_ease == max(1.3, expected_ease)

    def test_invalid_quality_raises_error(self):
        """Test that invalid quality values raise ValueError."""
        with pytest.raises(ValueError, match="Quality must be between 0 and 5"):
            SM2Algorithm.calculate_next_interval(
                quality=6,  # Invalid
                ease_factor=2.5,
                interval_days=1,
                repetitions=1,
            )

        with pytest.raises(ValueError, match="Quality must be between 0 and 5"):
            SM2Algorithm.calculate_next_interval(
                quality=-1,  # Invalid
                ease_factor=2.5,
                interval_days=1,
                repetitions=1,
            )

    def test_ease_factor_progression(self):
        """Test how ease factor changes with different quality ratings."""
        base_ease = 2.5

        # Quality 0-2 should decrease ease factor
        for quality in [0, 1, 2]:
            new_ease, _, _ = SM2Algorithm.calculate_next_interval(
                quality=quality,
                ease_factor=base_ease,
                interval_days=1,
                repetitions=1,
            )
            assert new_ease < base_ease, f"Quality {quality} should decrease ease factor"

        # Quality 5 should increase ease factor
        new_ease, _, _ = SM2Algorithm.calculate_next_interval(
            quality=5,
            ease_factor=base_ease,
            interval_days=1,
            repetitions=1,
        )
        assert new_ease > base_ease

    def test_interval_growth_over_time(self):
        """Test that intervals grow exponentially with successful reviews."""
        ease_factor = 2.5
        interval = 0
        repetitions = 0

        intervals = []

        for _ in range(5):
            ease_factor, interval, repetitions = SM2Algorithm.calculate_next_interval(
                quality=4,
                ease_factor=ease_factor,
                interval_days=interval,
                repetitions=repetitions,
            )
            intervals.append(interval)

        # Check progression: 1, 6, then exponential growth
        assert intervals[0] == 1
        assert intervals[1] == 6
        assert intervals[2] > intervals[1]
        assert intervals[3] > intervals[2]
        assert intervals[4] > intervals[3]


class TestSM2GetNextReviewDate:
    """Test SM2Algorithm.get_next_review_date method."""

    def test_calculates_future_date(self):
        """Test that next review date is correctly calculated."""
        base_date = datetime(2025, 11, 4, 12, 0, 0)
        interval_days = 6

        next_date = SM2Algorithm.get_next_review_date(interval_days, base_date)

        expected_date = base_date + timedelta(days=6)
        assert next_date == expected_date

    def test_uses_current_time_by_default(self):
        """Test that current time is used when no base date provided."""
        before = datetime.utcnow()
        next_date = SM2Algorithm.get_next_review_date(1)
        after = datetime.utcnow()

        # Should be approximately 1 day from now
        expected_min = before + timedelta(days=1)
        expected_max = after + timedelta(days=1)

        assert expected_min <= next_date <= expected_max

    def test_zero_interval(self):
        """Test that zero interval returns the same date."""
        base_date = datetime(2025, 11, 4, 12, 0, 0)
        next_date = SM2Algorithm.get_next_review_date(0, base_date)
        assert next_date == base_date


class TestSM2IsDueForReview:
    """Test SM2Algorithm.is_due_for_review method."""

    def test_null_review_date_is_due(self):
        """Test that cards never reviewed are always due."""
        assert SM2Algorithm.is_due_for_review(None) is True

    def test_past_date_is_due(self):
        """Test that past review dates are due."""
        past_date = datetime.utcnow() - timedelta(days=1)
        assert SM2Algorithm.is_due_for_review(past_date) is True

    def test_future_date_not_due(self):
        """Test that future review dates are not due."""
        future_date = datetime.utcnow() + timedelta(days=1)
        assert SM2Algorithm.is_due_for_review(future_date) is False

    def test_current_time_is_due(self):
        """Test that current time is considered due."""
        # A review date equal to current time should be due
        current_time = datetime.utcnow()
        assert SM2Algorithm.is_due_for_review(current_time) is True


class TestSM2GetQualityFromCorrect:
    """Test SM2Algorithm.get_quality_from_correct helper method."""

    def test_correct_easy(self):
        """Test correct answer with easy difficulty."""
        quality = SM2Algorithm.get_quality_from_correct(True, "easy")
        assert quality == 5

    def test_correct_normal(self):
        """Test correct answer with normal difficulty."""
        quality = SM2Algorithm.get_quality_from_correct(True, "normal")
        assert quality == 4

    def test_correct_hard(self):
        """Test correct answer with hard difficulty."""
        quality = SM2Algorithm.get_quality_from_correct(True, "hard")
        assert quality == 3

    def test_incorrect_answer(self):
        """Test incorrect answer always returns 0."""
        assert SM2Algorithm.get_quality_from_correct(False, "easy") == 0
        assert SM2Algorithm.get_quality_from_correct(False, "normal") == 0
        assert SM2Algorithm.get_quality_from_correct(False, "hard") == 0
        assert SM2Algorithm.get_quality_from_correct(False) == 0

    def test_default_difficulty(self):
        """Test default difficulty for correct answer."""
        quality = SM2Algorithm.get_quality_from_correct(True)
        assert quality == 4  # Default is 'normal'

    def test_invalid_difficulty_defaults_to_normal(self):
        """Test that invalid difficulty defaults to normal."""
        quality = SM2Algorithm.get_quality_from_correct(True, "unknown")
        assert quality == 4


class TestSM2RealWorldScenario:
    """Test realistic study scenarios."""

    def test_successful_learning_progression(self):
        """Test a card successfully learned over multiple reviews."""
        # New card, never reviewed
        ease = 2.5
        interval = 0
        reps = 0

        # Review 1: Good recall
        ease, interval, reps = SM2Algorithm.calculate_next_interval(4, ease, interval, reps)
        assert reps == 1
        assert interval == 1

        # Review 2: Good recall
        ease, interval, reps = SM2Algorithm.calculate_next_interval(4, ease, interval, reps)
        assert reps == 2
        assert interval == 6

        # Review 3: Perfect recall
        ease, interval, reps = SM2Algorithm.calculate_next_interval(5, ease, interval, reps)
        assert reps == 3
        assert interval == 15  # 6 * 2.6 (ease increased by quality=5)
        assert ease > 2.5  # Ease factor improved

    def test_learning_with_setback(self):
        """Test a card that has a setback during learning."""
        ease = 2.5
        interval = 0
        reps = 0

        # Review 1: Good
        ease, interval, reps = SM2Algorithm.calculate_next_interval(4, ease, interval, reps)
        assert reps == 1

        # Review 2: Good
        ease, interval, reps = SM2Algorithm.calculate_next_interval(4, ease, interval, reps)
        assert reps == 2

        # Review 3: Forgot! (quality=2)
        ease, interval, reps = SM2Algorithm.calculate_next_interval(2, ease, interval, reps)
        assert reps == 0  # Back to square one
        assert interval == 1
        assert ease < 2.5  # Ease factor decreased

        # Review 4: Remembered again
        ease, interval, reps = SM2Algorithm.calculate_next_interval(4, ease, interval, reps)
        assert reps == 1
        assert interval == 1

    def test_mature_card_intervals(self):
        """Test intervals for a well-learned mature card."""
        ease = 2.6  # Card has been reviewed successfully many times
        interval = 60  # Review every 2 months
        reps = 10

        # Perfect recall
        ease, new_interval, reps = SM2Algorithm.calculate_next_interval(5, ease, interval, reps)

        assert reps == 11
        assert new_interval > 100  # Should be several months now
        assert ease > 2.6  # Ease continues to improve


class TestSM2Constants:
    """Test SM-2 algorithm constants."""

    def test_min_ease_factor(self):
        """Test minimum ease factor constant."""
        assert SM2Algorithm.MIN_EASE_FACTOR == 1.3

    def test_default_ease_factor(self):
        """Test default ease factor constant."""
        assert SM2Algorithm.DEFAULT_EASE_FACTOR == 2.5
