# ML Component Integration Guide

This guide provides instructions for integrating new components with the ML architecture in the Qlix project. It's particularly focused on integrating the TextandFlex Analysis Engine components with the core ML architecture.

## Architecture Overview

The ML architecture is built on these key components:

1. **MLModelService**: Central service for managing ML model operations
2. **Dependency Container**: Registry for component creation and dependency injection
3. **Component Registration**: Functions for registering components with the container

## Integration Steps for New Components

### 1. Component Design

When creating a new analytical component:

```python
class YourComponent:
    def __init__(self,
                 ml_model_service=None,
                 logging_service=None,
                 config_manager=None):
        """Initialize with dependencies."""
        # Get services from container if not provided
        self.ml_model_service = ml_model_service
        self.logging_service = logging_service
        self.config_manager = config_manager

    def your_analysis_method(self, df, column_mapping=None):
        """Perform analysis using the ML service."""
        try:
            # Extract features using MLModelService
            features = self.ml_model_service.extract_features(df, column_mapping)

            # Use models for prediction
            result = self.ml_model_service.predict(
                "TimePatternModel", df, column_mapping
            )

            # Your implementation...

            # Log success
            if self.logging_service:
                self.logging_service.info(
                    "Analysis completed successfully",
                    component="YourComponent"
                )

            return result

        except MLError as e:
            # Handle errors appropriately
            if self.logging_service:
                self.logging_service.error(
                    f"Error during analysis: {str(e)}",
                    component="YourComponent",
                    error=str(e)
                )
            raise
```

### 2. Component Registration

Register your component with the dependency container:

```python
# In your component registration module
def register_your_components(container, logging_service=None, config_manager=None):
    # Get the ML service from the container
    ml_service = container.get("MLModelService")

    # Register your components
    container.register(
        "YourComponent",
        lambda: create_your_component(ml_service, logging_service, config_manager),
        singleton=True
    )

def create_your_component(ml_model_service, logging_service=None, config_manager=None):
    from .your_module import YourComponent

    return YourComponent(
        ml_model_service=ml_model_service,
        logging_service=logging_service,
        config_manager=config_manager
    )
```

### 3. Feature Flag Integration

Use feature flags for experimental features:

```python
def your_method(self):
    # Check if feature is enabled
    use_advanced_feature = True
    if self.config_manager and hasattr(self.config_manager, "is_feature_enabled"):
        use_advanced_feature = self.config_manager.is_feature_enabled(
            "your_feature_flag", default=False
        )

    if use_advanced_feature:
        # Advanced implementation
        pass
    else:
        # Standard implementation
        pass
```

### 4. Error Handling

Use the ML exception hierarchy consistently:

```python
from ..ml_exceptions import MLError, FeatureExtractionError

try:
    # Your code
except FeatureExtractionError as e:
    # Handle specific error
    pass
except MLError as e:
    # Handle general ML errors
    pass
```

## Integration Guide for TextandFlex Components

### Longitudinal Analysis Components

For components like `TrendAnalyzer`, `ContactEvolutionTracker`, and `SeasonalityDetector`:

1. **Use MLModelService for all ML operations**:

   - Feature extraction
   - Model predictions
   - Model training (if needed)

2. **Register with the dependency container** using `longitudinal_component_registration.py`

3. **Follow consistent logging patterns** using the LoggingService

### Advanced Pattern Detection Components

For components like `GapDetector`, `OverlapAnalyzer`, and `ResponseAnalyzer`:

1. **Use MLModelService for ML operations**

2. **Create a similar registration module** for pattern detection components

3. **Implement consistent error handling** using the ML exception hierarchy

## Best Practices

1. **Dependency Injection**: Always design components to accept dependencies in the constructor

2. **Error Handling**: Use the appropriate exception types from the ML exception hierarchy

3. **Logging**: Log important events using the logging service with consistent component names

4. **Feature Flags**: Use feature flags for experimental or high-resource features

5. **Testing**: Create unit tests that mock dependencies for isolated testing

## Example: Integrating TrendAnalyzer

```python
# In longitudinal/trend_analyzer.py
class TrendAnalyzer:
    def __init__(self, ml_model_service=None, logging_service=None, config_manager=None):
        self.ml_model_service = ml_model_service
        self.logging_service = logging_service
        self.config_manager = config_manager

    def analyze_trends(self, df, column_mapping=None, time_window=None):
        try:
            # Get predictions from time pattern model
            result = self.ml_model_service.predict(
                "TimePatternModel", df, column_mapping
            )

            # Extract trends from predictions
            # Implementation...

            return trends

        except MLError as e:
            if self.logging_service:
                self.logging_service.error(
                    f"Error analyzing trends: {str(e)}",
                    component="TrendAnalyzer",
                    error=str(e)
                )
            raise
```

This guide provides a foundation for integrating new components with the ML architecture.
