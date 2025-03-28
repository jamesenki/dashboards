"""
Prediction service for ML models.
"""
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
import joblib
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PredictionService:
    """
    Service for making predictions using ML models from the model registry.
    
    The PredictionService is responsible for:
    1. Loading models from the model registry
    2. Preprocessing input data for prediction
    3. Making predictions using the models
    4. Optionally recording feedback on predictions
    5. Providing explanations for model predictions
    """
    
    def __init__(self, db, model_registry, feature_store, feedback_service=None):
        """
        Initialize the prediction service
        
        Args:
            db: Database connection
            model_registry: ModelRegistry instance for accessing models
            feature_store: FeatureStore instance for feature transformations
            feedback_service: Optional FeedbackService for recording feedback
        """
        self.db = db
        self.model_registry = model_registry
        self.feature_store = feature_store
        self.feedback_service = feedback_service
        
        # Cache for loaded models to avoid reloading the same model
        self._model_cache = {}
    
    def predict(self, model_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a prediction using the active version of a model
        
        Args:
            model_name: Name of the model to use
            input_data: Input data for prediction
            
        Returns:
            Prediction results
        """
        # Get the active model info from the registry
        model_info = self.model_registry.get_active_model(model_name)
        
        if not model_info:
            raise ValueError(f"No active model found for {model_name}")
        
        # Get model version
        model_version = model_info.get("model_version")
        
        # Load the model
        model = self._load_model(model_info.get("model_path"))
        
        # Preprocess the input data
        features = self._preprocess_input(input_data, model_info)
        
        # Make prediction
        prediction_value = model.predict(features)[0]
        
        # Get prediction probability if the model supports it
        probability = None
        if hasattr(model, 'predict_proba'):
            try:
                # For binary classification, get probability of the positive class (1)
                probability = model.predict_proba(features)[0][1]
            except:
                logger.warning(f"Could not get prediction probability for model {model_name}")
        
        # Create prediction record
        prediction_id = self._record_prediction(
            model_name=model_name,
            model_version=model_version,
            input_data=input_data,
            prediction=prediction_value,
            probability=probability
        )
        
        # Create response
        result = {
            "prediction_id": prediction_id,
            "model_name": model_name,
            "model_version": model_version,
            "prediction": int(prediction_value),
            "timestamp": datetime.now().isoformat(),
            "device_id": input_data.get("device_id")
        }
        
        if probability is not None:
            result["probability"] = float(probability)
        
        return result
    
    def batch_predict(self, model_name: str, batch_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Make predictions for a batch of inputs
        
        Args:
            model_name: Name of the model to use
            batch_data: List of input data for predictions
            
        Returns:
            List of prediction results
        """
        # Get the active model info from the registry
        model_info = self.model_registry.get_active_model(model_name)
        
        if not model_info:
            raise ValueError(f"No active model found for {model_name}")
        
        # Get model version
        model_version = model_info.get("model_version")
        
        # Load the model
        model = self._load_model(model_info.get("model_path"))
        
        # Process each item in the batch
        results = []
        
        # Prepare all features as a single batch for efficient prediction
        all_features = pd.DataFrame([
            self._extract_features(item, model_info) for item in batch_data
        ])
        
        # Make batch predictions
        predictions = model.predict(all_features)
        
        # Get prediction probabilities if the model supports it
        probabilities = None
        if hasattr(model, 'predict_proba'):
            try:
                # For binary classification, get probability of the positive class (1)
                probabilities = model.predict_proba(all_features)[:, 1]
            except:
                logger.warning(f"Could not get prediction probabilities for model {model_name}")
        
        # Create prediction results
        for i, item in enumerate(batch_data):
            prediction_value = predictions[i]
            
            # Create prediction record
            prediction_id = self._record_prediction(
                model_name=model_name,
                model_version=model_version,
                input_data=item,
                prediction=prediction_value,
                probability=probabilities[i] if probabilities is not None else None
            )
            
            # Create response
            result = {
                "prediction_id": prediction_id,
                "model_name": model_name,
                "model_version": model_version,
                "prediction": int(prediction_value),
                "timestamp": datetime.now().isoformat(),
                "device_id": item.get("device_id")
            }
            
            if probabilities is not None:
                result["probability"] = float(probabilities[i])
            
            results.append(result)
        
        return results
    
    def predict_with_feedback(self, 
                             model_name: str, 
                             input_data: Dict[str, Any],
                             actual_outcome: int,
                             feedback_type: str,
                             details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make a prediction and record feedback on the prediction
        
        Args:
            model_name: Name of the model to use
            input_data: Input data for prediction
            actual_outcome: Actual outcome (ground truth)
            feedback_type: Type of feedback (e.g., "correct", "false_positive", "false_negative")
            details: Additional details about the feedback
            
        Returns:
            Prediction results
        """
        # First make the prediction
        prediction = self.predict(model_name, input_data)
        
        # If feedback service is available, record feedback
        if self.feedback_service:
            if not details:
                details = {}
                
            # Add actual outcome to details
            details["actual_outcome"] = actual_outcome
            details["predicted_outcome"] = prediction["prediction"]
            if "probability" in prediction:
                details["predicted_probability"] = prediction["probability"]
            
            # Record feedback
            self.feedback_service.record_feedback(
                model_name=model_name,
                prediction_id=prediction["prediction_id"],
                device_id=input_data.get("device_id"),
                feedback_type=feedback_type,
                details=details
            )
        
        return prediction
    
    def predict_with_version(self, 
                            model_name: str, 
                            model_version: str,
                            input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a prediction using a specific model version
        
        Args:
            model_name: Name of the model to use
            model_version: Specific version of the model to use
            input_data: Input data for prediction
            
        Returns:
            Prediction results
        """
        # Get the specific model version info from the registry
        model_info = self.model_registry.get_model_info(
            model_name=model_name,
            model_version=model_version
        )
        
        if not model_info:
            raise ValueError(f"Model version {model_version} not found for {model_name}")
        
        # Load the model
        model = self._load_model(model_info.get("model_path"))
        
        # Preprocess the input data
        features = self._preprocess_input(input_data, model_info)
        
        # Make prediction
        prediction_value = model.predict(features)[0]
        
        # Get prediction probability if the model supports it
        probability = None
        if hasattr(model, 'predict_proba'):
            try:
                # For binary classification, get probability of the positive class (1)
                probability = model.predict_proba(features)[0][1]
            except:
                logger.warning(f"Could not get prediction probability for model {model_name}")
        
        # Create prediction record
        prediction_id = self._record_prediction(
            model_name=model_name,
            model_version=model_version,
            input_data=input_data,
            prediction=prediction_value,
            probability=probability
        )
        
        # Create response
        result = {
            "prediction_id": prediction_id,
            "model_name": model_name,
            "model_version": model_version,
            "prediction": int(prediction_value),
            "timestamp": datetime.now().isoformat(),
            "device_id": input_data.get("device_id")
        }
        
        if probability is not None:
            result["probability"] = float(probability)
        
        return result
    
    def get_prediction_explanation(self, 
                               model_name: str,
                               input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get an explanation for a prediction
        
        Args:
            model_name: Name of the model to use
            input_data: Input data for prediction
            
        Returns:
            Explanation of the prediction
        """
        # Get the active model info from the registry
        model_info = self.model_registry.get_active_model(model_name)
        
        if not model_info:
            raise ValueError(f"No active model found for {model_name}")
        
        # Load the model
        model = self._load_model(model_info.get("model_path"))
        
        # Preprocess the input data
        features = self._preprocess_input(input_data, model_info)
        
        # Check if model has an explainer
        if not hasattr(model, 'explainer'):
            logger.warning(f"Model {model_name} does not have an explainer")
            return {"error": "Model does not support explanations"}
        
        # Get feature names
        feature_names = self._get_feature_names(model_info)
        
        # Get SHAP values
        try:
            shap_values = model.explainer.shap_values(features)
            
            # For binary classification, get SHAP values for the positive class
            if isinstance(shap_values, list) and len(shap_values) > 1:
                shap_values = shap_values[1]
                
            # Convert to a flat array
            if len(shap_values.shape) > 1:
                shap_values = shap_values[0]
                
            # Create a dictionary of feature importance
            feature_importance = {}
            for i, feature in enumerate(feature_names):
                feature_importance[feature] = float(shap_values[i])
                
            # Sort features by absolute importance
            sorted_features = sorted(
                feature_importance.items(), 
                key=lambda x: abs(x[1]), 
                reverse=True
            )
            
            top_features = [
                {"feature": feature, "importance": importance}
                for feature, importance in sorted_features
            ]
            
            return {
                "feature_importance": feature_importance,
                "top_features": top_features
            }
        except Exception as e:
            logger.error(f"Error getting prediction explanation: {e}")
            return {"error": f"Could not generate explanation: {str(e)}"}
    
    def _load_model(self, model_path: str):
        """
        Load a model from file path with caching
        
        Args:
            model_path: Path to the model file
            
        Returns:
            Loaded model
        """
        # Check if model is already in cache
        if model_path in self._model_cache:
            return self._model_cache[model_path]
        
        # Load model securely
        try:
            from security.secure_model_loader import SecureModelLoader
            
            # Configure the secure loader
            secure_loader = SecureModelLoader(
                # Define trusted model sources - adjust to your environment
                allowed_sources=[os.path.dirname(model_path)],
                # Enable signature verification when in production
                signature_verification=False,  # Set to True in production
                # Enable sandbox in production for critical models
                use_sandbox=False  # Set to True for stronger isolation
            )
            
            # Load the model securely
            model = secure_loader.load(model_path)
            
            # Cache the model
            self._model_cache[model_path] = model
            
            return model
        except Exception as e:
            logger.error(f"Error loading model from {model_path}: {e}")
            raise
    
    def _preprocess_input(self, input_data: Dict[str, Any], model_info: Dict[str, Any]) -> pd.DataFrame:
        """
        Preprocess input data for prediction
        
        Args:
            input_data: Raw input data
            model_info: Model information
            
        Returns:
            Processed features
        """
        # Extract features
        features = self._extract_features(input_data, model_info)
        
        # Convert to DataFrame
        features_df = pd.DataFrame([features])
        
        return features_df
    
    def _extract_features(self, input_data: Dict[str, Any], model_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features from input data
        
        Args:
            input_data: Raw input data
            model_info: Model information
            
        Returns:
            Extracted features
        """
        # Get required features from model metadata
        required_features = []
        
        if isinstance(model_info.get("metadata"), dict):
            required_features = model_info.get("metadata", {}).get("features", [])
        elif isinstance(model_info.get("metadata"), str):
            import json
            try:
                metadata = json.loads(model_info.get("metadata", "{}"))
                required_features = metadata.get("features", [])
            except:
                pass
        
        # Extract only the required features
        features = {}
        for feature in required_features:
            if feature in input_data:
                features[feature] = input_data[feature]
        
        return features
    
    def _get_feature_names(self, model_info: Dict[str, Any]) -> List[str]:
        """
        Get feature names from model metadata
        
        Args:
            model_info: Model information
            
        Returns:
            List of feature names
        """
        if isinstance(model_info.get("metadata"), dict):
            return model_info.get("metadata", {}).get("features", [])
        elif isinstance(model_info.get("metadata"), str):
            import json
            try:
                metadata = json.loads(model_info.get("metadata", "{}"))
                return metadata.get("features", [])
            except:
                pass
        
        return []
    
    def _record_prediction(self, 
                          model_name: str,
                          model_version: str,
                          input_data: Dict[str, Any],
                          prediction: Any,
                          probability: float = None) -> str:
        """
        Record prediction in the database
        
        Args:
            model_name: Name of the model used
            model_version: Version of the model used
            input_data: Input data for prediction
            prediction: Prediction result
            probability: Prediction probability (if available)
            
        Returns:
            Prediction ID
        """
        import uuid
        import json
        from datetime import datetime
        
        prediction_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Convert input data to JSON
        input_json = json.dumps(input_data)
        
        # Execute database query
        query = """
            INSERT INTO model_predictions 
            (prediction_id, model_name, model_version, input_data, prediction, probability, device_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = [
            prediction_id,
            model_name,
            model_version,
            input_json,
            prediction,
            probability,
            input_data.get("device_id"),
            timestamp
        ]
        
        try:
            self.db.execute(query, params)
        except Exception as e:
            logger.error(f"Error recording prediction: {e}")
            # Don't fail the prediction if recording fails
        
        return prediction_id