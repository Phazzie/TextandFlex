"""
Integration tests for the CLI and GUI integration.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

from src.cli.commands import CommandParser, GuiCommand
from src.app import launch_gui


@pytest.mark.integration
def test_gui_command_parsing():
    """Test parsing the GUI command from the CLI."""
    # Create a command parser
    parser = CommandParser()
    
    # Parse the GUI command
    command = parser.parse(["gui"])
    
    # Verify the command is a GuiCommand
    assert isinstance(command, GuiCommand)
    assert command.theme is None
    assert command.debug is False
    
    # Parse the GUI command with options
    command = parser.parse(["gui", "--theme", "dark", "--debug"])
    
    # Verify the command is a GuiCommand with the correct options
    assert isinstance(command, GuiCommand)
    assert command.theme == "dark"
    assert command.debug is True


@pytest.mark.integration
def test_gui_command_execution():
    """Test executing the GUI command."""
    # Create a GuiCommand
    command = GuiCommand(theme="light", debug=True)
    
    # Mock the launch_gui function
    with patch("src.app.launch_gui") as mock_launch_gui:
        # Execute the command
        command.execute()
        
        # Verify launch_gui was called
        assert mock_launch_gui.called


@pytest.mark.integration
def test_launch_gui_function():
    """Test the launch_gui function."""
    # Mock the importlib.import_module function
    with patch("importlib.import_module") as mock_import_module:
        # Mock the gui_app module
        mock_gui_app = MagicMock()
        mock_import_module.return_value = mock_gui_app
        
        # Call launch_gui
        launch_gui()
        
        # Verify importlib.import_module was called with the correct module name
        mock_import_module.assert_called_with("src.presentation_layer.gui.app")
        
        # Verify gui_app.main was called
        assert mock_gui_app.main.called


@pytest.mark.integration
def test_launch_gui_error_handling():
    """Test error handling in the launch_gui function."""
    # Mock the importlib.import_module function to raise an exception
    with patch("importlib.import_module") as mock_import_module:
        mock_import_module.side_effect = ImportError("Module not found")
        
        # Mock the logger
        with patch("src.app.logger") as mock_logger:
            # Call launch_gui
            launch_gui()
            
            # Verify logger.error was called
            assert mock_logger.error.called
            assert "Failed to launch GUI" in mock_logger.error.call_args[0][0]


@pytest.mark.integration
def test_gui_command_with_missing_dependencies():
    """Test the GUI command with missing dependencies."""
    # Create a GuiCommand
    command = GuiCommand()
    
    # Mock the importlib.import_module function
    with patch("importlib.import_module") as mock_import_module:
        # Mock the import of PySide6 to raise an ImportError
        with patch("src.app.importlib.import_module") as mock_app_import:
            def side_effect(module_name):
                if module_name == "PySide6":
                    raise ImportError("No module named 'PySide6'")
                return MagicMock()
            
            mock_app_import.side_effect = side_effect
            
            # Mock the logger
            with patch("src.app.logger") as mock_logger:
                # Execute the command
                command.execute()
                
                # Verify logger.error was called
                assert mock_logger.error.called
                assert "Missing required package" in mock_logger.error.call_args[0][0]
