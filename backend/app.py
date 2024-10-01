import sys
import ctypes
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon  # Import QIcon
from modules.download_manager import DownloadManager
from modules.main_window import BrowserWindow

def main():
    # Set the application ID for Windows taskbar
    myappid = 'ytvd.01102024'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # Cria a instância da aplicação
    app = QApplication(sys.argv)

    # Define o ícone da aplicação
    app.setWindowIcon(QIcon('icon.ico'))  # Set the application icon

    # Verifica a conexão com a internet antes de iniciar a aplicação
    if not DownloadManager.is_internet_connected():
        QMessageBox.critical(None, "Sem Conexão com a Internet", "Você não está conectado à internet.")
        return  # Sai se não houver conexão com a internet

    # Cria e mostra a janela principal da aplicação
    window = BrowserWindow()

    # Define o ícone da janela principal
    window.setWindowIcon(QIcon('icon.ico'))  # Set the main window icon

    window.showMaximized()  # Usa showMaximized() aqui

    # Conecta o evento de fechamento da janela à saída da aplicação
    window.closeEvent = lambda event: app.quit()  # Ensure app quits on close

    # Inicia o loop de eventos
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
