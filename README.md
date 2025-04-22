# TextyMcTextface

A Python application for analyzing text message records to extract insights about communication patterns and relationships.

## Features

- Parse Excel (.xlsx) files containing text message records
- Analyze text message data for patterns and insights
- Generate statistical reports on communication habits
- Identify key contacts and communication patterns
- Export analysis results to various formats (CSV, Excel, JSON)
- Command-line interface for easy operation

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/Phazzie/TextyMcTextface.git
   cd TextyMcTextface
   ```

2. Create a virtual environment and activate it:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```
python -m src.app analyze path/to/your/phone_records.xlsx
```

### Available Commands

- `analyze`: Analyze phone records from an Excel file
- `export`: Export analysis results to a file
- `list`: List available datasets
- `stats`: Show basic statistics for a dataset

### Examples

Analyze a phone records file:

```
python -m src.app analyze data/my_phone_records.xlsx
```

Export analysis results to CSV:

```
python -m src.app export --format csv --output results.csv
```

Show basic statistics:

```
python -m src.app stats
```

## Data Format

The application expects Excel files with the following columns:

- `timestamp`: Date and time of the communication
- `phone_number`: The contact's phone number
- `message_type`: Type of message (sent/received)
- `message_content`: Content of the text message

## Development

### Running Tests

```
pytest
```

### Project Structure

- `src/`: Source code
  - `data_layer/`: Data parsing and storage
  - `analysis_layer/`: Analysis functionality
  - `cli/`: Command-line interface
  - `export/`: Export functionality
  - `services/`: Coordination services
  - `utils/`: Utility functions
- `tests/`: Test files
- `data/`: Data directory for user files
- `docs/`: Documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Thanks to all contributors who have helped with the development of this tool.

## Machine Learning Model Usage

The analysis layer includes several machine learning models for pattern detection, anomaly detection, and contact grouping. These models are implemented in `src/analysis_layer/ml_models.py` and can be used as follows:

### Feature Extraction

Use the `extract_features` function to convert raw DataFrames into features suitable for ML models. You can provide a custom column mapping if your data uses different column names.

```python
from src.analysis_layer.ml_models import extract_features
features = extract_features(df, column_mapping={'timestamp': 'Time', 'message_length': 'Len'})
```

### Training and Using ML Models

```python
from src.analysis_layer.ml_models import TimePatternModel, ContactPatternModel, AnomalyDetectionModel

# Time-based pattern regression
model = TimePatternModel()
model.train(features, labels)
predictions = model.predict(features)
metrics = model.evaluate(test_features, test_labels)
model.save('time_model.pkl')
model.load('time_model.pkl')

# Contact-based clustering
contact_model = ContactPatternModel()
contact_model.train(features)
contact_preds = contact_model.predict(features)

# Anomaly detection (supports incremental learning)
anomaly_model = AnomalyDetectionModel()
anomaly_model.train(features)
# For large datasets, use batched/incremental training:
for batch in extract_features_batched(df, batch_size=1000):
    anomaly_model._partial_fit(batch)
```

### Model Persistence

- Use `.save(path)` and `.load(path)` to persist models between sessions.

### Incremental Learning

- `AnomalyDetectionModel` supports incremental (batched) training via `_partial_fit`.
- Use `train_batched` for efficient training on large datasets.

### Notes

- All models require features extracted with `extract_features` or `extract_features_batched`.
- You can customize column mapping for different data sources.
- See docstrings in `ml_models.py` for more details and examples.
