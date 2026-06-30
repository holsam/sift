'''
Sift: recursive file scanning and filtering
'''

# -- Import external dependencies --
from pathlib import Path

# -- scan: collects files from sources and filters by extensions to return a list of Paths --
def scan(
    sources: list[Path],
    recursive: bool = True,
    extensions: set[str] | None = None,
) -> list[Path]:
    exts = extensions or set()
    seen: set[Path] = set()
    out: list[Path] = []
    def consider(p: Path) -> None:
        if not p.is_file():
            return
        if exts and p.suffix.lower() not in exts:
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