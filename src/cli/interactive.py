import cmd
import readline
import os

class InteractiveCLI(cmd.Cmd):
    intro = "Welcome to the Phone Records Analyzer CLI. Type help or ? to list commands.\n"
    prompt = "(analyzer) "

    def __init__(self):
        super().__init__()
        self.command_history = []
        self.history_file = os.path.expanduser("~/.textymctextface_history")
        self.load_command_history()

    def do_analyze(self, arg):
        "Analyze phone records: analyze <file_path>"
        print(f"Analyzing file: {arg}")
        # Add analysis logic here

    def do_export(self, arg):
        "Export analysis results: export <file_path> [--format=csv|json]"
        print(f"Exporting file: {arg}")
        # Add export logic here

    def do_exit(self, arg):
        "Exit the interactive CLI"
        print("Exiting")
        return True

    def do_help(self, arg):
        "List available commands with 'help' or detailed help with 'help <command>'"
        super().do_help(arg)

    def default(self, line):
        print(f"Unknown command: {line}")

    def precmd(self, line):
        self.command_history.append(line)
        self.save_command_history()
        return line

    def load_command_history(self):
        if os.path.exists(self.history_file):
            readline.read_history_file(self.history_file)

    def save_command_history(self):
        readline.write_history_file(self.history_file)

    def get_command_history(self):
        return self.command_history

    def clear_command_history(self):
        self.command_history = []
        open(self.history_file, 'w').close()

    def complete_export(self, text, line, begidx, endidx):
        options = ['--format=csv', '--format=json']
        if not text:
            return options
        return [option for option in options if option.startswith(text)]

if __name__ == '__main__':
    InteractiveCLI().cmdloop()
