'''
Sift UI: icons for buttons (loaded from sprite sheet with Qt fallbacks)
'''

# -- Import external dependencies --
from pathlib import Path
from PySide6.QtCore import QRect
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QStyle, QWidget

# -- Sprite sheet layout: one row of 64x64 cells, in this fixed order --
ICON_NAMES = [
    'add_folder',
    'add_file',
    'clear_list',
    'add_destination',
    'remove_destination',
    'clear_filter',
]
CELL_SIZE = 64
SHEET_PATH = Path(__file__).resolve().parent.parent.parent / 'assets' / 'icons' / 'setup_icons.png'

# -- Fallback Qt standard icons, used until the sprite sheet exists --
_FALLBACKS = {
    'add_folder': QStyle.StandardPixmap.SP_DirIcon,
    'add_file': QStyle.StandardPixmap.SP_FileIcon,
    'clear_list': QStyle.StandardPixmap.SP_DialogResetButton,
    'add_destination': QStyle.StandardPixmap.SP_DirLinkIcon,
    'remove_destination': QStyle.StandardPixmap.SP_TrashIcon,
    'clear_filter': QStyle.StandardPixmap.SP_LineEditClearButton,
}

_sheet_cache: QPixmap | None = None

# -- _sheet: load and cache the sprite sheet pixmap (may be null if missing) --
def _sheet() -> QPixmap:
    global _sheet_cache
    if _sheet_cache is None:
        _sheet_cache = QPixmap(str(SHEET_PATH))
    return _sheet_cache

# -- icon: return a QIcon for name, cropped from the sprite sheet if present, else a Qt standard icon --
def icon(name: str, widget: QWidget) -> QIcon:
    if name not in ICON_NAMES:
        raise ValueError(f'Unknown icon name: {name}')
    sheet = _sheet()
    if not sheet.isNull():
        index = ICON_NAMES.index(name)
        rect = QRect(index * CELL_SIZE, 0, CELL_SIZE, CELL_SIZE)
        return QIcon(sheet.copy(rect))
    return widget.style().standardIcon(_FALLBACKS[name])