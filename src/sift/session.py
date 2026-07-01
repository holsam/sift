'''
Sift: session history
'''

# -- Import external dependencies --
import random, tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# -- DELETED_KEY: variable holding the key for deleted files --
DELETED_KEY = 'deleted'

# -- MoveRecord: dataclass holding information needed to describe and reverse a file move --
@dataclass
class MoveRecord:
    original: Path  # original file path
    final: Path  # post-move/rename file path
    key: str  # destination key used
    colour: str | None = None

# -- LogLine: dataclass holding information about a history console entry --
@dataclass
class LogLine:
    stamp: str
    body: str
    key: str = ''
    colour: str | None = None

# -- Session: dataclass holding the working queue, counts, history and the last move --
@dataclass
class Session:
    files: list[Path]
    rng: random.Random = field(default_factory=random.Random)
    total: int = 0
    sorted_count: int = 0
    history: list[LogLine] = field(default_factory=list)
    last_move: MoveRecord | None = None
    trash_dir: Path = field(default=Path)
    _queue: list[Path] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._queue = list(self.files)
        self.rng.shuffle(self._queue)
        self.total = len(self._queue)
        self.trash_dir = Path(tempfile.mkdtemp(prefix='sift-trash-'))

    @property
    def remaining(self) -> int:
        return len(self._queue)

    def current(self) -> Path | None:
        return self._queue[0] if self._queue else None

    # log: add an entry to the history console 
    def log(self, body: str, key: str = '', colour: str | None = None) -> None:
        stamp = datetime.now().strftime('%H:%M:%S')
        self.history.append(LogLine(stamp, body, key, colour))

    # record_move: pop the current file out of queue, count it and remember information for potential undo
    def record_move(self, record: MoveRecord) -> None:
        if self._queue:
            self._queue.pop(0)
        self.sorted_count += 1
        self.last_move = record
        self.log(f'moved "{record.original.name}" → ', record.key, record.colour)

    # record_delete: pop the current file out of queue, count it and move to Sift trash directory
    def record_delete(self, record: MoveRecord) -> None:
        if self._queue:
            self._queue.pop(0)
        self.sorted_count += 1
        self.last_move = record
        self.log(f'deleted "{record.original.name}" → ', 'Trash', '#b04a4a')

    # skip: send the current file to a random spot further down the queue
    def skip(self) -> None:
        if len(self._queue) <= 1:
            return
        item = self._queue.pop(0)
        idx = self.rng.randint(1, len(self._queue))
        self._queue.insert(idx, item)
    
    # restore: put an undone file back at the front and adjust counts
    def restore(self, record: MoveRecord) -> None:
        self._queue.insert(0, record.original)
        self.sorted_count = max(0, self.sorted_count - 1)
        self.last_move = None
        self.log(f'undo: restored "{record.original.name}"')