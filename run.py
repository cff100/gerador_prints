"""
Ponto de entrada do Gerador Automático de Prints de Vídeo.
"""
import sys
import os

# Garante que o diretório raiz esteja no sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.gui.app import MainWindow

def main():
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()

