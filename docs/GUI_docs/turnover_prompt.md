# Turnover Prompt for New Chat Window

I'm working on implementing a new GUI for the TextandFlex phone analyzer application. Here's what you need to know:

## Current Status
- We've decided to scrap the existing Kivy-based GUI implementation in the `add-gui` branch due to fundamental design issues
- After evaluating different frameworks, we've chosen PyQt/PySide6 as a better fit for our data analysis application
- I've created a detailed implementation plan in `gui_implementation_plan.md` with two non-overlapping plans:
  - Plan A: Core Functionality and Data Flow
  - Plan B: UI Components and User Experience

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

The implementation should follow these principles:
- Correct Code > Readable Code > Simple Code > Fast Code
- Fail fast at boundaries with descriptive errors
- Write explicitly, not cleverly
- Design for testability
- Separate concerns (UI elements from business logic)
- Prefer immutability
- Document decisions, not mechanics

Refer to `gui_implementation_plan.md` for the detailed checklist of tasks for Plan B.
