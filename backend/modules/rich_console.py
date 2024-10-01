# rich_console.py

from rich.console import Console
from rich.progress import Progress

class RichConsole:
    def __init__(self):
        self.console = Console()

    def print_info(self, message):
        """Prints an info message in blue."""
        self.console.print(f"[bold blue]{message}[/bold blue]")

    def print_warning(self, message):
        """Prints a warning message in yellow."""
        self.console.print(f"[bold yellow]{message}[/bold yellow]")

    def print_error(self, message):
        """Prints an error message in red."""
        self.console.print(f"[bold red]{message}[/bold red]")

    def print_success(self, message):
        """Prints a success message in green."""
        self.console.print(f"[bold green]{message}[/bold green]")

    def start_progress(self, total):
        """Starts a progress bar."""
        self.progress = Progress()
        self.task = self.progress.add_task("Downloading...", total=total)
        self.progress.start()

    def update_progress(self, completed):
        """Updates the progress bar."""
        self.progress.update(self.task, completed=completed)

    def stop_progress(self):
        """Stops the progress bar."""
        self.progress.stop()
