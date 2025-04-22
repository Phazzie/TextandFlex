import argparse
from typing import List, Optional

class Command:
    """Base class for all commands."""
    def execute(self):
        raise NotImplementedError("Subclasses must implement this method")

class AnalyzeCommand(Command):
    """Command to analyze phone records."""
    def __init__(self, file_path: str):
        self.file_path = file_path

    def execute(self):
        print(f"Analyzing file: {self.file_path}")
        # Add analysis logic here

class ExportCommand(Command):
    """Command to export analysis results."""
    def __init__(self, file_path: str, format: str = "csv"):
        self.file_path = file_path
        self.format = format

    def execute(self):
        print(f"Exporting file: {self.file_path} to format: {self.format}")
        # Add export logic here

class GuiCommand(Command):
    """Command to launch the new PySide6 GUI."""
    def __init__(self, theme: Optional[str] = None, debug: bool = False):
        self.theme = theme
        self.debug = debug

    def execute(self):
        """Execute the GUI command."""
        from src.app import launch_gui
        print("Launching PySide6 GUI...")
        if self.debug:
            print("Debug mode enabled. Additional logging will be shown.")
        if self.theme:
            print(f"Theme set to: {self.theme}")
        launch_gui()

class CommandParser:
    """Parser for CLI commands."""
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Phone Records Analyzer CLI")
        self.subparsers = self.parser.add_subparsers(dest="command")

        # Analyze command
        analyze_parser = self.subparsers.add_parser("analyze", help="Analyze phone records")
        analyze_parser.add_argument("file_path", type=str, help="Path to the phone records file")

        # Export command
        export_parser = self.subparsers.add_parser("export", help="Export analysis results")
        export_parser.add_argument("file_path", type=str, help="Path to the phone records file")
        export_parser.add_argument("--format", type=str, choices=["csv", "json"], default="csv", help="Export format")

        # GUI command
        gui_parser = self.subparsers.add_parser("gui", help="Launch the PySide6 GUI")
        gui_parser.add_argument("--theme", type=str, choices=["light", "dark", "system"],
                              help="Set the GUI theme (light, dark, or system)")
        gui_parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    def parse(self, args: List[str]) -> Command:
        parsed_args = self.parser.parse_args(args)
        if parsed_args.command == "analyze":
            return AnalyzeCommand(parsed_args.file_path)
        elif parsed_args.command == "export":
            return ExportCommand(parsed_args.file_path, parsed_args.format)
        elif parsed_args.command == "gui":
            return GuiCommand(theme=parsed_args.theme, debug=parsed_args.debug)
        else:
            raise ValueError(f"Unknown command: {parsed_args.command}")
