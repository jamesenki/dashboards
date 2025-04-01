from src.models.model_monitoring import ModelMetadata
from src.repository.model_repository import ModelRepository
from typing import List, Optional

class ModelMonitoringService:
    def __init__(self, model_repository: ModelRepository):
        self.model_repository = model_repository
    
    def get_models(self, include_archived=False):
        """Get all models with their metadata"""
        models = self.model_repository.get_models(include_archived=include_archived)

        # Enrich with monitoring status and ensure metrics have default values
        for model in models:
            model_id = model.id
            monitoring_enabled = self.model_repository.is_monitoring_enabled(model_id)
            model.monitoring_enabled = monitoring_enabled
            
            # Set default values for metrics if they're missing or N/A
            if not hasattr(model, 'accuracy') or model.accuracy is None or model.accuracy == 'N/A':
                model.accuracy = 0.0
            
            if not hasattr(model, 'drift_score') or model.drift_score is None or model.drift_score == 'N/A':
                model.drift_score = 0.0
                
            # Set health status based on metrics
            if hasattr(model, 'health') and (model.health is None or model.health == 'Unknown'):
                if model.accuracy > 0 or model.drift_score > 0:
                    model.health = 'Good' if model.accuracy > 0.7 and model.drift_score < 0.3 else 'Poor'
                else:
                    model.health = 'Unknown'

        return models

    def toggle_monitoring(self, model_id: str) -> bool:
        """Toggle monitoring for a model"""
        return self.model_repository.toggle_monitoring(model_id)

    def archive_model(self, model_id: str) -> bool:
        """Archive a model"""
        return self.model_repository.archive_model(model_id)

    def unarchive_model(self, model_id: str) -> bool:
        """Unarchive a model"""
        return self.model_repository.unarchive_model(model_id)
