'''
Sift test suite: fixtures used within test suite
'''

# -- Import external dependencies --
import pytest, random
from pathlib import Path

# -- Import internal classes --
from sift.session import Session

# -- single_src_file: fixture defining a single file to use for move tests --
@pytest.fixture
def single_src_file(tmp_path):
    src_file = tmp_path / 'src' / 'a.txt'
    src_file.parent.mkdir(parents=True, exist_ok=True)
    src_file.write_text('x')
    return src_file

# -- session_instance: fixture defining an instantiated session --
@pytest.fixture
def session_instance(tmp_path, n: int = 3):
    files = [tmp_path / f'file_{i}.txt' for i in range (n)]
    return Session(files=files, rng=random.Random(0))

# -- source_files: fixture defining a set of files for testing scanning functions --
@pytest.fixture
def source_files(tmp_path):
    file_paths = [Path(tmp_path / 'a.jpg'), Path(tmp_path / 'sub' / 'b.png'), Path(tmp_path / 'sub' / 'c.txt')]
    for f in file_paths:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text('x', encoding='utf-8')
    return tmp_path