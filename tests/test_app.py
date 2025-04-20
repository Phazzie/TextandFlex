import pytest
from src.app import main
from src.config import ConfigManager
from src.cli.commands import CommandParser

def test_command_routing_valid_command(mocker):
    mocker.patch('src.cli.commands.CommandParser.parse', return_value=('analyze', {'file': 'sample.xlsx'}))
    mocker.patch('src.app.analyze_file', return_value=True)
    result = main()
    assert result == 0

def test_command_routing_invalid_command(mocker):
    mocker.patch('src.cli.commands.CommandParser.parse', return_value=('invalid_command', {}))
    result = main()
    assert result == 1

def test_configuration_integration_loading(mocker):
    mock_config = ConfigManager()
    mock_config.set('data.excel.required_columns', ['timestamp', 'phone_number'])
    mocker.patch('src.config.ConfigManager', return_value=mock_config)
    config = ConfigManager()
    assert config.get('data.excel.required_columns') == ['timestamp', 'phone_number']

def test_configuration_integration_applying(mocker):
    mock_config = ConfigManager()
    mock_config.set('data.excel.required_columns', ['timestamp', 'phone_number'])
    mocker.patch('src.config.ConfigManager', return_value=mock_config)
    config = ConfigManager()
    assert config.get('data.excel.required_columns') == ['timestamp', 'phone_number']

def test_end_to_end_cli_workflow_analyze(mocker):
    mocker.patch('src.cli.commands.CommandParser.parse', return_value=('analyze', {'file': 'sample.xlsx'}))
    mocker.patch('src.app.analyze_file', return_value=True)
    result = main()
    assert result == 0

def test_end_to_end_cli_workflow_export(mocker):
    mocker.patch('src.cli.commands.CommandParser.parse', return_value=('export', {'file': 'sample.xlsx', 'format': 'csv'}))
    mocker.patch('src.app.export_file', return_value=True)
    result = main()
    assert result == 0
