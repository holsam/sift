'''
Sift UI: sort tab
'''
# -- Import external dependencies --
import html
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# -- Import internal classes and variables --
from sift.config import AppConfig
from sift.session import DELETED_KEY, MoveRecord, Session

# -- Import internal functions --
from sift.mover import delete_to_session_trash, flush_session_trash, move_file, undo_move
from sift.scanner import scan
from sift.shortcuts import resolve_shortcuts

# -- Import internal UI components --
from sift.ui.utils.preview import PreviewWidget
from sift.ui.utils.shortcut_button import ShortcutButton

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
        self._set_session_enabled(False)

    
    # _build_left_column: construct the left column panel (summary, file information, destinations, history)
    def _build_left_column(self) -> QWidget:
        col = QWidget()
        layout = QVBoxLayout(col)
        self._session_widgets: list[QWidget] = []
        # Set up summary box panel
        summary_box = QGroupBox('Session Summary')
        sl = QVBoxLayout(summary_box)
        self.start_btn = QPushButton('Start session')
        self.start_btn.clicked.connect(self.toggle_session)
        self.summary_label = QLabel('No session running')
        sl.addWidget(self.start_btn)
        sl.addWidget(self.summary_label)
        layout.addWidget(summary_box)
        # Set up current file info panel
        self.info_box = QGroupBox('Current File')
        info_box = self.info_box
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
        # Set up action row
        action_row = QHBoxLayout()
        self.skip_btn = QPushButton('Skip')
        self.skip_btn.clicked.connect(self.skip_current)
        self.undo_btn = QPushButton('Undo')
        self.undo_btn.clicked.connect(self.undo_last)
        self.undo_btn.setEnabled(False)
        self.delete_btn = QPushButton('Delete')
        self.delete_btn.clicked.connect(self.delete_current)
        action_row.addWidget(self.skip_btn)
        action_row.addWidget(self.undo_btn)
        action_row.addWidget(self.delete_btn)
        layout.addLayout(action_row)
        self._session_widgets.append(self.skip_btn)
        self._session_widgets.append(self.undo_btn)
        self._session_widgets.append(self.delete_btn)
        # Set up session history panel
        console_box = QGroupBox('Session History')
        cl = QVBoxLayout(console_box)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        cl.addWidget(self.console)
        layout.addWidget(console_box, stretch=1)
        return col
    
    # toggle_session: toggles between starting and stopping a session as required
    def toggle_session(self) -> None:
        if self.session is None:
            self.start_session()
        else:
            self.stop_session()

    # start_session: start a session by scanning for files, clearing history, and constructing destination buttons
    def start_session(self) -> None:
        files = scan(
            [Path(p) for p in self.config.source_paths],
            recursive=self.config.recursive,
            filters=self.config.filters,
        )
        if not files:
            self.summary_label.setText("No files matched. Check the Setup tab.")
            return
        self.session = Session(files=files)
        self.console.clear()
        self._rebuild_destination_buttons()
        self.start_btn.setText("Stop session")
        self._set_session_enabled(True)
        self.setFocus()   # so key shortcuts reach the tab, not a button
        self._refresh()

    # stop_session: end a session by deleting any deleted files and resetting the UI
    def stop_session(self) -> None:
        if self.session is not None:
            flush_session_trash(self.session.trash_dir)
        self.session = None
        self.start_btn.setText("Start session")
        self._set_session_enabled(False)
        self.summary_label.setText("No session running.")
        self.name_label.setText("—")
        self.size_label.setText("—")
        self.dir_label.setText("—")
        self.preview.show_message("No session running.")

    # _set_session_enabled: enables UI components if session is started
    def _set_session_enabled(self, on: bool) -> None:
        self.buttons_box.setEnabled(on)
        self.info_box.setEnabled(on)
        for w in self._session_widgets:
            w.setEnabled(on)

    # _rebuild_destination_buttons: create destination directory buttons
    def _rebuild_destination_buttons(self) -> None:
        while self.buttons_layout.count():
            item = self.buttons_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._shortcuts = resolve_shortcuts(self.config.destinations)
        self._shortcut_to_dest = {}
        for i, dest in enumerate(self.config.destinations):
            letter = self._shortcuts.get(i)
            text, underline = self._button_label(dest.key, letter)
            btn = ShortcutButton(text, underline)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)   # keep keys on the tab
            if dest.colour:
                btn.setStyleSheet(f'ShortcutButton {{ color: {dest.colour}; }}')
            btn.clicked.connect(lambda _=False, d=dest: self.sort_current(d))
            self.buttons_layout.addWidget(btn, i // 2, i % 2)
            if letter:
                self._shortcut_to_dest[letter] = dest

    # _button_label: returns the keyboard shorcut key and the letter to underline
    @staticmethod
    def _button_label(key: str, letter: str | None) -> tuple[str, int]:
        if not letter:
            return key, -1
        low = key.lower()
        if letter in low:
            return key, low.index(letter)
        text = f'{key} ({letter})'
        return text, text.lower().index(letter, len(key))

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
            MoveRecord(original=original, final=final, key=dest.key, colour=dest.colour)
        )
        self._refresh()

    # skip_current: skip current file
    def skip_current(self) -> None:
        if not self.session:
            return
        self.session.skip()
        self._refresh()

    # delete_current: moves the current file to the session trash directory (for deleting at session end)
    def delete_current(self) -> None:
        if not self.session:
            return
        current = self.session.current()
        if current is None:
            return
        final = delete_to_session_trash(current, self.session.trash_dir)
        self.session.record_delete(
            MoveRecord(original=current, final=final, key=DELETED_KEY)
        )
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
        lines = []
        for entry in self.session.history:
            body = html.escape(entry.body)
            if entry.key:
                colour = entry.colour or "#888888"
                key = (
                    f'<span style="color:{colour}; font-weight:600">'
                    f"{html.escape(entry.key)}</span>"
                )
            else:
                key = ""
            lines.append(
                f'<span style="color:#888888">[{entry.stamp}]</span> {body}{key}'
            )
        self.console.setHtml("<br>".join(lines))
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

    # keyPressEvent: handler for all keyboard shortcuts
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self.session:
            super().keyPressEvent(event)
            return
        key = event.key()
        mods = event.modifiers()
        # Register destination keyboard shortcuts
        text = event.text().lower()
        if text and text in getattr(self, '_shortcut_to_dest', {}):
            self.sort_current(self._shortcut_to_dest[text])
            return
        # Register skip keyboard shortcut
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.skip_current()
            return
        # Register delete keyboard shortcut
        if key == Qt.Key.Key_Backspace:
            self.delete_current()
            return
        # Register undo keyboard shortcut
        if key == Qt.Key.Key_Z and mods & Qt.KeyboardModifier.ControlModifier:
            self.undo_last()
            return
        super().keyPressEvent(event)

    # keyReleaseEvent: handler for key being released
    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        super().keyReleaseEvent(event)