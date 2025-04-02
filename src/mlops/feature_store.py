"""
FeatureStore for managing ML model training data.

This module provides functionality for storing, retrieving, and
transforming features for machine learning models.
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FeatureStore:
    """
    Feature store for managing ML model training data.

    Handles storage, retrieval, and transformation of features for ML models.
    """

    def __init__(self, db):
        """
        Initialize the feature store.

        Args:
            db: Database connection for executing SQL queries
        """
        self.db = db
        logger.info("FeatureStore initialized")

    def register_feature(
        self,
        device_id: str,
        feature_name: str,
        feature_value: float,
        timestamp: datetime,
    ) -> bool:
        """
        Register a new feature value in the store.

        Args:
            device_id: ID of the device
            feature_name: Name of the feature
            feature_value: Value of the feature
            timestamp: Timestamp of the feature value

        Returns:
            Success flag
        """
        try:
            query = """
                INSERT INTO feature_data
                (device_id, feature_name, feature_value, timestamp, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """

            self.db.execute(
                query,
                (
                    device_id,
                    feature_name,
                    float(feature_value),
                    timestamp,
                    datetime.now(),
                ),
            )

            logger.debug(
                f"Registered feature {feature_name}={feature_value} for device {device_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to register feature: {e}")
            return False

    def get_feature_values(
        self,
        device_id: str,
        feature_names: List[str] = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> Dict[str, Any]:
        """
        Get feature values for a device within a date range.

        Args:
            device_id: ID of the device
            feature_names: Optional list of specific features to retrieve
            start_date: Optional start date for filtering data
            end_date: Optional end date for filtering data

        Returns:
            Dictionary of feature values by feature name
        """
        try:
            params = [device_id]
            query = """
                SELECT feature_name, feature_value
                FROM feature_data
                WHERE device_id = %s
            """

            if feature_names:
                placeholders = ", ".join(["%s"] * len(feature_names))
                query += f" AND feature_name IN ({placeholders})"
                params.extend(feature_names)

            if start_date:
                query += " AND timestamp >= %s"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= %s"
                params.append(end_date)

            # Get latest values by timestamp
            query += " ORDER BY timestamp DESC"

            results = self.db.execute(query, tuple(params))

            # Convert to dictionary with feature name as key
            features = {}
            for feature_name, feature_value in results:
                if feature_name not in features:  # Only take the most recent value
                    features[feature_name] = feature_value

            return features

        except Exception as e:
            logger.error(f"Failed to get features for device {device_id}: {e}")
            return {}

    def get_training_dataset(
        self,
        feature_names: List[str] = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> List[Dict[str, Any]]:
        """
        Get a dataset suitable for training ML models.

        Args:
            feature_names: List of features to include in the dataset
            start_date: Optional start date for filtering data
            end_date: Optional end date for filtering data

        Returns:
            List of dictionaries containing feature values for training
        """
        try:
            params = []
            query = """
                SELECT DISTINCT ON (device_id, feature_name)
                device_id, feature_name, feature_value, timestamp
                FROM feature_data
            """

            conditions = []

            if feature_names:
                placeholders = ", ".join(["%s"] * len(feature_names))
                conditions.append(f"feature_name IN ({placeholders})")
                params.extend(feature_names)

            if start_date:
                conditions.append("timestamp >= %s")
                params.append(start_date)

            if end_date:
                conditions.append("timestamp <= %s")
                params.append(end_date)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            # Order to get latest values
            query += " ORDER BY device_id, feature_name, timestamp DESC"

            results = self.db.execute(query, tuple(params) if params else None)

            # Group by device_id
            devices = {}
            for device_id, feature_name, feature_value, timestamp in results:
                if device_id not in devices:
                    devices[device_id] = {"device_id": device_id}
                devices[device_id][feature_name] = feature_value

            dataset = list(devices.values())
            logger.info(f"Retrieved training dataset with {len(dataset)} samples")
            return dataset

        except Exception as e:
            logger.error(f"Failed to get training dataset: {e}")
            return []

    def register_feature_transformer(
        self, feature_name: str, transformer_type: str, transformer_path: str
    ) -> bool:
        """
        Register a feature transformer.

        Args:
            feature_name: Name of the feature
            transformer_type: Type of the transformer (e.g., StandardScaler)
            transformer_path: Path to the saved transformer

        Returns:
            Success flag
        """
        try:
            query = """
                INSERT INTO feature_transformers
                (feature_name, transformer_type, transformer_path, created_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (feature_name) DO UPDATE
                SET transformer_type = EXCLUDED.transformer_type,
                    transformer_path = EXCLUDED.transformer_path,
                    updated_at = %s
            """

            now = datetime.now()
            self.db.execute(
                query, (feature_name, transformer_type, transformer_path, now, now)
            )

            logger.info(
                f"Registered {transformer_type} transformer for feature {feature_name}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to register feature transformer: {e}")
            return False

    def get_feature_transformer(self, feature_name: str) -> Dict[str, Any]:
        """
        Get a feature transformer.

        Args:
            feature_name: Name of the feature

        Returns:
            Dictionary with transformer information
        """
        try:
            query = """
                SELECT transformer_type, transformer_path
                FROM feature_transformers
                WHERE feature_name = %s
            """

            result = self.db.execute(query, (feature_name,))

            if result and len(result) > 0:
                transformer_type, transformer_path = result[0]
                return {
                    "feature_name": feature_name,
                    "transformer_type": transformer_type,
                    "transformer_path": transformer_path,
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get transformer for feature {feature_name}: {e}")
            return None
