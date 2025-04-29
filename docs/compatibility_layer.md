# Compatibility Layer Documentation

## Overview

The compatibility layer provides a clean interface between the PySide6 GUI and the existing backend components. It follows SOLID principles and provides a clear separation of concerns, making it easier to maintain and extend the application.

## Architecture

The compatibility layer consists of the following components:

1. **Service Layer**: Abstracts backend operations for GUI controllers
   - `RepositoryService`: Abstracts repository operations
   - `AnalysisService`: Abstracts analysis operations
   - `ExportService`: Abstracts export operations
   - `ConfigManager`: Manages feature flags and application configuration

2. **Application Facade**: Provides a unified interface for the application
   - Coordinates the different services
   - Simplifies error handling and data transformation

3. **Controller Factory**: Creates controllers with appropriate dependencies
   - Handles feature flag integration
   - Ensures controllers have the correct dependencies

4. **Feature Flag System**: Enables/disables features at runtime
   - Allows for gradual rollout of new features
   - Supports A/B testing and experimental features

## Component Details

### Service Layer

#### RepositoryService

The `RepositoryService` abstracts repository operations for GUI controllers. It provides methods for:

- Getting dataset names
- Retrieving datasets
- Adding datasets
- Removing datasets
- Getting dataset metadata
- Managing dataset versions

```python
# Example usage
repository_service = RepositoryService()
dataset_names = repository_service.get_dataset_names()
dataset = repository_service.get_dataset("my_dataset")
```

#### AnalysisService

The `AnalysisService` abstracts analysis operations for GUI controllers. It provides methods for:

- Running different types of analysis (basic, contact, time, pattern)
- Transforming analysis results into GUI-friendly formats

```python
# Example usage
analysis_service = AnalysisService()
result = analysis_service.run_analysis("basic", dataframe, options={"max_contacts": 5})
```

#### ExportService

The `ExportService` handles export operations for different formats. It provides methods for:

- Exporting analysis results to different file formats (CSV, Excel, JSON)
- Generating text reports from analysis results

```python
# Example usage
export_service = ExportService()
export_service.export_to_file(analysis_result, "csv", "export.csv")
export_service.generate_report(analysis_result, "report.txt")
```

#### ConfigManager

The `ConfigManager` manages feature flags and application configuration. It provides methods for:

- Getting and setting feature flags
- Getting and setting configuration values
- Loading and saving configuration to a file

```python
# Example usage
config_manager = ConfigManager()
is_enabled = config_manager.get_feature_flag("advanced_analysis")
theme = config_manager.get_config_value("ui.theme")
config_manager.set_feature_flag("experimental_ml", True)
```

### Application Facade

The `ApplicationFacade` provides a unified interface for the application. It coordinates the different services and simplifies error handling and data transformation.

```python
# Example usage
facade = ApplicationFacade()
dataset_names = facade.get_dataset_names()
dataset = facade.get_dataset("my_dataset")
result = facade.run_analysis("basic", dataframe)
facade.export_results(result, "csv", "export.csv")
```

### Controller Factory

The `ControllerFactory` creates controllers with appropriate dependencies. It handles feature flag integration and ensures controllers have the correct dependencies.

```python
# Example usage
factory = ControllerFactory(application_facade=facade)
file_controller = factory.create_file_controller()
analysis_controller = factory.create_analysis_controller()
controllers = factory.create_all_controllers()
```

## Feature Flags

The compatibility layer supports the following feature flags:

- `repository_service`: Enables the repository service
- `analysis_service`: Enables the analysis service
- `export_service`: Enables the export service
- `visualization`: Enables visualization features
- `contact_analysis`: Enables contact analysis
- `time_analysis`: Enables time analysis
- `pattern_detection`: Enables pattern detection
- `experimental_ml`: Enables experimental machine learning features
- `disk_based_indices`: Enables disk-based indices for improved performance
- `dataset_versioning`: Enables dataset versioning

## Integration with Existing Code

The compatibility layer integrates with the existing code as follows:

1. **Data Layer**: The `RepositoryService` wraps the existing `PhoneRecordRepository` and provides a simplified interface for GUI controllers.

2. **Analysis Layer**: The `AnalysisService` wraps the existing analyzers (`BasicStatisticsAnalyzer`, `ContactAnalyzer`, `TimeAnalyzer`, `PatternDetector`) and provides a simplified interface for GUI controllers.

3. **Export Functionality**: The `ExportService` provides methods for exporting analysis results to different file formats and generating reports.

4. **GUI Controllers**: The `ControllerFactory` creates controllers with the appropriate dependencies, including services from the compatibility layer.

## Error Handling

The compatibility layer provides consistent error handling across all components:

1. **Service Layer**: Each service method validates inputs and catches exceptions from the backend components, raising `ValueError` with descriptive error messages.

2. **Application Facade**: The facade catches exceptions from the services and re-raises them with additional context.

3. **Controller Factory**: The factory handles feature flag integration and ensures controllers have the correct dependencies, even when features are disabled.

## Extension Points

The compatibility layer can be extended in the following ways:

1. **New Services**: Add new services to abstract additional backend components.

2. **New Feature Flags**: Add new feature flags to enable/disable features at runtime.

3. **New Controllers**: Add new controllers to the controller factory.

4. **New Export Formats**: Add new export formats to the export service.

## Testing

The compatibility layer includes comprehensive tests:

1. **Unit Tests**: Each component has unit tests that verify its behavior in isolation.

2. **Integration Tests**: Integration tests verify that the components work together correctly.

3. **Feature Flag Tests**: Tests verify that feature flags correctly enable/disable features.

4. **Error Handling Tests**: Tests verify that errors are handled correctly and appropriate error messages are provided.

## Usage Examples

### Basic Workflow

```python
# Create the application facade
facade = ApplicationFacade()

# Add a dataset
facade.add_dataset("my_dataset", dataframe, column_mapping)

# Run an analysis
result = facade.run_analysis("basic", dataframe)

# Export the results
facade.export_results(result, "csv", "export.csv")
```

### Creating Controllers

```python
# Create the controller factory
factory = ControllerFactory(application_facade=facade)

# Create individual controllers
file_controller = factory.create_file_controller()
analysis_controller = factory.create_analysis_controller()

# Create all controllers
controllers = factory.create_all_controllers()
```

### Managing Feature Flags

```python
# Check if a feature is enabled
is_enabled = facade.is_feature_enabled("advanced_analysis")

# Enable a feature
facade.set_feature_flag("experimental_ml", True)

# Disable a feature
facade.set_feature_flag("experimental_ml", False)
```

## Conclusion

The compatibility layer provides a clean interface between the PySide6 GUI and the existing backend components. It follows SOLID principles and provides a clear separation of concerns, making it easier to maintain and extend the application.
