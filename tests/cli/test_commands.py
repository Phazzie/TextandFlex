import pytest
from src.cli.commands import CommandParser, AnalyzeCommand, ExportCommand

def test_command_parsing():
    parser = CommandParser()
    
    # Test valid commands
    analyze_command = parser.parse(["analyze", "sample.xlsx"])
    assert isinstance(analyze_command, AnalyzeCommand)
    assert analyze_command.file_path == "sample.xlsx"
    
    export_command = parser.parse(["export", "sample.xlsx", "--format", "json"])
    assert isinstance(export_command, ExportCommand)
    assert export_command.file_path == "sample.xlsx"
    assert export_command.format == "json"
    
    # Test invalid command
    with pytest.raises(ValueError):
        parser.parse(["invalid_command"])

def test_argument_handling():
    parser = CommandParser()
    
    # Test required arguments
    with pytest.raises(ValueError):
        parser.parse(["analyze"])
    
    # Test optional arguments
    export_command = parser.parse(["export", "sample.xlsx"])
    assert export_command.format == "csv"  # Default format

def test_error_handling():
    parser = CommandParser()
    
    # Test invalid arguments
    with pytest.raises(ValueError):
        parser.parse(["analyze", "sample.xlsx", "--invalid-arg"])
    
    # Test missing command
    with pytest.raises(ValueError):
        parser.parse([])
