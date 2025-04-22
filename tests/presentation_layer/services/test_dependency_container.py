"""
Tests for the dependency container.
"""
import pytest
from unittest.mock import MagicMock

from src.presentation_layer.services.dependency_container import DependencyContainer


class TestDependencyContainer:
    """Tests for the DependencyContainer class."""

    def test_register_and_get(self):
        """Test registering and getting a service."""
        # Arrange
        container = DependencyContainer()
        mock_service = MagicMock()
        
        # Act
        container.register("test_service", lambda: mock_service)
        result = container.get("test_service")
        
        # Assert
        assert result is mock_service
    
    def test_register_instance(self):
        """Test registering an existing instance."""
        # Arrange
        container = DependencyContainer()
        mock_service = MagicMock()
        
        # Act
        container.register_instance("test_service", mock_service)
        result = container.get("test_service")
        
        # Assert
        assert result is mock_service
    
    def test_singleton(self):
        """Test that singleton services return the same instance."""
        # Arrange
        container = DependencyContainer()
        counter = 0
        
        def factory():
            nonlocal counter
            counter += 1
            return counter
        
        # Act
        container.register("singleton_service", factory, singleton=True)
        result1 = container.get("singleton_service")
        result2 = container.get("singleton_service")
        
        # Assert
        assert result1 == 1
        assert result2 == 1  # Same instance
        assert counter == 1  # Factory called only once
    
    def test_non_singleton(self):
        """Test that non-singleton services return new instances."""
        # Arrange
        container = DependencyContainer()
        counter = 0
        
        def factory():
            nonlocal counter
            counter += 1
            return counter
        
        # Act
        container.register("non_singleton_service", factory, singleton=False)
        result1 = container.get("non_singleton_service")
        result2 = container.get("non_singleton_service")
        
        # Assert
        assert result1 == 1
        assert result2 == 2  # New instance
        assert counter == 2  # Factory called twice
    
    def test_get_typed(self):
        """Test getting a service with type checking."""
        # Arrange
        container = DependencyContainer()
        mock_service = "test"
        
        # Act
        container.register_instance("test_service", mock_service)
        result = container.get_typed("test_service", str)
        
        # Assert
        assert result == "test"
    
    def test_get_typed_wrong_type(self):
        """Test getting a service with wrong type."""
        # Arrange
        container = DependencyContainer()
        mock_service = "test"
        
        # Act
        container.register_instance("test_service", mock_service)
        
        # Assert
        with pytest.raises(ValueError) as exc_info:
            container.get_typed("test_service", int)
        
        assert "wrong type" in str(exc_info.value)
    
    def test_has(self):
        """Test checking if a service is registered."""
        # Arrange
        container = DependencyContainer()
        
        # Act
        container.register("test_service", lambda: "test")
        
        # Assert
        assert container.has("test_service") is True
        assert container.has("nonexistent_service") is False
    
    def test_get_nonexistent(self):
        """Test getting a nonexistent service."""
        # Arrange
        container = DependencyContainer()
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            container.get("nonexistent_service")
        
        assert "not registered" in str(exc_info.value)
    
    def test_clear(self):
        """Test clearing all services."""
        # Arrange
        container = DependencyContainer()
        container.register("test_service", lambda: "test")
        
        # Act
        container.clear()
        
        # Assert
        assert container.has("test_service") is False
    
    def test_clear_instances(self):
        """Test clearing instances but keeping factories."""
        # Arrange
        container = DependencyContainer()
        counter = 0
        
        def factory():
            nonlocal counter
            counter += 1
            return counter
        
        container.register("test_service", factory, singleton=True)
        result1 = container.get("test_service")
        
        # Act
        container.clear_instances()
        result2 = container.get("test_service")
        
        # Assert
        assert result1 == 1
        assert result2 == 2  # New instance after clearing
        assert counter == 2  # Factory called twice
