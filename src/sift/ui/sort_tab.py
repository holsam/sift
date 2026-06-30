'''
Sift UI: sort tab
'''
# -- Import external dependencies --
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# -- Import internal classes --
from sift.config import AppConfig
from sift.session import MoveRecord, Session

# -- Import internal functions --
from sift.mover import move_file, undo_move
from sift.scanner import scan

# -- Import internal UI components --
from sift.ui.preview import PreviewWidget

# -- human_size: convert a file size into a human-readable string --
def human_size(num: int) -> str:
    size = float(num)
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if size < 1024 or unit == 'TB':
            return f'{size:.0f} {unit}' if unit == 'B' else f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} TB'

# -- SortTab: class to define the structure of the sort tab panels --
class SortTab(QWidget):
    # Initialise QWidget
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.session: Session | None = None
        root = QHBoxLayout(self)
        left = self._build_left_column()
        self.preview = PreviewWidget()       
        root.addWidget(left, stretch=1)
        root.addWidget(self.preview, stretch=2)

    
    # _build_left_column: construct the left column panel (summary, file information, destinations, history)
    def _build_left_column(self) -> QWidget:
        col = QWidget()
        layout = QVBoxLayout(col)
        # Set up summary box panel
        summary_box = QGroupBox('Session Summary')
        sl = QVBoxLayout(summary_box)
        self.start_btn = QPushButton('Start session')
        self.start_btn.clicked.connect(self.start_session)
        self.summary_label = QLabel('No session running.')
        sl.addWidget(self.start_btn)
        sl.addWidget(self.summary_label)
        layout.addWidget(summary_box)

        # Set up current file info panel
        info_box = QGroupBox('Current File')
        il = QVBoxLayout(info_box)
        self.name_label = QLabel('—')
        self.name_label.setWordWrap(True)
        self.size_label = QLabel('—')
        self.dir_label = QLabel('—')
        self.dir_label.setWordWrap(True)
        il.addWidget(self.name_label)
        il.addWidget(self.size_label)
        il.addWidget(self.dir_label)
        layout.addWidget(info_box)

        # Set up destination buttons panel
        self.buttons_box = QGroupBox('Move To')
        self.buttons_layout = QGridLayout(self.buttons_box)
        layout.addWidget(self.buttons_box)

        action_row = QHBoxLayout()
        skip_btn = QPushButton('Skip')
        skip_btn.clicked.connect(self.skip_current)
        self.undo_btn = QPushButton('Undo last move')
        self.undo_btn.clicked.connect(self.undo_last)
        self.undo_btn.setEnabled(False)
        action_row.addWidget(skip_btn)
        action_row.addWidget(self.undo_btn)
        layout.addLayout(action_row)

        # Set up session history panel
        console_box = QGroupBox('Session History')
        cl = QVBoxLayout(console_box)
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        cl.addWidget(self.console)
        layout.addWidget(console_box, stretch=1)

        return col

    # start_session: start a session by scanning for files, clearing history, and constructing destination buttons
    def start_session(self) -> None:
        files = scan(
            [Path(p) for p in self.config.source_paths],
            recursive=self.config.recursive,
            extensions=self.config.filters.normalised(),
        )
        if not files:
            self.summary_label.setText('No files matched. Check the Setup tab.')
            return
        self.session = Session(files=files)
        self.console.clear()
        self._rebuild_destination_buttons()
        self._refresh()

    # _rebuild_destination_buttons: create destination directory buttons
    def _rebuild_destination_buttons(self) -> None:
        # Clear any existing buttons.
        while self.buttons_layout.count():
            item = self.buttons_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for i, dest in enumerate(self.config.destinations):
            btn = QPushButton(f'{i + 1}. {dest.key}')
            btn.clicked.connect(lambda _=False, d=dest: self.sort_current(d))
            self.buttons_layout.addWidget(btn, i // 2, i % 2)

    # sort_current: move current file
    def sort_current(self, dest) -> None:
        if not self.session:
            return
        current = self.session.current()
        if current is None:
            return
        original = current
        final = move_file(current, Path(dest.path))
        self.session.record_move(
            MoveRecord(original=original, final=final, key=dest.key)
        )
        self._refresh()

    # skip_current: skip current file
    def skip_current(self) -> None:
        if not self.session:
            return
        self.session.skip()
        self._refresh()

    # undo_last: undo last file move
    def undo_last(self) -> None:
        if not self.session or self.session.last_move is None:
            return
        record = self.session.last_move
        undo_move(record.final, record.original)
        self.session.restore(record)
        self._refresh()

    # _refresh: refresh Sort tab
    def _refresh(self) -> None:
        if not self.session:
            return
        self.summary_label.setText(f'Sorted {self.session.sorted_count} of {self.session.total} ({self.session.remaining} left)')
        self.undo_btn.setEnabled(self.session is not None and self.session.last_move is not None)
        self.console.setPlainText('\n'.join(self.session.history))
        self.console.verticalScrollBar().setValue(
            self.console.verticalScrollBar().maximum()
        )
        current = self.session.current()
        if current is None:
            self.name_label.setText('All done')
            self.size_label.setText('—')
            self.dir_label.setText('—')
            self.preview.show_message('Session complete')
            return
        self.name_label.setText(f'<b>{current.name}</b>')
        try:
            self.size_label.setText(human_size(current.stat().st_size))
        except OSError:
            self.size_label.setText('size unavailable')
        self.dir_label.setText(str(current.parent))
        self.preview.show_file(current)