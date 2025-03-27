"""
Feedback Service for model prediction feedback processing.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import uuid
import json

logger = logging.getLogger(__name__)


class FeedbackService:
    """
    Service for collecting and analyzing feedback on model predictions.
    
    The FeedbackService is responsible for:
    1. Recording user feedback on model predictions
    2. Tracking false positives, false negatives, and other error types
    3. Providing feedback summaries for model performance analysis
    4. Supporting continuous model improvement
    """
    
    def __init__(self, db, model_registry):
        """
        Initialize the feedback service
        
        Args:
            db: Database connection for persistence
            model_registry: Model registry for referencing models
        """
        self.db = db
        self.model_registry = model_registry
    
    def record_feedback(self, 
                       model_name: str,
                       prediction_id: str,
                       device_id: str,
                       feedback_type: str,
                       details: Dict[str, Any] = None) -> str:
        """
        Record feedback for a model prediction
        
        Args:
            model_name: Name of the model that made the prediction
            prediction_id: ID of the prediction
            device_id: ID of the device the prediction was made for
            feedback_type: Type of feedback (e.g., "false_positive", "false_negative", "correct")
            details: Additional details about the feedback
            
        Returns:
            Feedback ID
        """
        feedback_id = str(uuid.uuid4())
        created_at = datetime.now()
        
        # Serialize the details dictionary if provided
        details_json = json.dumps(details) if details else None
        
        query = """
            INSERT INTO model_feedback
            (feedback_id, model_name, prediction_id, device_id, feedback_type, details, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        params = [
            feedback_id,
            model_name,
            prediction_id,
            device_id,
            feedback_type,
            details_json,
            created_at
        ]
        
        self.db.execute(query, params)
        logger.info(f"Recorded feedback {feedback_id} for prediction {prediction_id}")
        
        return feedback_id
    
    def get_feedback_for_model(self, 
                              model_name: str,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              feedback_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get feedback for a specific model
        
        Args:
            model_name: Name of the model
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            feedback_type: Optional feedback type for filtering
            
        Returns:
            List of feedback records
        """
        query = """
            SELECT * 
            FROM model_feedback
            WHERE model_name = %s
        """
        
        params = [model_name]
        
        if start_date:
            query += " AND created_at >= %s"
            params.append(start_date)
            
        if end_date:
            query += " AND created_at <= %s"
            params.append(end_date)
            
        if feedback_type:
            query += " AND feedback_type = %s"
            params.append(feedback_type)
            
        query += " ORDER BY created_at DESC"
        
        feedback_records = self.db.execute(query, params)
        
        # Process any JSON fields
        for record in feedback_records:
            if 'details' in record and record['details']:
                try:
                    record['details'] = json.loads(record['details'])
                except:
                    pass
                    
        return feedback_records
    
    def get_feedback_summary(self, 
                            model_name: str, 
                            days: int = 30) -> Dict[str, Any]:
        """
        Get a summary of feedback for a model
        
        Args:
            model_name: Name of the model
            days: Number of days to include in the summary
            
        Returns:
            Dictionary with feedback metrics
        """
        start_date = datetime.now() - timedelta(days=days)
        
        query = """
            SELECT 
                COUNT(*) as total_count,
                SUM(CASE WHEN feedback_type = 'false_positive' THEN 1 ELSE 0 END) as false_positives,
                SUM(CASE WHEN feedback_type = 'false_negative' THEN 1 ELSE 0 END) as false_negatives,
                SUM(CASE WHEN feedback_type = 'correct' THEN 1 ELSE 0 END) as correct_count
            FROM model_feedback
            WHERE model_name = %s
            AND created_at >= %s
        """
        
        params = [model_name, start_date]
        
        result = self.db.execute(query, params)
        summary = result[0] if result else {
            "total_count": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "correct_count": 0
        }
        
        # Calculate error rates if we have data
        if summary["total_count"] > 0:
            summary["false_positive_rate"] = summary["false_positives"] / summary["total_count"]
            summary["false_negative_rate"] = summary["false_negatives"] / summary["total_count"]
            summary["accuracy"] = summary["correct_count"] / summary["total_count"]
        else:
            summary["false_positive_rate"] = 0
            summary["false_negative_rate"] = 0
            summary["accuracy"] = 0
            
        return summary
    
    def analyze_feedback_patterns(self, 
                                model_name: str,
                                days: int = 90) -> Dict[str, Any]:
        """
        Analyze patterns in feedback data
        
        Args:
            model_name: Name of the model
            days: Number of days to include in the analysis
            
        Returns:
            Dictionary with analysis results
        """
        feedback = self.get_feedback_for_model(
            model_name=model_name,
            start_date=datetime.now() - timedelta(days=days)
        )
        
        if not feedback:
            return {"error_patterns": [], "device_patterns": []}
            
        # Group feedback by devices to find problematic devices
        device_feedback = {}
        for item in feedback:
            device_id = item.get("device_id")
            if device_id not in device_feedback:
                device_feedback[device_id] = {"total": 0, "errors": 0}
            
            device_feedback[device_id]["total"] += 1
            if item.get("feedback_type") in ["false_positive", "false_negative"]:
                device_feedback[device_id]["errors"] += 1
        
        # Find devices with high error rates
        problem_devices = []
        for device_id, stats in device_feedback.items():
            if stats["total"] >= 5 and stats["errors"] / stats["total"] > 0.5:
                problem_devices.append({
                    "device_id": device_id,
                    "error_rate": stats["errors"] / stats["total"],
                    "feedback_count": stats["total"]
                })
        
        # Group by error types to find common issues
        error_types = {}
        for item in feedback:
            if item.get("feedback_type") in ["false_positive", "false_negative"]:
                details = item.get("details", {})
                issue = details.get("issue", "unknown")
                
                if issue not in error_types:
                    error_types[issue] = 0
                error_types[issue] += 1
        
        # Find most common error types
        common_errors = [
            {"issue": issue, "count": count}
            for issue, count in error_types.items()
            if count >= 3
        ]
        
        return {
            "error_patterns": sorted(common_errors, key=lambda x: x["count"], reverse=True),
            "device_patterns": sorted(problem_devices, key=lambda x: x["error_rate"], reverse=True)
        }