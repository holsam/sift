'''
Sift UI: icons for buttons
'''

# -- Import external dependencies --
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QStyle, QWidget

# -- ICONS: define dictionary for icons from Qt --
ICONS = {
    'add_folder': QStyle.StandardPixmap.SP_DirIcon,
    'add_file': QStyle.StandardPixmap.SP_FileIcon,
    'clear_list': QStyle.StandardPixmap.SP_DialogResetButton,
    'add_destination': QStyle.StandardPixmap.SP_DirLinkIcon,
    'remove_destination': QStyle.StandardPixmap.SP_TrashIcon,
    'clear_filter': QStyle.StandardPixmap.SP_LineEditClearButton,
}

# -- icon: return the icon from the ICONS dictionary for a given name --
def icon(name: str, widget: QWidget) -> QIcon:
    if name not in ICONS.keys():
        raise ValueError(f'Unknown icon: {name!r}')
    return widget.style().standardIcon(ICONS[name])