# ResponseAnalyzer Integration Contract

_Version: 1.0_
_Date: April 24, 2025_

## 1. Overview

This document defines the integration contract for the `ResponseAnalyzer` component within the TextandFlex Analysis Engine. The `ResponseAnalyzer` is responsible for analyzing response times, reciprocity, and related conversational dynamics from communication data. It integrates with the `PatternDetector` and its results may be consumed by the `InsightGenerator`.

## 2. Component Location

- **Implementation:** `src/analysis_layer/advanced_patterns/response_analyzer.py`
- **Class Name:** `ResponseAnalyzer`

## 3. Dependencies

- **Logging:** Standard project logger (`src/logger.py`)
- **Configuration:** Standard project configuration (`src/config.py`)
- **Data Structures:** Pandas DataFrame
- **Error Handling:** Project-specific exceptions (e.g., `MLExceptions` hierarchy if available, otherwise standard Python exceptions).
- **ML Models:** May interact with models via `MLModelService` (if implemented) or directly with models in `src/analysis_layer/ml_models.py` for complex pattern recognition or anomaly detection.

## 4. API Contract

### `__init__(self)`

- **Purpose:** Initializes the `ResponseAnalyzer`.
- **Parameters:** None
- **Behavior:** Sets up the analyzer with default values. The `last_error` attribute is initialized to None.

**Note:** This follows the pattern used by other advanced pattern detection components like GapDetector and OverlapAnalyzer, which don't take constructor parameters but instead use the project's standard logger and caching utilities.

### `analyze_response_patterns(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> Dict`

- **Purpose:** Analyzes the input DataFrame to identify response-related patterns and anomalies.
- **Parameters:**
  - `df` (`pd.DataFrame`): DataFrame containing communication records. Expected columns (based on `column_mapping`):
    - Timestamp column (e.g., 'timestamp', datetime)
    - Contact identifier column (e.g., 'phone_number', str)
    - Message type/direction column (e.g., 'message_type', str, indicating 'sent'/'received')
    - Potentially message content for context (e.g., 'message_content', str)
  - `column_mapping` (`Dict[str, str]`): A dictionary mapping standard column names (like 'timestamp', 'phone_number', 'message_type') to the actual column names in the input `df`.
- **Returns:** (`Dict`) A dictionary containing the analysis results. The structure should be:
  ```python
  {
      "response_times": {
          "average_response_time_seconds": float | None,
          "median_response_time_seconds": float | None,
          "response_time_distribution": Dict[str, float], # e.g., {'<1min': 0.5, '1-5min': 0.3, ...}
          "details": pd.DataFrame | List[Dict] | None # Optional: Detailed response time calculations per message pair
      },
      "reciprocity_patterns": {
          "initiation_ratio": float | None, # Ratio of conversations initiated by user vs. contact
          "response_rate": float | None, # Overall rate at which received messages get a response
          "contact_reciprocity": Dict[str, Dict], # Per-contact reciprocity metrics
          "details": pd.DataFrame | List[Dict] | None # Optional: Detailed reciprocity calculations
      },
      "conversation_flows": {
          "common_sequences": List[Dict], # e.g., [{'sequence': ['received', 'sent'], 'count': 150}, ...]
          "turn_taking_metrics": Dict, # Metrics on conversation turn length, interruptions etc.
          "details": pd.DataFrame | List[Dict] | None # Optional: Detailed flow analysis
      },
      "anomalies": [
           # List of detected anomalies related to response patterns
           # Example:
           # {
           #     "type": "response_time_spike",
           #     "description": "Unusually long response time to Contact X on Y date",
           #     "severity": 0.8, # 0.0 to 1.0
           #     "timestamp": datetime,
           #     "contact": "Contact X",
           #     "details": {...} # Specific data about the anomaly
           # }, ...
      ],
      "error": str | None # Error message if analysis failed, None otherwise
  }
  ```
  - If analysis fails catastrophically, the dictionary should contain only the `"error"` key with a descriptive message. Individual sections might be `None` or empty if specific analysis parts fail or yield no results.

## 5. Integration Points

- **Called By:** `PatternDetector` (likely within its main pattern detection method, e.g., `detect_all_patterns` or `_detect_advanced_patterns`).
- **Results Used By:**
  - `PatternDetector`: To aggregate response patterns with other detected patterns.
  - `InsightGenerator`: To generate narrative insights based on response times, reciprocity, and anomalies.

## 6. Error Handling

- The `analyze_response_patterns` method must catch all internal exceptions (including those from dependencies like ML models).
- Log caught exceptions using the standard project logger, including tracebacks where appropriate.
- If an analysis step fails but others can proceed, populate the relevant section of the return dictionary with an error indicator or leave it empty/None, and log the specific failure.
- If the entire analysis fails, return a dictionary containing only `{"error": "Detailed error message"}`.
- Use specific exceptions from the project's `MLExceptions` hierarchy (or standard exceptions like `ValueError`, `TypeError`, `KeyError`) where appropriate to signal specific failure modes (e.g., `DataFormatError`, `ModelPredictionError`).

## 7. Logging

- Use the standard project logger (`src/logger.py`).
- Log key steps during analysis (e.g., "Starting response time analysis", "Completed reciprocity analysis").
- Log warnings for potential data issues (e.g., "Insufficient data for reliable response time calculation for contact X").
- Log errors with tracebacks when exceptions are caught.
- Avoid logging sensitive data from the messages themselves unless explicitly configured for debugging.

## 8. Performance Considerations

- The analyzer should be mindful of performance, especially with large datasets.
- Implement efficient calculations (e.g., vectorized operations with Pandas where possible).
- Consider caching intermediate results if applicable and computationally expensive.
