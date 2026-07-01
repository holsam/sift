'''
Sift test suite: unit tests for core helper files
'''

# -- Import external dependencies ==
import random
from pathlib import Path

# -- Import internal classes and functions for testing --
from sift.config import AppConfig, Destination, Filters
from sift.mover import delete_to_session_trash, flush_session_trash, move_file, paths_overlap, undo_move, unique_target
from sift.scanner import scan
from sift.session import MoveRecord, Session
from sift.shortcuts import resolve_shortcuts

# -- TestConfig: class defining unit tests for configuration handling --
class TestConfig:
    # test_round_trip: tests that an AppConfig instance can be saved and loaded correctly
    def test_round_trip(self, tmp_path: Path) -> None:
        cfg = AppConfig(
            source_paths=['/some/dir'],
            recursive=False,
            filters=Filters(extensions=['jpg', '.PNG']),
            destinations=[Destination(key='keep', path='/out/keep')],
        )
        target = tmp_path / 'config.yaml'
        cfg.save(target)
        loaded = AppConfig.load(target)
        assert loaded.source_paths == ['/some/dir']
        assert loaded.recursive is False
        assert loaded.destinations[0].key == 'keep'
    
    # test_missing_file_gives_defaults: tests that an AppConfig loaded from a missing file uses default values
    def test_missing_file_gives_defaults(self, tmp_path: Path) -> None:
        cfg = AppConfig.load(tmp_path / 'missing-file.yaml')
        assert cfg.source_paths == []
        assert cfg.recursive is True

    # test_extension_normalisation: tests that extensions are correctly normalised
    def test_extension_normalisation(self) -> None:
        f = Filters(extensions=['jpg', '.PNG', '  Mp4 '])
        assert f.normalised() == {'.jpg', '.png', '.mp4'}


# -- TestMove: class defining unit tests for move
class TestMove:
    # test_unique_target_on_clash: tests that a file which has the same filename as an existing file is renamed to a unique filename
    def test_unique_target_on_clash(self, tmp_path: Path) -> None:
        (tmp_path / 'a.txt').write_text('x')
        assert unique_target(tmp_path, 'a.txt').name == 'a_(1).txt'

    # test_move: tests that files are moved from a source directory to a destination directory
    def test_move(self, single_src_file, tmp_path) -> None:
        dest_dir = tmp_path / 'dest'
        moved = move_file(single_src_file, dest_dir)
        assert moved.exists()
        assert not single_src_file.exists()

    # test_undo: tests that files which are moved can be undone
    def test_undo(self, single_src_file, tmp_path: Path) -> None:
        orig_filepath = single_src_file
        dest_dir = tmp_path / 'dest'
        moved = move_file(orig_filepath, dest_dir)
        back = undo_move(moved, orig_filepath)
        assert back == orig_filepath
        assert orig_filepath.read_text() == 'x'
        assert not moved.exists()

    # test_overlap: test that directories which are the same or contain one another are flagged as overlapping
    def test_overlap(self) -> None:
        assert paths_overlap(Path('/a/b'), Path('/a/b'))
        assert paths_overlap(Path("/a"), Path("/a/b"))
        assert paths_overlap(Path("/a/b"), Path("/a"))
        assert not paths_overlap(Path("/a/b"), Path("/a/c"))

    # test_delete_then_flush: test that a file moved to Sift trash directory is deleted and directory is flushed
    def test_delete_then_flush(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        trash = tmp_path / "trash"
        src.mkdir()
        f = src / "x.txt"
        f.write_text("hi")

        moved = delete_to_session_trash(f, trash)
        assert moved.exists()
        assert not f.exists()

        flush_session_trash(trash)  # sends to OS trash, removes holding folder
        assert not trash.exists()


# -- TestScan: class defining unit tests for file scanning --
class TestScan:
    # test_recursive: test file scanning in recursive mode scans subdirectories
    def test_recursive(self, source_files) -> None:
        results = scan([source_files], recursive=True)
        assert len(results) == 3
        assert {p.name for p in results} == {'a.jpg', 'b.png', 'c.txt'}

    # test_non_recursive: test file scanning in non-recursive mode doesn't scan subdirectories
    def test_non_recursive(self, source_files) -> None:
        results = scan([source_files], recursive=False)
        assert len(results) == 1
        assert {p.name for p in results} == {'a.jpg'}

    # test_filter: tests than scan filters by file extensions
    def test_filter(self, source_files) -> None:
        filters = Filters(extensions=['.jpg', '.png'])
        results = scan([source_files], recursive=True, filters=filters)
        assert len(results) == 2
        assert {p.name for p in results} == {'a.jpg', 'b.png'}

    # test_dedup: test that duplicated files are not reported
    def test_dedup(self, tmp_path, source_files) -> None:
        dup = tmp_path / 'a.jpg'
        dup.parent.mkdir(parents=True, exist_ok=True)
        dup.write_text('x', encoding='utf-8')
        files = scan([source_files, tmp_path / 'a.jpg'], recursive=False)
        assert len(files) == 1


# -- TestSession: class defining unit tests for session information --
class TestSession:
    # test_counts_on_move: tests that a moved file is counted as sorted (and removed from remaining count)
    def test_counts_on_move(self, session_instance) -> None:
        s = session_instance
        assert s.total == 3
        cur = s.current()
        s.record_move(MoveRecord(original=cur, final=Path('/out/x'), key='keep'))
        assert s.sorted_count == 1
        assert s.remaining == 2

    # test_skip_keeps_file_in_queue: tests that a skipped file remains in the queue
    def test_skip_keeps_file_in_queue(self, session_instance) -> None:
        s = session_instance
        before = s.remaining
        s.skip()
        assert s.remaining == before

    # test_undo_restores: tests that undoing a move removes the file from the sorted count, and
    def test_undo_restores(self, session_instance) -> None:
        s = session_instance
        cur = s.current()
        rec = MoveRecord(original=cur, final=Path('/out/x'), key='keep')
        s.record_move(rec)
        s.restore(rec)
        assert s.sorted_count == 0
        assert s.current() == cur
        assert s.last_move is None


# -- TestShortcut: class defining unit tests for keyboard shortcut resolution --
class TestShortcuts:
    # create_dest: return a Destination class with the provided key and shortcut
    def create_dest(self, key: str, shortcut: str| None = None) -> Destination:
        return Destination(key=key, path='tmp', shortcut=shortcut)
    
    # test_first_letters_when_unique: tests that shortcut resolves to first letter of each destination when unique
    def test_first_letters_when_unique(self) -> None:
        out = resolve_shortcuts([self.create_dest('Keep'), self.create_dest('Bin'), self.create_dest('Archive')])
        assert out == {0: "k", 1: "b", 2: "a"}

    # test_falls_back_to_next_free_letter: test that shortcut resolves to the next available letter if the first letter is taken
    def test_falls_back_to_next_free_letter(self) -> None:
        out = resolve_shortcuts([self.create_dest(key='Keep'), self.create_dest(key='Kittens')])
        assert out[0] == 'k'
        assert out[1] != 'k'  # 'i', 't', etc.

    # test_custom_shortcut: test that custom shortcuts are always used over auto-resolved shortcuts
    def test_custom_shortcut_wins(self) -> None:
        out = resolve_shortcuts([self.create_dest('Keep', shortcut='z'), self.create_dest('Zebra')])
        assert out[0] == 'z'
        assert out[1] != 'z'