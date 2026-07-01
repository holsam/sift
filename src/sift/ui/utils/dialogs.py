'''
Sift UI: dialog panel for selecting directories
'''

# -- Import external dependencies --
from PySide6.QtWidgets import QFileDialog, QWidget

# -- pick_directories: return a selected directory from file dialog (empty list if cancelled)
def pick_directories(parent: QWidget, caption: str = "Select directory") -> list[str]:
    path = QFileDialog.getExistingDirectory(parent, caption)
    return [path] if path else []
