# PatternDetector Integration with Advanced Analyzers

_Version: 1.0_
_Date: April 24, 2025_

## 1. Overview

This document describes how the `PatternDetector` component integrates and utilizes the specialized advanced pattern analyzers:

- `GapDetector` (`src/analysis_layer/advanced_patterns/gap_detector.py`)
- `OverlapAnalyzer` (`src/analysis_layer/advanced_patterns/overlap_analyzer.py`)
- `ResponseAnalyzer` (`src/analysis_layer/advanced_patterns/response_analyzer.py`)

The `PatternDetector` acts as an orchestrator, calling these specialized analyzers and aggregating their findings alongside its own core pattern detection and ML-based results.

## 2. Integration Points within `PatternDetector`

- **Primary Method:** A central method within `PatternDetector`, likely named `detect_all_patterns` (or similar), is responsible for invoking the advanced analyzers.
- **Orchestration:** This method will:
  1. Perform initial data validation.
  2. Call core `PatternDetector` methods (e.g., for basic time/contact patterns).
  3. Call the `analyze_*` methods of the injected advanced analyzer instances (`GapDetector.detect_gaps`, `OverlapAnalyzer.analyze_overlaps`, `ResponseAnalyzer.analyze_response_patterns`).
  4. Call ML model prediction methods (via `MLModelService` or directly).
  5. Aggregate results from all sources into a unified structure.
  6. Calculate pattern significance and apply filtering if necessary.

## 3. Initialization and Dependency Management

- **Dependency Injection:** The `PatternDetector` should receive instances of `GapDetector`, `OverlapAnalyzer`, and `ResponseAnalyzer` via its constructor (`__init__`). This aligns with the project's use of a dependency container.
  ```python
  # Example PatternDetector.__init__ signature
  def __init__(self,
               gap_detector: GapDetector,
               overlap_analyzer: OverlapAnalyzer,
               response_analyzer: ResponseAnalyzer,
               ml_model_service: Optional[MLModelService] = None,
               logging_service: Optional[LoggingService] = None,
               config_manager = None):
      self.gap_detector = gap_detector
      self.overlap_analyzer = overlap_analyzer
      self.response_analyzer = response_analyzer
      self.ml_model_service = ml_model_service
      # ... rest of initialization
  ```
- **Configuration:** The `PatternDetector` may pass relevant configuration (e.g., thresholds like `min_gap_hours`) obtained from the `config_manager` to the analyzers when calling their methods, or the analyzers might fetch configuration themselves if they also receive the `config_manager`.

## 4. Data Flow

1.  Input `pd.DataFrame` and `column_mapping` are passed to `PatternDetector.detect_all_patterns`.
2.  The `DataFrame` and `column_mapping` are passed down to each advanced analyzer's respective `analyze_*` method.
3.  Each analyzer performs its specific analysis and returns results in a structured dictionary format (as defined in their respective integration contracts).
4.  `PatternDetector` collects these dictionaries.

## 5. Result Aggregation

- **Unified Structure:** The `PatternDetector` is responsible for merging the results from the advanced analyzers into its final output.
- **Pattern Types:** Results from advanced analyzers should be clearly identifiable, potentially using distinct `pattern_type` values (e.g., 'gap', 'overlap', 'response_time', 'reciprocity') or nested structures within the main result dictionary.
- **Example Aggregated Result Snippet:**
  ```python
  {
      "detected_patterns": [
          # ... patterns from core PatternDetector ...
          {
              "pattern_type": "gap",
              "subtype": "overall",
              "start_time": datetime,
              "end_time": datetime,
              "duration_hours": 48.5,
              "significance": 3.2,
              # ... from GapDetector ...
          },
          {
              "pattern_type": "overlap",
              "subtype": "contact_overlap",
              "start_time": datetime,
              "end_time": datetime,
              "contacts": ["ContactA", "ContactB"],
              # ... from OverlapAnalyzer ...
          },
          {
              "pattern_type": "response_time",
              "subtype": "average",
              "value_seconds": 300,
              # ... from ResponseAnalyzer ...
          }
      ],
      "anomalies": [
          # ... anomalies from ML models ...
          {
              "type": "response_time_spike",
              "description": "Unusually long response time...",
              # ... from ResponseAnalyzer ...
          }
      ],
      "errors": [] # List of errors encountered during analysis
  }
  ```

## 6. Error Handling

- **Catch and Log:** The `PatternDetector`'s orchestrating method (`detect_all_patterns`) must wrap calls to the advanced analyzers in `try...except` blocks.
- **Individual Failures:** If an individual analyzer fails (e.g., `ResponseAnalyzer.analyze_response_patterns` raises an exception or returns an `{"error": ...}` dictionary):
  - The error should be logged by `PatternDetector` (including which analyzer failed).
  - The failure should _not_ necessarily stop the entire pattern detection process. Other analyzers and core detection should still run.
  - The error information should be included in the final aggregated results (e.g., in a dedicated `errors` list or by adding an error field to the specific pattern type's section).
- **Propagation:** `PatternDetector` should rely on the error contracts defined for each analyzer (i.e., they log internally and return specific error indicators).

## 7. Configuration

- Thresholds and parameters for the advanced analyzers (e.g., `min_gap_hours`, `time_window_minutes`) should be managed via the central project configuration (`config.py` or `config_manager`).
- `PatternDetector` can either pass these values explicitly when calling the analyzers or the analyzers can retrieve them directly if they have access to the configuration manager.
