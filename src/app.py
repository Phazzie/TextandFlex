"""
Phone Analyzer Application
-----------------------
Main application entry point.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from .data_layer.excel_parser import ExcelParser
from .data_layer.repository import PhoneRecordRepository
from .analysis_layer.basic_statistics import BasicStatisticsAnalyzer
from .logger import app_logger as logger
from .config import ConfigManager
from .cli.commands import CommandParser, AnalyzeCommand, ExportCommand, GuiCommand

def main():
    """Main application entry point."""
    logger.info("Starting Phone Analyzer application")

    # Load configuration
    config = ConfigManager()
    config.load_from_env()

    # Initialize components
    parser = ExcelParser()
    repository = PhoneRecordRepository()
    analyzer = BasicStatisticsAnalyzer()
    command_parser = CommandParser()

    # Parse command-line arguments
    command = command_parser.parse(sys.argv[1:])

    if isinstance(command, AnalyzeCommand):
        analyze_file(command.file_path, parser, repository, analyzer)
    elif isinstance(command, ExportCommand):
        export_file(command.file_path, command.format, repository)
    elif isinstance(command, GuiCommand):
        launch_gui()
    else:
        logger.error(f"Unknown command: {command}")
        return 1

    return 0

def analyze_file(file_path: str, parser: ExcelParser, repository: PhoneRecordRepository, analyzer: BasicStatisticsAnalyzer):
    """Analyze a phone records file."""
    logger.info(f"Analyzing file: {file_path}")

    # Parse file
    df, mapping, error = parser.parse_and_detect(file_path)

    if df is not None:
        logger.info(f"Parsed file with {len(df)} records")
        logger.info(f"Detected column mapping: {mapping}")

        # Add to repository
        if repository.add_dataset("sample", df, mapping):
            logger.info("Added dataset to repository")

            # Analyze data
            stats, error = analyzer.analyze(df, mapping)

            if stats:
                logger.info("Analysis complete")
                logger.info(f"Total records: {stats.total_records}")

                if stats.date_range:
                    logger.info(f"Date range: {stats.date_range.start} to {stats.date_range.end} ({stats.date_range.days} days)")

                if stats.top_contacts:
                    logger.info(f"Top contact: {stats.top_contacts[0].number} ({stats.top_contacts[0].count} records, {stats.top_contacts[0].percentage:.2f}%)")
            else:
                logger.error(f"Analysis failed: {error}")
        else:
            logger.error(f"Failed to add dataset: {repository.last_error}")
    else:
        logger.error(f"Failed to parse file: {error}")

def export_file(file_path: str, format: str, repository: PhoneRecordRepository):
    """Export analysis results to a file."""
    logger.info(f"Exporting file: {file_path} to format: {format}")
    # Add export logic here

def launch_gui():
    """Launch the new PySide6 GUI."""
    import importlib
    import traceback
    from pathlib import Path

    try:
        # Check if required dependencies are installed
        try:
            import PySide6
            import pandas
            import matplotlib
        except ImportError as e:
            missing_package = str(e).split("'")
            if len(missing_package) > 1:
                package_name = missing_package[1]
                logger.error(f"Missing required package: {package_name}")
                print(f"Error: Missing required package: {package_name}")
                print(f"Please install it using: pip install {package_name}")
            else:
                logger.error(f"Missing required package: {e}")
                print(f"Error: Missing required package. Please install required packages.")
            return

        # Check if GUI module exists
        gui_module_path = Path(__file__).parent / 'presentation_layer' / 'gui' / 'app.py'
        if not gui_module_path.exists():
            logger.error(f"GUI module not found at {gui_module_path}")
            print(f"Error: GUI module not found. Please ensure the application is properly installed.")
            return

        # Import and launch GUI
        gui_app = importlib.import_module('src.presentation_layer.gui.app')
        logger.info("Launching GUI application")
        gui_app.main()

    except Exception as exc:
        logger.error(f"Failed to launch GUI: {exc}")
        logger.error(traceback.format_exc())
        print("Failed to launch GUI. See logs for details.")
        print(f"Error: {exc}")

if __name__ == "__main__":
    main()
