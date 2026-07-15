'''
Sift UI: setup tab
'''

# -- Import external dependencies --
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QDate, QSize, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QColorDialog,
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
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

# -- Import internal functions --
from sift.scanner import filter_files, walk_files
from sift.mover import paths_overlap
from sift.ui.utils.dialogs import pick_directories
from sift.ui.utils.icons import icon

# -- SetupTab: class to define the structure of the setup tab panels --
class SetupTab(QWidget):
    config_changed = Signal()
    # Initialise QWidget
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        layout = QVBoxLayout(self)
        upper_panel = QHBoxLayout()
        file_panels = QVBoxLayout()
        file_panels.addWidget(self._build_filters_panel(), stretch=1)
        file_panels.addWidget(self._build_count_panel(), stretch=1)
        upper_panel.addWidget(self._build_sources_panel(), stretch=1)
        upper_panel.addLayout(file_panels)
        layout.addLayout(upper_panel)
        layout.addWidget(self._build_lower_panel(), stretch=1)
        self._load_from_config()
        self._refresh_count()

    # _build_upper_panel: construct the upper panel of setup tab (source selection and filtering)
    def _build_sources_panel(self) -> QWidget:
        box = QGroupBox('Source Files')
        layout = QVBoxLayout(box)
        btn_dir = QPushButton()
        btn_dir.setIcon(icon('add_folder', self))
        btn_dir.setToolTip('Add directory')
        btn_dir.clicked.connect(self._pick_directory)
        btn_files = QPushButton()
        btn_files.setIcon(icon('add_file', self))
        btn_files.setToolTip('Add files')
        btn_files.clicked.connect(self._pick_files)
        btn_clear = QPushButton()
        btn_clear.setIcon(icon('clear_list', self))
        btn_clear.setToolTip('Clear sources')
        btn_clear.clicked.connect(self._clear_sources)
        for b in (btn_dir, btn_files, btn_clear):
            b.setIconSize(QSize(20, 20))
        src_tools_row = QHBoxLayout()
        src_tools_row.addWidget(btn_dir)
        src_tools_row.addWidget(btn_files)
        src_tools_row.addWidget(btn_clear)
        self.recursive_check = ToggleSwitch()
        self.recursive_check.setChecked(self.config.recursive)
        self.recursive_check.toggled.connect(self._on_recursive_toggled)
        src_tools_row.addStretch(1)
        src_tools_row.addWidget(QLabel('Search directories recursively'))
        src_tools_row.addWidget(self.recursive_check)
        self.source_list = QListWidget()
        layout.addLayout(src_tools_row)
        layout.addWidget(QLabel('Selected sources:'))
        layout.addWidget(self.source_list, stretch=1)
        return box

