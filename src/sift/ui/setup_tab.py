'''
Sift UI: setup tab
'''

# -- Import external dependencies --
from pathlib import Path
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# -- Import internal configuration classes --
from sift.config import AppConfig, Destination, Filters

# -- Import internal scanner function --
from sift.scanner import scan

# -- SetupTab: class to define the structure of the setup tab panels
class SetupTab(QWidget):
    config_changed = Signal()
    # Initialise QWidget
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        root = QVBoxLayout(self)
        root.addWidget(self._build_upper_panel(), stretch=1)
        root.addWidget(self._build_lower_panel(), stretch=1)
        self._load_from_config()
        self._refresh_count()
    # _build_upper_panel: construct the upper panel of setup tab (source selection and filtering)
    def _build_upper_panel(self) -> QWidget:
        box = QGroupBox('Source Files and Filters')
        row = QHBoxLayout(box)
        # LHS: source selection
        left = QVBoxLayout()
        self.recursive_check = QCheckBox('Search directories recursively')
        self.recursive_check.setChecked(self.config.recursive)
        self.recursive_check.toggled.connect(self._on_recursive_toggled)
        btn_dir = QPushButton('Add directory...')
        btn_dir.clicked.connect(self._pick_directory)
        btn_files = QPushButton('Add files...')
        btn_files.clicked.connect(self._pick_files)
        btn_clear = QPushButton('Clear sources')
        btn_clear.clicked.connect(self._clear_sources)
        self.source_list = QListWidget()
        left.addWidget(self.recursive_check)
        left.addWidget(btn_dir)
        left.addWidget(btn_files)
        left.addWidget(btn_clear)
        left.addWidget(QLabel('Selected sources:'))
        left.addWidget(self.source_list, stretch=1)
        # RHS: filters
        right = QVBoxLayout()
        right.addWidget(QLabel('Extensions (comma separated, blank = all):'))
        self.ext_input = QLineEdit()
        self.ext_input.setPlaceholderText('jpg, png, mp4')
        self.ext_input.editingFinished.connect(self._on_filter_changed)
        right.addWidget(self.ext_input)
        self.count_label = QLabel('Files matched: 0')
        self.count_label.setStyleSheet('font-size: 18px; font-weight: 600;')
        right.addWidget(self.count_label)
        right.addStretch(1)
        row.addLayout(left, stretch=1)
        row.addLayout(right, stretch=1)
        return box

    # _build_lower_panel: construct the upper panel of setup tab (source selection and filtering)
    def _build_lower_panel(self) -> QWidget:
        box = QGroupBox('Destinations')
        layout = QVBoxLayout(box)
        controls = QHBoxLayout()
        btn_add = QPushButton('Add destination...')
        btn_add.clicked.connect(self._add_destination)
        btn_remove = QPushButton('Remove selected')
        btn_remove.clicked.connect(self._remove_destination)
        controls.addWidget(btn_add)
        controls.addWidget(btn_remove)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(['Key', 'Path'])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.itemChanged.connect(self._on_table_edited)
        layout.addWidget(self.table)
        return box

    # _load_from_config: load setup tab from configuration file
    def _load_from_config(self) -> None:
        self.ext_input.setText(', '.join(self.config.filters.extensions))
        for src in self.config.source_paths:
            self.source_list.addItem(src)
        self.table.blockSignals(True)
        for dest in self.config.destinations:
            self._append_row(dest.key, dest.path)
        self.table.blockSignals(False)

    # _persist: save setup tab to configuration file
    def _persist(self) -> None:
        self.config.save()
        self.config_changed.emit()

    # _pick_directory: allow user to select a directory
    def _pick_directory(self) -> None:
        path = QFileDialog.getExistingDirectory(self, 'Choose a directory')
        if path:
            self.config.source_paths.append(path)
            self.source_list.addItem(path)
            self._persist()
            self._refresh_count()

    # _pick_files: allow user to select files
    def _pick_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, 'Choose files')
        for p in paths:
            self.config.source_paths.append(p)
            self.source_list.addItem(p)
        if paths:
            self._persist()
            self._refresh_count()

    # _clear_sources: clear source list
    def _clear_sources(self) -> None:
        self.config.source_paths.clear()
        self.source_list.clear()
        self._persist()
        self._refresh_count()

    # _on_recursive_toggled: apply recursive toggle functionality
    def _on_recursive_toggled(self, checked: bool) -> None:
        self.config.recursive = checked
        self._persist()
        self._refresh_count()

    # _on_filter_changed: apply filter logic
    def _on_filter_changed(self) -> None:
        raw = [p.strip() for p in self.ext_input.text().split(',')]
        self.config.filters = Filters(extensions=[p for p in raw if p])
        self._persist()
        self._refresh_count()

    # _refresh_count: refresh file count
    def _refresh_count(self) -> None:
        files = scan(
            [Path(p) for p in self.config.source_paths],
            recursive=self.config.recursive,
            extensions=self.config.filters.normalised(),
        )
        self.count_label.setText(f'Files matched: {len(files)}')

    # _append_row: add a row to the destinations table
    def _append_row(self, key: str, path: str) -> None:
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem(key))
        self.table.setItem(r, 1, QTableWidgetItem(path))

    # _add_destination: add a destination to the destinations table
    def _add_destination(self) -> None:
        path = QFileDialog.getExistingDirectory(self, 'Choose a destination')
        if not path:
            return
        key = Path(path).name or path
        self.table.blockSignals(True)
        self._append_row(key, path)
        self.table.blockSignals(False)
        self._sync_destinations_from_table()

    # _remove_destination: remove a destination from the destinations table
    def _remove_destination(self) -> None:
        rows = sorted(
            {i.row() for i in self.table.selectedIndexes()}, reverse=True
        )
        for r in rows:
            self.table.removeRow(r)
        self._sync_destinations_from_table()

    # _on_table_edited: on table being edited, call sync destinations
    def _on_table_edited(self, _item: QTableWidgetItem) -> None:
        self._sync_destinations_from_table()

    # _sync_destinations_from_table: sync destinations from destinations table to config
    def _sync_destinations_from_table(self) -> None:
        dests: list[Destination] = []
        for r in range(self.table.rowCount()):
            key_item = self.table.item(r, 0)
            path_item = self.table.item(r, 1)
            key = key_item.text().strip() if key_item else ''
            path = path_item.text().strip() if path_item else ''
            if key and path:
                dests.append(Destination(key=key, path=path))
        self.config.destinations = dests
        self._persist()
