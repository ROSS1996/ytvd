# main.py

import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from modules.download_manager import DownloadManager
from modules.main_window import BrowserWindow

def main():
    # Cria a instância da aplicação
    app = QApplication(sys.argv)

    # Verifica a conexão com a internet antes de iniciar a aplicação
    if not DownloadManager.is_internet_connected():
        QMessageBox.critical(None, "Sem Conexão com a Internet", "Você não está conectado à internet.")
        return  # Sai se não houver conexão com a internet

    # Cria e mostra a janela principal da aplicação
    window = BrowserWindow()
    window.showMaximized()  # Usa showMaximized() aqui

    # Inicia o loop de eventos
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