# _build_upper_panel: construct the upper panel of setup tab (source selection and filtering)
    def _build_filters_panel(self) -> QWidget:
        box = QGroupBox('Filters')
        layout = QVBoxLayout(box)
        form = QFormLayout()
        # Add file extenstion filters
        self.ext_input = QLineEdit()
        self.ext_input.setPlaceholderText('jpg, png, mp4')
        self.ext_input.editingFinished.connect(self._on_filter_changed)
        form.addRow('Filter for file extensions (blank = all):', self._row_with_clear(self.ext_input, 'Clear filter', self._clear_ext))
        # Add file name glob filters
        self.glob_input = QLineEdit()
        self.glob_input.setPlaceholderText('*pattern*')
        self.glob_input.editingFinished.connect(self._on_filter_changed)
        form.addRow('Filter for file names matching glob:', self._row_with_clear(self.glob_input, 'Clear filter', self._clear_glob))
        # Add file name glob filters
        self.regex_input = QLineEdit()
        self.regex_input.setPlaceholderText(r"\d{4}-\d{2}-\d{2}")
        self.regex_input.editingFinished.connect(self._on_filter_changed)
        form.addRow('Filters for files matching regex:', self._row_with_clear(self.regex_input, 'Clear filter', self._clear_regex))
        # Add size filters
        self.min_size = QSpinBox()
        self.min_size.setRange(0, 1_000_000)
        self.min_size.setSuffix(' MB')
        self.min_size.valueChanged.connect(self._on_filter_changed)
        form.addRow('Filter for minimum file size:', self._row_with_clear(self.min_size, 'Clear filter', self._clear_min_size))
        self.max_size = QSpinBox()
        self.max_size.setRange(0, 1_000_000)   # 0 = no maximum
        self.max_size.setSuffix(' MB')
        self.max_size.setSpecialValueText('none')
        self.max_size.valueChanged.connect(self._on_filter_changed)
        form.addRow('Filter for maximum file size:', self._row_with_clear(self.max_size, 'Clear filter', self._clear_max_size))
        # Add date filters
        self.date_before = QDateEdit()
        self.date_before.setCalendarPopup(True)
        self.date_before.setSpecialValueText('none')
        self.date_before.setMinimumDate(QDate(2000, 1, 1))
        self.date_before.setDate(self.date_before.minimumDate())
        self.date_before.dateChanged.connect(self._on_filter_changed)
        form.addRow('Filter for files modified before:', self._row_with_clear(self.date_before, 'Clear filter', self._clear_date_before))
        self.date_after = QDateEdit()
        self.date_after.setCalendarPopup(True)
        self.date_after.setSpecialValueText('none')
        self.date_after.setMinimumDate(QDate(2000, 1, 1))
        self.date_after.setDate(self.date_after.minimumDate())
        self.date_after.dateChanged.connect(self._on_filter_changed)
        form.addRow('Filter for files modified after:', self._row_with_clear(self.date_after, 'Clear filter', self._clear_date_after))
        # Add form of filters to RHS
        layout.addLayout(form)
        return box

    # _build_count_panel: construct the file-count panel (total vs matching)
    def _build_count_panel(self) -> QWidget:
        box = QGroupBox('File Counts')
        layout = QHBoxLayout(box)
        self.total_label = QLabel('Total files: 0')
        self.match_label = QLabel('Matching files: 0')
        for lbl in (self.total_label, self.match_label):
            lbl.setStyleSheet('font-size: 18px; font-weight: 600;')
        layout.addWidget(self.total_label)
        layout.addStretch(1)
        layout.addWidget(self.match_label)
        return box

    # _build_lower_panel: construct the upper panel of setup tab (source selection and filtering)
    def _build_lower_panel(self) -> QWidget:
        box = QGroupBox('Destinations')
        layout = QVBoxLayout(box)
        controls = QHBoxLayout()
        btn_add = QPushButton()
        btn_add.setIcon(icon('add_destination', self))
        btn_add.setToolTip('Add destination directory')
        btn_add.clicked.connect(self._add_destination)
        btn_remove = QPushButton()
        btn_remove.setIcon(icon('remove_destination', self))
        btn_remove.setToolTip('Remove selected destination')
        btn_remove.clicked.connect(self._remove_destination)
        for b in (btn_add, btn_remove):
            b.setIconSize(QSize(20, 20))
        controls.addWidget(btn_add)
        controls.addWidget(btn_remove)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(['Key', 'Path', 'Shortcut', 'Colour'])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.itemChanged.connect(self._on_table_edited)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        layout.addWidget(self.table)
        hint = QLabel('Leave Shortcut blank to auto-assign. Double-click a Colour cell to select a colour for terminal output.')
        hint.setStyleSheet('color: #888;')
        layout.addWidget(hint)
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
            self._append_row(dest)
        self.table.blockSignals(False)

    # _persist: save setup tab to configuration file
    def _persist(self) -> None:
        self.config.save()
        self.config_changed.emit()

    # _pick_directory: allow user to select a directory
    def _pick_directory(self) -> None:
        paths = pick_directories(self, 'Choose directories')
        added = False
        for path in paths:
            if self._reject_if_overlaps_destinations(path):
                continue
            self.config.source_paths.append(path)
            self.source_list.addItem(path)
            added = True
        if added:
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

    # _row_with_clear: wrap a filter widget with a small clear button and return as a single widget
    def _row_with_clear(self, field: QWidget, tooltip: str, on_clear) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(field, stretch=1)
        clear_btn = QPushButton()
        clear_btn.setIcon(icon('clear_filter', self))
        clear_btn.setIconSize(QSize(14, 14))
        clear_btn.setFixedWidth(26)
        clear_btn.setToolTip(tooltip)
        clear_btn.clicked.connect(on_clear)
        row.addWidget(clear_btn)
        return container

    # _clear_ext: clear extension filter
    def _clear_ext(self) -> None:
        self.ext_input.clear()
        self._on_filter_changed()

    # _clear_glob: clear glob filter
    def _clear_glob(self) -> None:
        self.glob_input.clear()
        self._on_filter_changed()

    # _clear_regex: clear regex filter
    def _clear_regex(self) -> None:
        self.regex_input.clear()
        self._on_filter_changed()

    # _clear_min_size: clear minimum size filter
    def _clear_min_size(self) -> None:
        self.min_size.setValue(0)

    # _clear_max_size: clear maximum size filter
    def _clear_max_size(self) -> None:
        self.max_size.setValue(0)

    # _clear_date_after: clear modified-after filter
    def _clear_date_after(self) -> None:
        self.date_after.setDate(self.date_after.minimumDate())

    # _clear_date_before: clear modified-before filter
    def _clear_date_before(self) -> None:
        self.date_before.setDate(self.date_before.minimumDate())

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

    # _refresh_count: refresh file counts (total unfiltered vs matching current filters)
    def _refresh_count(self) -> None:
        sources = [Path(p) for p in self.config.source_paths]
        all_files = walk_files(sources, recursive=self.config.recursive)
        matching = filter_files(all_files, self.config.filters)
        self.total_label.setText(f'Total files: {len(all_files)}')
        self.match_label.setText(f'Matching files: {len(matching)}')

    # _append_row: add a row to the destinations table
    def _append_row(self, dest: Destination) -> None:
        from PySide6.QtGui import QColor
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem(dest.key))
        self.table.setItem(r, 1, QTableWidgetItem(dest.path))
        self.table.setItem(r, 2, QTableWidgetItem(dest.shortcut or ''))
        colour_item = QTableWidgetItem(dest.colour or '')
        if dest.colour:
            colour_item.setBackground(QColor(dest.colour))
        self.table.setItem(r, 3, colour_item)

    # _add_destination: add a destination to the destinations table
    def _add_destination(self) -> None:
        paths = pick_directories(self, 'Choose destination directories')
        added = False
        self.table.blockSignals(True)
        for path in paths:
            if self._reject_if_overlaps_sources(path):
                continue
            key = Path(path).name or path
            self._append_row(Destination(key=key, path=path))
            added = True
        self.table.blockSignals(False)
        if added:
            self._sync_destinations_from_table()

    # _on_cell_double_clicked: if a cell is double clicked and it's a Colour cell, select a colour
    def _on_cell_double_clicked(self, row: int, column: int) -> None:
        from PySide6.QtGui import QColor
        if column != 3:
            return
        chosen = QColorDialog.getColor(parent=self, title='Destination directory colour')
        if not chosen.isValid():
            return
        item = self.table.item(row, 3) or QTableWidgetItem()
        item.setText(chosen.name())
        item.setBackground(QColor(chosen.name()))
        self.table.setItem(row, 3, item)   # triggers itemChanged -> sync

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
            sc_item = self.table.item(r, 2)
            col_item = self.table.item(r, 3)
            key = key_item.text().strip() if key_item else ''
            path = path_item.text().strip() if path_item else ''
            shortcut = (sc_item.text().strip()[:1].lower() if sc_item else '') or None
            colour = (col_item.text().strip() if col_item else '') or None
            if key and path:
                dests.append(
                    Destination(key=key, path=path, shortcut=shortcut, colour=colour)
                )
        self.config.destinations = dests
        self._persist()

    # _reject_if_overlaps_sources: if a destination directory overlaps with a source directory, reject input
    def _reject_if_overlaps_sources(self, dest_path: str) -> bool:
        target = Path(dest_path)
        for src in self.config.source_paths:
            if paths_overlap(target, Path(src)):
                QMessageBox.warning(self, 'Overlapping path', f'{dest_path} overlaps a source path and was skipped')
                return True
        return False

    # _reject_if_overlaps_destinations: if a source directory overlaps with a destination directory, reject input
    def _reject_if_overlaps_destinations(self, src_path: str) -> bool:
        target = Path(src_path)
        for dest in self.config.destinations:
            if paths_overlap(target, Path(dest.path)):
                QMessageBox.warning(self, 'Overlapping path', f'{src_path} overlaps a destination and was skipped')
                return True
        return False