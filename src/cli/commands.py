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
    """Command to launch the Kivy GUI."""
    def execute(self):
        from src.presentation_layer.gui.main_window import MainApp
        MainApp().run()

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
        gui_parser = self.subparsers.add_parser("gui", help="Launch the Kivy GUI")

    def parse(self, args: List[str]) -> Command:
        parsed_args = self.parser.parse_args(args)
        if parsed_args.command == "analyze":
            return AnalyzeCommand(parsed_args.file_path)
        elif parsed_args.command == "export":
            return ExportCommand(parsed_args.file_path, parsed_args.format)
        elif parsed_args.command == "gui":
            return GuiCommand()
        else:
            raise ValueError(f"Unknown command: {parsed_args.command}")
