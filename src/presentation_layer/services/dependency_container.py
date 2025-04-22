"""
Dependency Container Module
------------------------
Provides dependency injection for the compatibility layer.
"""
from typing import Dict, Any, Type, Optional, Callable, TypeVar, cast

T = TypeVar('T')


class DependencyContainer:
    """
    Dependency injection container for the compatibility layer.
    
    This class provides a simple dependency injection container that
    manages service instances and their dependencies.
    """
    
    def __init__(self):
        """Initialize the dependency container."""
        self._factories: Dict[str, Callable[..., Any]] = {}
        self._instances: Dict[str, Any] = {}
        self._singletons: Dict[str, bool] = {}
    
    def register(self, name: str, factory: Callable[..., T], 
                singleton: bool = True) -> None:
        """
        Register a service factory.
        
        Args:
            name: Name of the service
            factory: Factory function to create the service
            singleton: Whether the service should be a singleton
        """
        self._factories[name] = factory
        self._singletons[name] = singleton
        
        # Clear instance if it exists
        if name in self._instances:
            del self._instances[name]
    
    def register_instance(self, name: str, instance: T) -> None:
        """
        Register an existing instance.
        
        Args:
            name: Name of the service
            instance: Service instance
        """
        self._instances[name] = instance
        self._singletons[name] = True
    
    def get(self, name: str) -> Any:
        """
        Get a service instance.
        
        Args:
            name: Name of the service
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If the service is not registered
        """
        # Return existing instance if it's a singleton
        if name in self._instances and self._singletons.get(name, False):
            return self._instances[name]
        
        # Create new instance
        if name in self._factories:
            factory = self._factories[name]
            instance = factory()
            
            # Store instance if it's a singleton
            if self._singletons.get(name, False):
                self._instances[name] = instance
            
            return instance
        
        raise ValueError(f"Service '{name}' not registered")
    
    def get_typed(self, name: str, expected_type: Type[T]) -> T:
        """
        Get a service instance with type checking.
        
        Args:
            name: Name of the service
            expected_type: Expected type of the service
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If the service is not registered or has wrong type
        """
        instance = self.get(name)
        
        if not isinstance(instance, expected_type):
            raise ValueError(
                f"Service '{name}' has wrong type. "
                f"Expected {expected_type.__name__}, got {type(instance).__name__}"
            )
        
        return cast(T, instance)
    
    def has(self, name: str) -> bool:
        """
        Check if a service is registered.
        
        Args:
            name: Name of the service
            
        Returns:
            True if the service is registered, False otherwise
        """
        return name in self._factories or name in self._instances
    
    def clear(self) -> None:
        """Clear all registered services and instances."""
        self._factories.clear()
        self._instances.clear()
        self._singletons.clear()
    
    def clear_instances(self) -> None:
        """Clear all service instances but keep factories."""
        self._instances.clear()


# Create a global container instance
container = DependencyContainer()
