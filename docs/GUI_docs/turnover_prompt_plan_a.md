# Turnover Prompt for Plan A: Core Functionality and Data Flow

I'm working on implementing a new GUI for the TextandFlex phone analyzer application. Here's what you need to know:

## Current Status

- We've decided to scrap the existing Kivy-based GUI implementation in the `add-gui` branch due to fundamental design issues
- After evaluating different frameworks, we've chosen PyQt/PySide6 as a better fit for our data analysis application
- I've created a detailed implementation plan in `gui_implementation_plan.md` with two non-overlapping plans:
  - Plan A: Core Functionality and Data Flow (your focus)
  - Plan B: UI Components and User Experience (being handled separately)

## Why PyQt/PySide6?

- Better fit for data analysis with excellent support for tables, charts, and data visualization
- Native look and feel on all platforms
- Mature ecosystem with comprehensive documentation
- Strong integration with data science libraries (pandas, matplotlib, numpy)
- Development efficiency with Qt Designer for visual UI design

## Repository Information

- Repository: https://github.com/Phazzie/TextandFlex
- Current branch: `add-gui` (but we'll be creating new branches)
- The application analyzes phone records data from Excel/CSV files

## Your Task

I'd like you to help implement Plan A: Core Functionality and Data Flow from the implementation plan. This involves:

1. Setting up the core infrastructure for the GUI
2. Implementing data models and controllers
3. Integrating with the existing application components
4. Following the QA plan for core functionality testing

Please start by:

1. Creating the new branch `new-gui-core-functionality`
2. Setting up the directory structure
3. Installing PySide6 dependencies
4. Implementing the error handling system
5. Implementing the file validation system

## Implementation Requirements

### Error Handling System

**Acceptance Criteria:**

- Must categorize errors by severity (INFO, WARNING, ERROR, CRITICAL)
- Must log errors with appropriate context (component, operation, timestamp)
- Must sanitize sensitive information in logs and UI messages
- Must display user-friendly messages without technical details
- Must provide actionable next steps in error messages

### File Validation System

**Acceptance Criteria:**

- Must validate file extensions (.xlsx, .csv only)
- Must check file size (reject files > 10MB)
- Must prevent path traversal attacks
- Must validate file content (headers, required columns)
- Must provide specific error messages for each validation failure

### Data Models

**Acceptance Criteria:**

- Must implement immutable data structures
- Must extend QAbstractTableModel/QAbstractItemModel
- Must validate data on creation
- Must be thread-safe for background processing
- Must include comprehensive unit tests

### Controllers

**Acceptance Criteria:**

- Must use Qt signals/slots for event notification
- Must handle errors gracefully with appropriate logging
- Must implement background processing for long operations
- Must not block the UI thread
- Must be testable in isolation with mock dependencies

## Integration Considerations

- Create clear interface contracts that Plan B components will depend on
- Document all signal/slot connections that will be used by UI components
- Maintain a decision log for any architectural changes
- Create mock implementations of your components for Plan B team to use
- Coordinate with Plan B team on data model requirements for views

## Technical Details

- Use Qt's signal/slot mechanism for event handling
- Implement background processing with QThreadPool for long-running operations
- Create QAbstractItemModel subclasses for data representation
- Use pytest-qt for testing Qt components
- Ensure thread safety in all shared data structures
- Document all public APIs with clear examples

## Coding Principles

- Correct Code > Readable Code > Simple Code > Fast Code
- Fail fast at boundaries with descriptive errors
- Write explicitly, not cleverly
- Design for testability
- Separate concerns (business logic from UI)
- Prefer immutability
- Document decisions, not mechanics

Refer to `gui_implementation_plan.md` for the detailed checklist of tasks for Plan A and the comprehensive acceptance criteria.
