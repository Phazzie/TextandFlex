import pytest
from src.cli.interactive import InteractiveCLI

def test_repl_functionality():
    cli = InteractiveCLI()
    
    # Test command input and output
    output = cli.execute_command("help")
    assert "Available commands" in output
    
    output = cli.execute_command("exit")
    assert "Exiting" in output

def test_command_history():
    cli = InteractiveCLI()
    
    # Test adding commands to history
    cli.execute_command("help")
    cli.execute_command("exit")
    
    history = cli.get_command_history()
    assert len(history) == 2
    assert history[0] == "help"
    assert history[1] == "exit"
    
    # Test clearing history
    cli.clear_command_history()
    history = cli.get_command_history()
    assert len(history) == 0

def test_tab_completion():
    cli = InteractiveCLI()
    
    # Test command completion
    completions = cli.complete_command("he")
    assert "help" in completions
    
    completions = cli.complete_command("ex")
    assert "exit" in completions
    
    # Test argument completion
    completions = cli.complete_command("export --f")
    assert "--format" in completions
