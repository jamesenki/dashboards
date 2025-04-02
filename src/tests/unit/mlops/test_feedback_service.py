"""
Tests for the MLOps Feedback Service.
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.mlops.feedback import FeedbackService


class TestFeedbackService:
    """Test suite for the feedback service implementation."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.db_mock = MagicMock()
        self.model_registry_mock = MagicMock()
        self.feedback_service = FeedbackService(self.db_mock, self.model_registry_mock)

        # Sample mock data
        self.mock_feedback_data = [
            {
                "feedback_id": "fb-123",
                "model_name": "component_failure",
                "prediction_id": "pred-123",
                "device_id": "wh-123",
                "feedback_type": "false_positive",
                "created_at": datetime(2025, 1, 1),
                "details": {"issue": "no actual failure observed"},
            },
            {
                "feedback_id": "fb-456",
                "model_name": "component_failure",
                "prediction_id": "pred-456",
                "device_id": "wh-456",
                "feedback_type": "false_negative",
                "created_at": datetime(2025, 1, 2),
                "details": {"issue": "failure occurred but wasn't predicted"},
            },
        ]

    def test_init(self):
        """Test that the feedback service initializes correctly."""
        assert self.feedback_service.db == self.db_mock
        assert self.feedback_service.model_registry == self.model_registry_mock

    def test_record_feedback(self):
        """Test recording user feedback."""
        # Arrange
        feedback_data = {
            "model_name": "component_failure",
            "prediction_id": "pred-789",
            "device_id": "wh-789",
            "feedback_type": "false_positive",
            "details": {"issue": "no failure observed"},
        }

        # Act
        feedback_id = self.feedback_service.record_feedback(**feedback_data)

        # Assert
        assert feedback_id is not None and isinstance(feedback_id, str)
        self.db_mock.execute.assert_called_once()

    def test_get_feedback_for_model(self):
        """Test retrieving feedback for a specific model."""
        # Arrange
        model_name = "component_failure"
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 5)

        # Mock the database response
        self.db_mock.execute.return_value = self.mock_feedback_data

        # Act
        result = self.feedback_service.get_feedback_for_model(
            model_name=model_name, start_date=start_date, end_date=end_date
        )

        # Assert
        assert len(result) == 2
        assert all(item["model_name"] == model_name for item in result)
        self.db_mock.execute.assert_called_once()

    def test_get_feedback_summary(self):
        """Test getting a summary of feedback for a model."""
        # Arrange
        model_name = "component_failure"
        days = 30

        # Mock summary data
        summary_data = {
            "total_count": 10,
            "false_positives": 2,
            "false_negatives": 1,
            "correct_count": 7,
        }

        # Mock the database response
        self.db_mock.execute.return_value = [summary_data]

        # Act
        result = self.feedback_service.get_feedback_summary(
            model_name=model_name, days=days
        )

        # Assert
        assert result["total_count"] == 10
        assert result["false_positive_rate"] == 0.2  # 2/10
        assert result["false_negative_rate"] == 0.1  # 1/10
        assert result["accuracy"] == 0.7  # 7/10
        self.db_mock.execute.assert_called_once()

    def test_get_feedback_summary_empty(self):
        """Test getting a summary when no feedback exists."""
        # Arrange
        model_name = "unused_model"
        days = 30

        # Mock empty database response
        self.db_mock.execute.return_value = []

        # Act
        result = self.feedback_service.get_feedback_summary(
            model_name=model_name, days=days
        )

        # Assert
        assert result["total_count"] == 0
        assert result["false_positive_rate"] == 0
        assert result["false_negative_rate"] == 0
        assert result["accuracy"] == 0
        self.db_mock.execute.assert_called_once()

    def test_analyze_feedback_patterns(self):
        """Test analyzing patterns in feedback data."""
        # Arrange
        model_name = "component_failure"
        days = 90

        # Create mock feedback with patterns
        pattern_data = [
            # Device wh-123 has multiple errors with the same issue
            {
                "feedback_id": "fb-1",
                "model_name": "component_failure",
                "device_id": "wh-123",
                "feedback_type": "false_positive",
                "details": {"issue": "no actual failure observed"},
            },
            {
                "feedback_id": "fb-2",
                "model_name": "component_failure",
                "device_id": "wh-123",
                "feedback_type": "false_positive",
                "details": {"issue": "no actual failure observed"},
            },
            {
                "feedback_id": "fb-3",
                "model_name": "component_failure",
                "device_id": "wh-123",
                "feedback_type": "false_negative",
                "details": {"issue": "failure occurred but wasn't predicted"},
            },
            # Add more records for wh-123 to meet the minimum count of 5
            {
                "feedback_id": "fb-3a",
                "model_name": "component_failure",
                "device_id": "wh-123",
                "feedback_type": "false_positive",
                "details": {"issue": "no actual failure observed"},
            },
            {
                "feedback_id": "fb-3b",
                "model_name": "component_failure",
                "device_id": "wh-123",
                "feedback_type": "false_negative",
                "details": {"issue": "failure occurred but wasn't predicted"},
            },
            # Device wh-456 has perfect predictions
            {
                "feedback_id": "fb-4",
                "model_name": "component_failure",
                "device_id": "wh-456",
                "feedback_type": "correct",
                "details": {"comment": "perfect prediction"},
            },
            {
                "feedback_id": "fb-5",
                "model_name": "component_failure",
                "device_id": "wh-456",
                "feedback_type": "correct",
                "details": {"comment": "accurate prediction"},
            },
        ]

        # Set up the mock to return our pattern data
        self.feedback_service.get_feedback_for_model = MagicMock(
            return_value=pattern_data
        )

        # Act
        result = self.feedback_service.analyze_feedback_patterns(
            model_name=model_name, days=days
        )

        # Assert
        assert "error_patterns" in result
        assert "device_patterns" in result

        # Device wh-123 should be identified as problematic (5 records with 4 errors = 80% error rate)
        assert len(result["device_patterns"]) >= 1
        device_pattern = result["device_patterns"][0]
        assert device_pattern["device_id"] == "wh-123"
        assert device_pattern["error_rate"] > 0.5

        # "no actual failure observed" should be identified as common issue (3 occurrences)
        assert len(result["error_patterns"]) >= 1
        error_pattern = result["error_patterns"][0]
        assert error_pattern["issue"] == "no actual failure observed"
        assert error_pattern["count"] >= 3
