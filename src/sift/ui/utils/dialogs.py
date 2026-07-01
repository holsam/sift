'''
Sift UI: dialog panel for selecting directories
'''

# -- Import external dependencies --
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QListView,
    QTreeView,
    QWidget,
)

# -- pick_directories: return one or more selected directories from file dialog (empty list if cancelled)
def pick_directories(parent: QWidget, caption: str = 'Select directories') -> list[str]:
    dialog = QFileDialog(parent, caption)
    dialog.setFileMode(QFileDialog.FileMode.Directory)
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
    for view in dialog.findChildren(QListView) + dialog.findChildren(QTreeView):
        view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    if dialog.exec():
        return dialog.selectedFiles()
    return []