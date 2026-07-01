'''
Sift UI: setup tab
'''

# -- Import external dependencies --
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# -- Import internal classes --
from sift.config import AppConfig, Destination, Filters
from sift.ui.utils.toggle import ToggleSwitch

# -- Import internal scanner function --
from sift.scanner import scan

# -- SetupTab: class to define the structure of the setup tab panels --
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
        recursive_row = QHBoxLayout()
        self.recursive_check = ToggleSwitch()
        self.recursive_check.setChecked(self.config.recursive)
        self.recursive_check.toggled.connect(self._on_recursive_toggled)
        recursive_row.addWidget(QLabel('Search directories recursively'))
        recursive_row.addWidget(self.recursive_check)
        recursive_row.addStretch(1)
        left.addLayout(recursive_row)
        btn_dir = QPushButton('Add directory...')
        btn_dir.clicked.connect(self._pick_directory)
        btn_files = QPushButton('Add files...')
        btn_files.clicked.connect(self._pick_files)
        btn_clear = QPushButton('Clear sources')
        btn_clear.clicked.connect(self._clear_sources)
        self.source_list = QListWidget()
        left.addWidget(btn_dir)
        left.addWidget(btn_files)
        left.addWidget(btn_clear)
        left.addWidget(QLabel('Selected sources:'))
        left.addWidget(self.source_list, stretch=1)
        # RHS: filters
        right = QVBoxLayout()
        form = QFormLayout()
        # Add file extenstion filters
        self.ext_input = QLineEdit()
        self.ext_input.setPlaceholderText('jpg, png, mp4')
        self.ext_input.editingFinished.connect(self._on_filter_changed)
        form.addRow('Filter for file extensions (blank = all):', self.ext_input)
        # Add file name glob filters
        self.glob_input = QLineEdit()
        self.glob_input.setPlaceholderText('*pattern*')
        self.glob_input.editingFinished.connect(self._on_filter_changed)
        form.addRow('Filter for file names matching glob:', self.glob_input)
        # Add file name glob filters
        self.regex_input = QLineEdit()
        self.regex_input.setPlaceholderText(r"\d{4}-\d{2}-\d{2}")
        self.regex_input.editingFinished.connect(self._on_filter_changed)
        form.addRow('Filters for files matching regex:', self.regex_input)
        # Add size filters
        self.min_size = QSpinBox()
        self.min_size.setRange(0, 1_000_000)
        self.min_size.setSuffix(' MB')
        self.min_size.valueChanged.connect(self._on_filter_changed)
        form.addRow('Filter for minimum file size:', self.min_size)
        self.max_size = QSpinBox()
        self.max_size.setRange(0, 1_000_000)   # 0 = no maximum
        self.max_size.setSuffix(' MB')
        self.max_size.setSpecialValueText('none')
        self.max_size.valueChanged.connect(self._on_filter_changed)
        form.addRow('Filter for maximum file size:', self.max_size)
        # Add date filters
        self.date_before = QDateEdit()
        self.date_before.setCalendarPopup(True)
        self.date_before.setSpecialValueText('none')
        self.date_before.setMinimumDate(QDate(2000, 1, 1))
        self.date_before.setDate(self.date_before.minimumDate())
        self.date_before.dateChanged.connect(self._on_filter_changed)
        form.addRow('Filter for files modified before:', self.date_before)
        self.date_after = QDateEdit()
        self.date_after.setCalendarPopup(True)
        self.date_after.setSpecialValueText('none')
        self.date_after.setMinimumDate(QDate(2000, 1, 1))
        self.date_after.setDate(self.date_after.minimumDate())
        self.date_after.dateChanged.connect(self._on_filter_changed)
        form.addRow('Filter for files modified after:', self.date_after)
        # Add form of filters to RHS and add count
        right.addLayout(form)
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
        f = self.config.filters
        self.ext_input.setText(', '.join(f.extensions))
        self.glob_input.setText(f.name_glob or '')
        self.regex_input.setText(f.name_regex or '')
        if f.min_size:
            self.min_size.setValue(f.min_size // 1_000_000)
        if f.max_size:
            self.max_size.setValue(f.max_size // 1_000_000)
        if f.modified_after:
            self.date_after.setDate(QDate(f.modified_after.date()))
        if f.modified_before:
            self.date_before.setDate(QDate(f.modified_before.date()))
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
        raw = [p.strip() for p in self.ext_input.text().split(",")]
        min_mb = self.min_size.value()
        max_mb = self.max_size.value()
        after = self.date_after.date()
        before = self.date_before.date()
        floor = self.date_after.minimumDate()
        self.config.filters = Filters(
            extensions=[p for p in raw if p],
            name_glob=self.glob_input.text().strip() or None,
            name_regex=self.regex_input.text().strip() or None,
            min_size=min_mb * 1_000_000 if min_mb else None,
            max_size=max_mb * 1_000_000 if max_mb else None,
            modified_after=(
                datetime(after.year(), after.month(), after.day())
                if after != floor
                else None
            ),
            modified_before=(
                datetime(before.year(), before.month(), before.day(), 23, 59, 59)
                if before != floor
                else None
            ),
        )
        self._persist()
        self._refresh_count()

    # _refresh_count: refresh file count
    def _refresh_count(self) -> None:
        files = scan(
            [Path(p) for p in self.config.source_paths],
            recursive=self.config.recursive,
            filters=self.config.filters,
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
