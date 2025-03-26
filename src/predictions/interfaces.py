"""
Core interfaces and base classes for the prediction system.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Union, TypeVar

from pydantic import BaseModel, Field

class ActionSeverity(str, Enum):
    """Severity levels for recommended actions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendedAction(BaseModel):
    """
    A recommended action based on a prediction result.
    
    Attributes:
        action_id: Unique identifier for this action
        description: Human-readable description of the action
        severity: Severity level of the action
        impact: Description of the impact if action is not taken
        expected_benefit: Expected benefit of taking the action
        due_date: Optional date by which the action should be completed
        estimated_cost: Optional estimated cost of the action
        estimated_duration: Optional estimated time to complete the action
    """
    action_id: str
    description: str
    severity: ActionSeverity
    impact: str
    expected_benefit: str
    due_date: Optional[datetime] = None
    estimated_cost: Optional[float] = None
    estimated_duration: Optional[str] = None


class PredictionResult(BaseModel):
    """
    Result of a prediction operation.
    
    Attributes:
        prediction_type: Type of prediction (e.g., "component_failure")
        device_id: ID of the device for which prediction was made
        predicted_value: The predicted value (interpretation depends on prediction_type)
        confidence: Confidence level of the prediction (0-1)
        features_used: List of feature names used for the prediction
        timestamp: When the prediction was made
        recommended_actions: List of recommended actions based on the prediction
        raw_details: Optional dictionary with model-specific raw prediction details
    """
    prediction_type: str
    device_id: str
    predicted_value: float
    confidence: float
    features_used: List[str]
    timestamp: datetime
    recommended_actions: List[RecommendedAction]
    raw_details: Optional[Dict[str, Any]] = None


class IPredictionModel(ABC):
    """
    Interface for all prediction models.
    
    All prediction models must implement these methods to be compatible
    with the prediction system.
    """
    
    @abstractmethod
    async def predict(self, device_id: str, features: Dict[str, Any]) -> PredictionResult:
        """
        Generate a prediction for the given device using the provided features.
        
        Args:
            device_id: Identifier for the device
            features: Dictionary of features to use for prediction
            
        Returns:
            PredictionResult: The prediction result
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Return information about the model.
        
        Returns:
            Dict containing model metadata including name, version, 
            required features, and performance metrics
        """
        pass


class IActionRecommender(ABC):
    """
    Interface for action recommenders.
    
    Action recommenders generate recommended actions based on prediction results.
    """
    
    @abstractmethod
    async def recommend_actions(self, prediction_result: PredictionResult) -> List[RecommendedAction]:
        """
        Generate recommended actions based on a prediction result.
        
        Args:
            prediction_result: The prediction result to analyze
            
        Returns:
            List of recommended actions
        """
        pass


class ModelRegistry:
    """
    Registry for prediction models.
    
    Maintains a catalog of available prediction models and their metadata.
    """
    
    def __init__(self):
        self._models: Dict[str, Dict[str, IPredictionModel]] = {}
    
    def register_model(self, prediction_type: str, model_version: str, model: IPredictionModel) -> None:
        """
        Register a prediction model.
        
        Args:
            prediction_type: Type of prediction the model performs
            model_version: Version string for the model
            model: The model instance
        """
        if prediction_type not in self._models:
            self._models[prediction_type] = {}
        
        self._models[prediction_type][model_version] = model
    
    def get_model(self, prediction_type: str, model_version: Optional[str] = None) -> IPredictionModel:
        """
        Get a prediction model by type and optionally version.
        
        Args:
            prediction_type: Type of prediction
            model_version: Optional version string. If None, returns the latest version.
            
        Returns:
            The prediction model
            
        Raises:
            ValueError: If no model is found for the given type/version
        """
        if prediction_type not in self._models:
            raise ValueError(f"No models registered for prediction type: {prediction_type}")
        
        models = self._models[prediction_type]
        
        if not models:
            raise ValueError(f"No models available for prediction type: {prediction_type}")
        
        if model_version is not None:
            if model_version not in models:
                raise ValueError(f"Model version {model_version} not found for prediction type: {prediction_type}")
            return models[model_version]
        
        # Return latest version if none specified
        latest_version = sorted(models.keys())[-1]
        return models[latest_version]
    
    def list_models(self) -> Dict[str, List[str]]:
        """
        List all registered prediction types and their available versions.
        
        Returns:
            Dictionary mapping prediction types to lists of available versions
        """
        return {
            pred_type: list(versions.keys())
            for pred_type, versions in self._models.items()
        }


class ActionRegistry:
    """
    Registry for action recommenders.
    
    Maintains a catalog of available action recommenders for different prediction types.
    """
    
    def __init__(self):
        self._recommenders: Dict[str, IActionRecommender] = {}
    
    def register_recommender(self, prediction_type: str, recommender: IActionRecommender) -> None:
        """
        Register an action recommender for a prediction type.
        
        Args:
            prediction_type: Type of prediction the recommender handles
            recommender: The recommender instance
        """
        self._recommenders[prediction_type] = recommender
    
    def get_recommender(self, prediction_type: str) -> IActionRecommender:
        """
        Get an action recommender for a prediction type.
        
        Args:
            prediction_type: Type of prediction
            
        Returns:
            The action recommender
            
        Raises:
            ValueError: If no recommender is found for the given prediction type
        """
        if prediction_type not in self._recommenders:
            raise ValueError(f"No action recommender registered for prediction type: {prediction_type}")
        
        return self._recommenders[prediction_type]


class PredictionService:
    """
    Service for generating predictions and recommendations.
    
    Coordinates the prediction process using registered models and recommenders.
    """
    
    def __init__(self, model_registry: ModelRegistry, action_registry: ActionRegistry):
        self.model_registry = model_registry
        self.action_registry = action_registry
    
    async def generate_prediction(
        self, 
        prediction_type: str, 
        device_id: str, 
        features: Dict[str, Any],
        model_version: Optional[str] = None
    ) -> PredictionResult:
        """
        Generate a prediction for a device.
        
        Args:
            prediction_type: Type of prediction to generate
            device_id: ID of the device
            features: Features to use for prediction
            model_version: Optional specific model version to use
            
        Returns:
            The prediction result with recommended actions
        """
        # Get the appropriate model
        model = self.model_registry.get_model(prediction_type, model_version)
        
        # Generate the prediction
        prediction = await model.predict(device_id, features)
        
        # Get the appropriate action recommender and generate recommendations
        try:
            recommender = self.action_registry.get_recommender(prediction_type)
            actions = await recommender.recommend_actions(prediction)
            
            # Update the prediction with the recommended actions
            prediction.recommended_actions = actions
        except ValueError:
            # No recommender for this prediction type, keep the default actions
            pass
        
        return prediction
