'''
Sift: file moving functions
'''

# -- Import external dependencies --
import shutil
from pathlib import Path

# -- unique_target: returns a Path which does not exist inside dest_dir --
def unique_target(dest_dir: Path, name: str) -> Path:
    target = dest_dir / name
    if not target.exists():
        return target
    stem = Path(name).stem
    suffix = Path(name).suffix
    i = 1
    while True:
        candidate = dest_dir / f"{stem}_({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1

# -- move_file: moves file src into dest_dir, renaming if a clash is present --
def move_file(src: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = unique_target(dest_dir, src.name)
    shutil.move(str(src), str(target))
    return target

# -- undo_move: moves a previously moved file back to its original path --
def undo_move(final: Path, original: Path) -> Path:
    original.parent.mkdir(parents=True, exist_ok=True)
    target = original
    if target.exists():
        target = unique_target(original.parent, original.name)
    shutil.move(str(final), str(target))
    return target