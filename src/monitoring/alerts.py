"""
Alert system for model monitoring.

This module defines alert rules and mechanisms for detecting and
notifying stakeholders about model performance issues.
"""
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    """Severity levels for alerts."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertRule(BaseModel):
    """
    Rule for triggering an alert when a metric crosses a threshold.
    """
    id: Optional[str] = None
    model_id: str
    model_version: str
    rule_name: str
    metric_name: str
    threshold: float
    operator: str  # One of: "<", ">", "<=", ">=", "=="
    severity: AlertSeverity = AlertSeverity.MEDIUM
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    is_active: bool = True
    description: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class AlertEvent(BaseModel):
    """
    Record of an alert that was triggered.
    """
    id: Optional[str] = None
    rule_id: str
    model_id: str
    model_version: str
    metric_name: str
    threshold: float
    actual_value: float
    triggered_at: datetime = Field(default_factory=datetime.now)
    severity: AlertSeverity
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class AlertChecker:
    """
    Utility class for checking if metrics trigger alerts.
    """
    @staticmethod
    def check_threshold(value: float, threshold: float, operator: str) -> bool:
        """
        Check if a value crosses a threshold based on the specified operator.
        
        Args:
            value: The metric value to check
            threshold: The threshold to compare against
            operator: One of "<", ">", "<=", ">=", "=="
            
        Returns:
            True if the threshold is crossed, False otherwise
        """
        if operator == "<":
            return value < threshold
        elif operator == ">":
            return value > threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "==":
            return value == threshold
        else:
            raise ValueError(f"Unsupported operator: {operator}")

    @staticmethod
    def check_metrics_against_rule(metrics: Dict[str, float], rule: AlertRule) -> bool:
        """
        Check if any of the metrics trigger an alert rule.
        
        Args:
            metrics: Dictionary of metric names and values
            rule: The alert rule to check against
            
        Returns:
            True if the rule is triggered, False otherwise
        """
        if rule.metric_name not in metrics:
            return False
            
        return AlertChecker.check_threshold(
            metrics[rule.metric_name], rule.threshold, rule.operator
        )
        
    @staticmethod
    def create_alert_event(rule: AlertRule, metric_value: float) -> AlertEvent:
        """
        Create an alert event for a triggered rule.
        
        Args:
            rule: The rule that was triggered
            metric_value: The metric value that triggered the rule
            
        Returns:
            AlertEvent instance
        """
        return AlertEvent(
            rule_id=rule.id,
            model_id=rule.model_id,
            model_version=rule.model_version,
            metric_name=rule.metric_name,
            threshold=rule.threshold,
            actual_value=metric_value,
            severity=rule.severity
        )


class NotificationService:
    """
    Service for sending alert notifications to stakeholders.
    Supports configurable notification channels (email, Slack, etc.).
    """
    
    def __init__(self, channels=None):
        """
        Initialize the notification service with configured channels.
        
        Args:
            channels: Dictionary of notification channels with boolean enable/disable flags
                     e.g., {'email': True, 'slack': False, 'webhook': True}
        """
        # Default channels if none provided
        self.channels = channels or {
            'email': True,
            'slack': False,
            'webhook': False
        }
    
    def send_alert(self, alert: AlertEvent) -> bool:
        """
        Send a notification for an alert event.
        
        Args:
            alert: The alert event to notify about
            
        Returns:
            True if the notification was sent successfully
        """
        # Log the alert (always happens regardless of channels)
        print(f"ALERT: {alert.severity} alert for model {alert.model_id} {alert.model_version}")
        print(f"Metric {alert.metric_name} is {alert.actual_value}, threshold: {alert.operator} {alert.threshold}")
        
        # Send to enabled channels
        self._send_to_enabled_channels(alert)
        
        return True
    
    def send_notification(self, title: str, message: str, severity: str = 'MEDIUM', channels=None) -> bool:
        """
        Send a generic notification.
        
        Args:
            title: Notification title
            message: Notification message
            severity: Notification severity
            channels: Override default channels for this notification
            
        Returns:
            True if the notification was sent successfully
        """
        print(f"NOTIFICATION [{severity}]: {title}")
        print(f"Message: {message}")
        
        # Use provided channels or fall back to configured channels
        effective_channels = channels or self.channels
        
        # Log which channels were used
        channel_str = ', '.join([k for k, v in effective_channels.items() if v])
        print(f"Sent to channels: {channel_str}")
        
        return True
    
    def _send_to_enabled_channels(self, alert: AlertEvent) -> None:
        """
        Send alert to all enabled channels.
        
        Args:
            alert: The alert event to notify about
        """
        if self.channels.get('email', False):
            self._send_email(alert)
            
        if self.channels.get('slack', False):
            self._send_slack(alert)
            
        if self.channels.get('webhook', False):
            self._send_webhook(alert)
    
    def _send_email(self, alert: AlertEvent) -> None:
        """
        Send alert via email.
        
        Args:
            alert: The alert event to notify about
        """
        # This would be implemented with actual email sending logic
        print(f"[EMAIL] Alert sent for model {alert.model_id}: {alert.metric_name} {alert.operator} {alert.threshold}")
    
    def _send_slack(self, alert: AlertEvent) -> None:
        """
        Send alert via Slack.
        
        Args:
            alert: The alert event to notify about
        """
        # This would be implemented with Slack API integration
        print(f"[SLACK] Alert sent for model {alert.model_id}: {alert.metric_name} {alert.operator} {alert.threshold}")
    
    def _send_webhook(self, alert: AlertEvent) -> None:
        """
        Send alert via webhook.
        
        Args:
            alert: The alert event to notify about
        """
        # This would be implemented with webhook calls
        print(f"[WEBHOOK] Alert sent for model {alert.model_id}: {alert.metric_name} {alert.operator} {alert.threshold}")
