'''
Sift UI: main window
'''

# -- Import external dependencies --
from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget

# -- MainWindow: class to hold the main window set up
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        # Initialise window and set title/size
        super().__init__()
        self.setWindowTitle('Sift')
        self.resize(1200, 800)
        # Set up tab widget and set this as central widget on main window
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        # Add tabs to the tab widget for set up and sorting tabs
        self.tabs.addTab(QWidget(), 'Setup')
        self.tabs.addTab(QWidget(), 'Sort')