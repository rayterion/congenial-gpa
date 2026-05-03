from apps.db_cli import DatabaseCLI

class CLIMockTerminal:
    def __init__(self):
        self.logs = []

    def run_cli_command(self, command):
        """ Run a cli command and return its response. """
        cli = DatabaseCLI(terminal=self)
        cli.store_cell(command)
    
    def log(self, text):
        """ integrated log for the cli to send output to the terminal. """
        self.logs.append(text)
    
    def clear_logs(self):
        """ Clear the terminal logs. """
        self.logs = []
    
    def get_logs(self):
        """ Get the current logs from the terminal. """
        return self.logs