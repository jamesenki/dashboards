"""
Service locator pattern for dependency injection of services.

This module provides a central registry for services to enable
dependency injection and testability.
"""
from typing import Dict, Type, TypeVar, Any, Optional, cast

# Type variable for services
T = TypeVar('T')

# Global registry of service instances
_services: Dict[Type, Any] = {}

# Global registry of service factories 
_factories: Dict[Type, Any] = {}


def register_service(service_type: Type[T], instance: T) -> None:
    """Register a service instance with the service locator.
    
    Args:
        service_type: The type/class of service
        instance: The service instance to register
    """
    _services[service_type] = instance


def register_factory(service_type: Type[T], factory) -> None:
    """Register a factory function for a service type.
    
    Args:
        service_type: The type/class of service
        factory: A callable that creates an instance of the service
    """
    _factories[service_type] = factory


def get_service(service_type: Type[T]) -> T:
    """Get a service instance by type.
    
    If the service instance doesn't exist yet but a factory is registered,
    it will create the instance using the factory.
    
    Args:
        service_type: The type/class of service to retrieve
        
    Returns:
        The service instance
        
    Raises:
        KeyError: If no service instance or factory is registered for the type
    """
    # Return existing instance if available
    if service_type in _services:
        return cast(T, _services[service_type])
    
    # Create instance using factory if available
    if service_type in _factories:
        instance = _factories[service_type]()
        _services[service_type] = instance
        return cast(T, instance)
    
    raise KeyError(f"No service or factory registered for type: {service_type.__name__}")


def clear_services() -> None:
    """Clear all registered services and factories.
    
    This is useful for testing or resetting the application state.
    """
    _services.clear()
    _factories.clear()
