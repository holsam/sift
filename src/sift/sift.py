'''
Sift: entrypoint
'''

# -- Import external dependencies --
import sys
from PySide6.QtWidgets import QApplication

# -- Import internal UI components --
from sift.ui.main_window import MainWindow

# -- main: launch the Sift UI main window, returning exit code as int --
def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
