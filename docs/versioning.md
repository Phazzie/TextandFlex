# Dataset Versioning System

The Phone Records Analyzer includes a comprehensive dataset versioning system that allows users to track changes to datasets over time, compare different versions, and revert to previous versions if needed.

## Overview

The versioning system provides the following capabilities:

- **Version Tracking**: Each dataset can have multiple versions, each with its own metadata.
- **Version History**: A complete history of all versions is maintained, including who created each version and when.
- **Version Comparison**: Different versions of a dataset can be compared to see what changed.
- **Version Reversion**: Datasets can be reverted to previous versions if needed.
- **Version Lineage**: Parent-child relationships between versions are tracked.

## Key Components

The versioning system consists of the following key components:

### 1. Version Metadata

Version metadata is stored in the `DatasetVersion` class, which includes:

- **Version Number**: A unique identifier for the version.
- **Author**: The user who created the version.
- **Timestamp**: When the version was created.
- **Description**: A description of the changes in this version.
- **Parent Version**: The version from which this version was derived.
- **Changes**: A dictionary of changes made in this version.

### 2. Version History

Version history is managed by the `VersionHistory` class, which includes:

- **Dataset Name**: The name of the dataset.
- **Versions**: A dictionary of all versions of the dataset.
- **Current Version**: The currently active version.

### 3. Version Manager

The `VersionManager` class provides the core functionality for managing versions:

- **Initializing Versioning**: Setting up versioning for a dataset.
- **Creating Versions**: Creating new versions of a dataset.
- **Getting Versions**: Retrieving specific versions of a dataset.
- **Comparing Versions**: Comparing different versions of a dataset.
- **Setting Current Version**: Changing the active version of a dataset.

### 4. Repository Integration

The `PhoneRecordRepository` class integrates with the versioning system to provide a high-level interface for working with versioned datasets:

- **Adding Datasets with Versioning**: Creating new datasets with versioning enabled.
- **Creating Dataset Versions**: Creating new versions of existing datasets.
- **Getting Dataset Versions**: Retrieving specific versions of a dataset.
- **Getting Version History**: Retrieving the version history of a dataset.
- **Comparing Dataset Versions**: Comparing different versions of a dataset.
- **Reverting to Version**: Reverting a dataset to a previous version.

## Usage Examples

### Enabling Versioning for a Dataset

```python
# Add a dataset with versioning enabled
repository.add_dataset(
    name="my_dataset",
    data=my_dataframe,
    column_mapping=my_column_mapping,
    enable_versioning=True,
    version_author="user123"
)
```

### Creating a New Version

```python
# Get the dataset
dataset = repository.get_dataset("my_dataset")

# Modify the dataset
modified_data = dataset.data.copy()
modified_data.loc[0, "duration"] = 90

# Update the dataset
repository.update_dataset(
    name="my_dataset",
    data=modified_data
)

# Create a new version
version_number = repository.create_dataset_version(
    name="my_dataset",
    description="Modified duration",
    author="user123"
)
```

### Getting a Specific Version

```python
# Get version 1
dataset_v1 = repository.get_dataset_version("my_dataset", 1)
```

### Getting Version History

```python
# Get version history
history = repository.get_dataset_version_history("my_dataset")
```

### Comparing Versions

```python
# Compare versions 1 and 2
comparison = repository.compare_dataset_versions("my_dataset", 1, 2)
```

### Reverting to a Previous Version

```python
# Revert to version 1
repository.revert_to_version("my_dataset", 1)
```

## Implementation Details

### Storage Format

Version data is stored in the following formats:

- **Version History**: Stored as JSON files in the repository storage directory.
- **Version Data**: Stored as pickle files in the repository storage directory.

### Version Naming Convention

Version files follow a specific naming convention:

- **Version History**: `{dataset_name}_version_history.json`
- **Version Data**: `{dataset_name}_v{version_number}.pkl`

### Error Handling

The versioning system includes robust error handling with custom exceptions:

- **VersioningError**: Base exception for versioning errors.
- **VersionNotFoundError**: Raised when a requested version is not found.
- **DatasetNotFoundError**: Raised when a requested dataset is not found.

## Best Practices

1. **Enable Versioning Early**: Enable versioning when first creating a dataset to ensure all changes are tracked.
2. **Provide Descriptive Version Information**: Include detailed descriptions and author information when creating versions.
3. **Create Versions for Significant Changes**: Create new versions for significant changes to datasets.
4. **Use Version Comparison**: Use the version comparison functionality to understand what changed between versions.
5. **Clean Up Old Versions**: Periodically clean up old versions that are no longer needed to save disk space.

## Limitations

1. **Storage Overhead**: Versioning increases storage requirements as each version is stored separately.
2. **Performance Impact**: Loading and comparing versions can have a performance impact for large datasets.
3. **No Branching**: The current implementation supports linear versioning only, not branching.
4. **No Merging**: There is no support for merging changes from different versions.

## Future Enhancements

1. **Branching Support**: Add support for branching to allow multiple parallel versions.
2. **Merging Support**: Add support for merging changes from different versions.
3. **Diff Visualization**: Add visualization of differences between versions.
4. **Version Tagging**: Add support for tagging versions with labels.
5. **Version Pruning**: Add support for pruning old versions to save disk space.
