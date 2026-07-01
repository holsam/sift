'''
Sift: auto-resolve keyboard shortcuts for destination directories
'''

# -- Import internal destination class --
from sift.config import Destination

# -- resolve_shortcuts: maps destination index to a single lower-case shortcut letter --
def resolve_shortcuts(destinations: list[Destination]) -> dict[int, str]:
    assigned: dict[int, str] = {}
    used: set[str] = set()
    for i, dest in enumerate(destinations):
        if dest.shortcut:
            ch = dest.shortcut.strip().lower()[:1]
            if ch and ch not in used:
                assigned[i] = ch
                used.add(ch)
    for i, dest in enumerate(destinations):
        if i in assigned:
            continue
        letters = [c.lower() for c in dest.key if c.isalnum()]
        if not letters:
            continue
        if letters[0] not in used:
            chosen = letters[0]
        else:
            chosen = next((c for c in letters if c not in used), None)
        if chosen:
            assigned[i] = chosen
            used.add(chosen)
    return assigned