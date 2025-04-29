# Machine Learning Architecture Documentation

## Overview

The Qlix application uses a robust, service-based ML architecture designed for reliability, reusability, and maintainability. This document details the actual implementation and how components interact in the production codebase.

## Core Architecture Components

### 1. ML Exception Hierarchy

```
MLError (base exception)
├── ModelError
│   ├── TrainingError
│   └── PredictionError
├── FeatureExtractionError
└── ModelPersistenceError
```

This specialized exception hierarchy enables targeted error handling throughout the ML pipeline:

```python
try:
    result = ml_service.predict("TimePatternModel", df, column_mapping)
except PredictionError as e:
    # Handle prediction errors specifically
    logging_service.error(f"Prediction failed: {str(e)}")
except FeatureExtractionError as e:
    # Handle feature extraction errors specifically
    logging_service.error(f"Feature extraction failed: {str(e)}")
```

### 2. MLModelService

The `MLModelService` (implemented in `src/analysis_layer/ml_model_service.py`) serves as the central access point for all ML operations with these key capabilities:

- **Lifecycle Management**: Handles model initialization, training, updating, and prediction
- **Feature Flags**: Supports toggling features via the config_manager (e.g., `advanced_feature_extraction`)
- **Performance Optimization**: Implements caching for expensive operations like feature extraction
- **Centralized Error Handling**: Uses the ML exception hierarchy for structured errors
- **Model Persistence**: Manages saving/loading models with versioning

```python
# MLModelService Implementation Details
ml_service = MLModelService(
    logging_service=logging_service,  # Uses the logging service for consistent logging
    config_manager=config_manager,    # Uses config_manager for feature flags
    models_dir="models/"              # Configurable model storage location
)

# Feature flag example (from the actual implementation)
use_advanced = True
if self.config_manager and hasattr(self.config_manager, "is_feature_enabled"):
    use_advanced = self.config_manager.is_feature_enabled(
        "advanced_feature_extraction",
        default=True
    )
```

### 3. Dependency Injection

The architecture uses dependency injection via the `DependencyContainer` to:

- Promote loose coupling between components
- Simplify testing and mocking
- Enable component reuse

```python
# The ML components are registered in ml_component_registration.py
def register_ml_components(
    container: DependencyContainer,
    logging_service: Optional[LoggingService] = None,
    config_manager = None,
    models_dir: str = None
):
    # Create the ML model service
    ml_service = MLModelService(
        logging_service=logging_service,
        config_manager=config_manager,
        models_dir=models_dir
    )

    # Register the ML model service
    container.register_instance("MLModelService", ml_service)

    # Register individual model factories
    container.register(
        "TimePatternModel",
        lambda: ml_service.get_model("TimePatternModel"),
        singleton=True
    )

    # Additional model registrations...
```

## ML Models

The application uses three specialized model types:

### 1. TimePatternModel

**Purpose**: Analyzes and predicts time-based patterns in communication data.

**Actual Capabilities**:

- Identifies preferred communication times
- Detects cyclical patterns (daily, weekly)
- Recognizes response time patterns

### 2. ContactPatternModel

**Purpose**: Analyzes relationship patterns with specific contacts.

**Actual Capabilities**:

- Identifies key contacts based on frequency and timing
- Detects changes in communication patterns with specific contacts
- Recognizes relationship evolution over time

### 3. AnomalyDetectionModel

**Purpose**: Identifies unusual or anomalous communication patterns.

**Actual Capabilities**:

- Detects statistical outliers in communication
- Identifies behavioral changes and anomalies
- Flags potential security or privacy concerns

## Integration Points

### 1. Pattern Detector Integration

The `PatternDetector` class uses the MLModelService to access models:

```python
class PatternDetector:
    def __init__(self,
                 ml_model_service: Optional[MLModelService] = None,
                 logging_service: Optional[LoggingService] = None,
                 config_manager = None):
        """Initialize the pattern detector and ML models."""
        self.last_error = None
        self.logging_service = logging_service
        self.config_manager = config_manager

        # Use the ML model service if provided, otherwise create models directly
        if ml_model_service:
            self.ml_model_service = ml_model_service
            self._models_trained = True
```

### 2. Longitudinal Analysis Integration

The longitudinal analysis components (introduced in the TextandFlex Analysis Engine) integrate with the ML architecture via:

```python
def register_longitudinal_components(
    container: DependencyContainer,
    logging_service: Optional[LoggingService] = None,
    config_manager = None
):
    # Get the ML model service from the container
    ml_service = container.get("MLModelService")

    # Register the trend analyzer factory
    container.register(
        "TrendAnalyzer",
        lambda: create_trend_analyzer(ml_service, logging_service, config_manager),
        singleton=True
    )

    # Additional component registrations...
```

## Best Practices for Using This Architecture

1. **Access Models via MLModelService**: Always get models through the service, not by creating them directly.

   ```python
   # Correct approach
   ml_service = container.get("MLModelService")
   time_model = ml_service.get_model("TimePatternModel")

   # Avoid this
   from .ml_models import TimePatternModel  # Direct import
   time_model = TimePatternModel()  # Direct instantiation
   ```

2. **Use Feature Flags for Experimental Features**: The architecture supports feature flags through the config_manager.

   ```python
   # Example from actual implementation
   use_advanced = self.config_manager.is_feature_enabled(
       "advanced_feature_extraction",
       default=True
   )
   ```

3. **Handle ML Errors Appropriately**: Use the specialized exception hierarchy.

   ```python
   try:
       result = ml_service.predict("TimePatternModel", df, column_mapping)
   except MLError as e:
       logging_service.error(f"ML operation failed: {str(e)}")
   ```

4. **Register New Components with the Dependency Container**: Follow the pattern in ml_component_registration.py.

5. **Prefer Dependency Injection**: Components should get their dependencies through constructor injection.
   ```python
   # Good approach
   def __init__(self, ml_model_service=None, logging_service=None):
       self.ml_model_service = ml_model_service
       self.logging_service = logging_service
   ```

## Actual Implementation Details

The ML architecture has these implementation characteristics:

1. **Models**: Implemented as scikit-learn compatible classes with consistent interfaces
2. **Versioning**: Uses semantic versioning (major.minor.patch) with history tracking
3. **Persistence**: Models are serialized to pickle files with version information
4. **Caching**: Uses a simple key-based caching system in statistical_utils.py
5. **Error Handling**: Uses specialized exceptions with detailed context information

This document reflects the actual implementation of the ML architecture in the Qlix codebase as of April 2025.
