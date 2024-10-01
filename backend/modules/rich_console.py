# rich_console.py

from rich.console import Console
from rich.progress import Progress

class RichConsole:
    def __init__(self):
        self.console = Console()

    def print_info(self, message):
        """Imprime uma mensagem de informação em azul."""
        self.console.print(f"[bold blue]{message}[/bold blue]")

    def print_warning(self, message):
        """Imprime uma mensagem de aviso em amarelo."""
        self.console.print(f"[bold yellow]{message}[/bold yellow]")

    def print_error(self, message):
        """Imprime uma mensagem de erro em vermelho."""
        self.console.print(f"[bold red]{message}[/bold red]")

    def print_success(self, message):
        """Imprime uma mensagem de sucesso em verde."""
        self.console.print(f"[bold green]{message}[/bold green]")

    def start_progress(self, total):
        """Inicia uma barra de progresso."""
        self.progress = Progress()
        self.task = self.progress.add_task("Baixando...", total=total)
        self.progress.start()

    def update_progress(self, completed):
        """Atualiza a barra de progresso."""
        self.progress.update(self.task, completed=completed)

    def stop_progress(self):
        """Para a barra de progresso."""
        self.progress.stop()
