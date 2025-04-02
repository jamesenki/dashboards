"""
Tests for the Vending Machine Maintenance Prediction ML model.
Following TDD approach, this file contains tests that define expected model behavior.
"""
import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

# Model is now implemented, let's import it
from src.ml.models.maintenance_prediction import (
    MaintenancePrediction,
    MaintenancePredictionModel,
)


@pytest.fixture
def sample_test_data():
    """
    Fixture providing sample test data for maintenance prediction tests.
    This synthetic data mimics vending machine sensor readings and maintenance history.
    """
    # Create a dataframe with 1000 synthetic readings
    np.random.seed(42)  # For reproducibility

    # Create timestamps for the past 100 days, 10 readings per day
    base_date = datetime.now() - timedelta(days=100)
    timestamps = [base_date + timedelta(hours=i * 2.4) for i in range(1000)]

    # Generate synthetic sensor data that would lead to maintenance needs
    data = {
        "timestamp": timestamps,
        "temperature": np.random.normal(5, 2, 1000),  # Temperature in Celsius
        "door_open_count": np.random.poisson(15, 1000),  # Number of door openings
        "power_consumption": np.random.normal(100, 15, 1000),  # Power in watts
        "vibration_level": np.random.normal(0.5, 0.2, 1000),  # Vibration sensor reading
        "compressor_runtime": np.random.normal(120, 30, 1000),  # Minutes per day
        "sales_count": np.random.poisson(40, 1000),  # Sales per day
    }

    # Ensure we have a good mix of maintenance events for testing
    # First, explicitly create some maintenance events (at least 100)
    maintenance_needed = [0] * 1000

    # Force about 20% of records to be maintenance events
    maintenance_indices = np.random.choice(1000, 200, replace=False)

    # Create more realistic pattern: maintenance events often cluster
    # (e.g., a machine having problems will likely need multiple services)
    for i in range(0, 180, 20):
        # Create clusters of maintenance events
        maintenance_needed[i : i + 5] = [1, 1, 1, 1, 1]

    # Add some individual random maintenance events
    for i in maintenance_indices[:50]:
        maintenance_needed[i] = 1

    # Update some feature values to correlate with maintenance events
    # for realistic patterns
    for i in range(1000):
        if maintenance_needed[i] == 1:
            # Machines needing maintenance tend to show higher temperature
            data["temperature"][i] = max(
                data["temperature"][i], np.random.normal(8, 1.5)
            )
            # Machines needing maintenance tend to have higher vibration
            data["vibration_level"][i] = max(
                data["vibration_level"][i], np.random.normal(0.8, 0.1)
            )
            # Machines needing maintenance tend to have longer compressor runtime
            data["compressor_runtime"][i] = max(
                data["compressor_runtime"][i], np.random.normal(170, 20)
            )

    data["maintenance_needed"] = maintenance_needed

    return pd.DataFrame(data)


def test_model_initialization():
    """
    Test that the MaintenancePredictionModel can be initialized with default parameters.
    """
    model = MaintenancePredictionModel()
    assert hasattr(model, "predict_next_maintenance")
    assert hasattr(model, "train")
    assert model.is_trained is False


def test_model_prediction_format(sample_test_data):
    """
    Test that the model returns predictions in the expected format.
    """
    model = MaintenancePredictionModel()

    # Since we might not have trained the model yet, this will use the mock prediction
    # which is fine for testing the format
    machine_id = "test-vm-123"
    prediction = model.predict_next_maintenance(machine_id)

    # Check prediction format
    assert isinstance(prediction.days_until_maintenance, int)
    assert 0 <= prediction.days_until_maintenance <= 365
    assert prediction.confidence >= 0.0 and prediction.confidence <= 1.0
    assert isinstance(prediction.component_risks, dict)
    assert all(0 <= risk <= 1 for risk in prediction.component_risks.values())


def test_model_training_with_data(sample_test_data):
    """
    Test that the model can be trained with the provided data.
    """
    model = MaintenancePredictionModel()

    # Should not raise any exceptions
    model.train(sample_test_data)

    # Model should be trained after this
    assert model.is_trained

    # Test prediction after training
    machine_id = "VM-001"
    prediction = model.predict_next_maintenance(machine_id, sample_test_data)

    # After training with real data, prediction should be based on the model
    assert isinstance(prediction.days_until_maintenance, int)
    assert hasattr(prediction, "component_risks")


def test_test_data_quality(sample_test_data):
    """
    Test that our test data meets quality requirements.
    This actually tests our test fixture to ensure it provides valid data.
    """
    # Check data shape
    assert sample_test_data.shape[0] >= 100, "Not enough test data samples"
    assert "temperature" in sample_test_data.columns, "Missing temperature column"
    assert "maintenance_needed" in sample_test_data.columns, "Missing target variable"

    # Check data completeness
    assert not sample_test_data.isna().any().any(), "Test data contains missing values"

    # Check data balance - ensure we have both positive and negative examples
    maintenance_counts = sample_test_data["maintenance_needed"].value_counts()
    assert len(maintenance_counts) > 1, "Test data only has one class"
    assert maintenance_counts.min() >= 10, "Not enough examples of minority class"

    # Check feature distributions
    assert (
        0 < sample_test_data["temperature"].mean() < 10
    ), "Temperature values outside expected range"
    assert (
        0 < sample_test_data["power_consumption"].mean() < 200
    ), "Power consumption outside expected range"


def test_data_directory_exists():
    """
    Test that the testdata directory exists and is accessible.
    """
    test_data_dir = os.path.join(os.path.dirname(__file__), "../../../testdata")
    assert os.path.exists(test_data_dir), "testdata directory doesn't exist"
    assert os.path.isdir(test_data_dir), "testdata is not a directory"


if __name__ == "__main__":
    # This will allow running the tests directly with `python test_maintenance_prediction.py`
    pytest.main(["-v", __file__])
