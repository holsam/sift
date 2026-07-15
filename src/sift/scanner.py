'''
Sift: recursive file scanning and filtering
'''

# -- Import external dependencies --
import fnmatch, re
from datetime import datetime
from pathlib import Path

# -- Import internal filter class --
from sift.config import Filters

# -- _passes: checks if a file matches set filters and returns boolean --
def _passes(path: Path, filters: Filters, exts: set[str]) -> bool:
    if exts and path.suffix.lower() not in exts:
        return False
    name = path.name
    if filters.name_glob and not fnmatch.fnmatch(name.lower(), filters.name_glob.lower()):
        return False
    if filters.name_regex:
        try:
            if not re.search(filters.name_regex, name):
                return False
        except re.error:
            return False
    try:
        stat = path.stat()
    except OSError:
        return False
    if filters.min_size is not None and stat.st_size < filters.min_size:
        return False
    if filters.max_size is not None and stat.st_size > filters.max_size:
        return False
    if filters.modified_after or filters.modified_before:
        mtime = datetime.fromtimestamp(stat.st_mtime)
        if filters.modified_after and mtime < filters.modified_after:
            return False
        if filters.modified_before and mtime > filters.modified_before:
            return False
    return True

# -- walk_files: collects every resolved file path from sources, deduplicated, unfiltered --
def walk_files(sources: list[Path], recursive: bool = True) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    def consider(p: Path) -> None:
        if not p.is_file():
            return
        resolved = p.resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        out.append(resolved)
    for src in sources:
        if src.is_file():
            consider(src)
        elif src.is_dir():
            walker = src.rglob('*') if recursive else src.glob('*')
            for child in walker:
                consider(child)
    return out

# -- filter_files: apply filters to an already-collected list of files, in memory --
def filter_files(files: list[Path], filters: Filters | None = None) -> list[Path]:
    filters = filters or Filters()
    exts = filters.normalised()
    return [p for p in files if _passes(p, filters, exts)]

# -- scan: collects files from sources and filters to return a list of Paths --
def scan(
    sources: list[Path],
    recursive: bool = True,
    filters: Filters | None = None,
) -> list[Path]:
    return filter_files(walk_files(sources, recursive), filters)