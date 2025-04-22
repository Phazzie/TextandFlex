# Interface Contracts and Signal/Slot Documentation for GUI Integration

## Overview

This document defines the interface contracts between controllers (core logic) and views (UI components), and documents the key Qt signal/slot connections for the new PySide6 GUI. This is intended for both backend and UI teams to ensure smooth integration and testability.

---

## 1. Controller Interfaces

### FileController

- **Signals:**
  - `fileValidated(str filePath, bool isValid, str message)`
  - `fileLoaded(FileModel fileModel)`
  - `fileError(str message)`
- **Slots/Methods:**
  - `selectFile(str filePath)`
  - `validateFile(str filePath)`
  - `loadFile(str filePath)`

### AnalysisController

- **Signals:**
  - `analysisStarted(str analysisType)`
  - `analysisProgress(int percent)`
  - `analysisCompleted(AnalysisResult result)`
  - `analysisError(str message)`
- **Slots/Methods:**
  - `runAnalysis(str analysisType, FileModel fileModel)`
  - `cancelAnalysis()`

### AppController

- **Signals:**
  - `stateChanged(str newState)`
  - `errorOccurred(str message)`
- **Slots/Methods:**
  - `setState(str newState)`
  - `handleEvent(str eventType, dict eventData)`

---

## 2. View-Controller Connections

- **FileView** connects to FileController:

  - Calls `selectFile()` on file selection
  - Listens for `fileValidated`, `fileLoaded`, `fileError` signals

- **AnalysisView** connects to AnalysisController:

  - Calls `runAnalysis()` on user action
  - Listens for `analysisStarted`, `analysisProgress`, `analysisCompleted`, `analysisError` signals

- **ResultsView**:

  - Receives `AnalysisResult` from AnalysisController
  - Displays via QAbstractItemModel subclass

- **MainWindow** connects to AppController:
  - Listens for `stateChanged`, `errorOccurred` signals
  - Calls `setState()` on navigation or workflow events

---

## 3. Data Model Contracts

- **FileModel**: Immutable, validated, provides file metadata and data for display
- **AnalysisResult**: Immutable, contains results for all analysis types, supports serialization for export
- **QAbstractTableModel/QAbstractItemModel**: Used for data display in ResultsView and FileView

---

## 4. Signal/Slot Example (PySide6 Syntax)

```python
# Example: Connecting FileView to FileController
file_controller = FileController()
file_view = FileView()
file_controller.fileValidated.connect(file_view.onFileValidated)
file_controller.fileError.connect(file_view.showError)
file_view.fileSelected.connect(file_controller.selectFile)
```

---

## 5. Testing and Mocking

- All controllers should be mockable for UI tests
- Signals should be tested using pytest-qt's QSignalSpy
- Views should not depend on concrete controller implementations (use interfaces/abstract base classes)

---

## 6. Notes

- All signals must be emitted on the main Qt thread
- Error messages should be user-friendly and never expose internal details
- All data passed between layers must be validated

---

_Last updated: 2025-04-22_
