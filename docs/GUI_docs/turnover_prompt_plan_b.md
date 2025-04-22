# Turnover Prompt for Plan B: UI Components and User Experience

I'm working on implementing a new GUI for the TextandFlex phone analyzer application. Here's what you need to know:

## Current Status

- We've decided to scrap the existing Kivy-based GUI implementation in the `add-gui` branch due to fundamental design issues
- After evaluating different frameworks, we've chosen PyQt/PySide6 as a better fit for our data analysis application
- I've created a detailed implementation plan in `gui_implementation_plan.md` with two non-overlapping plans:
  - Plan A: Core Functionality and Data Flow (being handled separately)
  - Plan B: UI Components and User Experience (your focus)

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

I'd like you to help implement Plan B: UI Components and User Experience from the implementation plan. This involves:

1. Creating the UI components using PyQt/PySide6
2. Implementing the visual design and theming system with QSS
3. Adding accessibility features and user experience enhancements
4. Following the QA plan for UI testing with pytest-qt

Please start by:

1. Creating the new branch `new-gui-ui-components`
2. Setting up the directory structure
3. Setting up Qt Designer integration
4. Implementing the theme system and base UI constants

## Implementation Requirements

### UI Framework Setup

**Acceptance Criteria:**

- Must create a consistent directory structure for UI resources
- Must set up Qt Designer integration with .ui file conversion
- Must implement resource compilation for icons and images
- Must create a theming system with light and dark modes
- Must define a consistent set of UI constants (colors, dimensions, typography)

### Core UI Components

**Acceptance Criteria:**

- Must implement main window with proper menu, toolbar, and status bar
- Must create file selection interface with drag-and-drop support
- Must implement analysis options interface with clear controls
- Must create results display with sorting, filtering, and pagination
- Must ensure all components follow accessibility guidelines

### Advanced UI Features

**Acceptance Criteria:**

- Must implement visualization display with matplotlib integration
- Must create custom widgets that extend Qt base classes
- Must ensure keyboard navigation works for all UI elements
- Must implement high contrast mode for accessibility
- Must create responsive layouts that adapt to different screen sizes

### User Experience

**Acceptance Criteria:**

- Must implement welcome/onboarding experience for new users
- Must create settings dialog with user preference saving
- Must implement in-app help system with context-sensitive help
- Must add tooltips for all complex features
- Must create keyboard shortcut documentation

## Integration Considerations

- Work with Plan A team to understand controller interfaces
- Use mock implementations of controllers during development
- Document all signal/slot connections you expect from controllers
- Maintain a decision log for any UI design decisions
- Create UI component tests that can run without real controllers
- Coordinate with Plan A team on data model requirements for views

## Technical Details

- Use Qt Designer for creating UI layouts (.ui files)
- Implement stylesheets using QSS for theming
- Use QMainWindow as the base for the main application window
- Implement custom widgets by extending Qt widget classes
- Use matplotlib integration for data visualization
- Ensure accessibility with QAccessible and proper tab order
- Test UI components with pytest-qt
- Document all widget properties and signals

## Coding Principles

- Correct Code > Readable Code > Simple Code > Fast Code
- Fail fast at boundaries with descriptive errors
- Write explicitly, not cleverly
- Design for testability
- Separate concerns (UI elements from business logic)
- Prefer immutability
- Document decisions, not mechanics

Refer to `gui_implementation_plan.md` for the detailed checklist of tasks for Plan B and the comprehensive acceptance criteria.
