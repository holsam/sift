'''
Sift UI: main window
'''

# -- Import external dependencies --
from PySide6.QtWidgets import QMainWindow, QTabWidget

# -- Import internal configuration classes --
from sift.config import AppConfig

# -- Import internal UI elements --
from sift.ui.setup_tab import SetupTab
from sift.ui.sort_tab import SortTab

# -- MainWindow: class to hold the main window set up
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        # Initialise window and set title/size
        super().__init__()
        self.config = AppConfig.load()
        self.setWindowTitle('Sift')
        self.resize(1200, 800)
        # Set up tab widget and set this as central widget on main window
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        # Initialise setup and sort tabs
        self.setup_tab = SetupTab(self.config)
        self.sort_tab = SortTab(self.config)
        # Add tabs to the tab widget for set up and sorting tabs
        self.tabs.addTab(self.setup_tab, 'Setup')
        self.tabs.addTab(self.sort_tab, 'Sort')