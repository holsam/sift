'''
Sift test suite: configuration management/handling (src/sift/config.py) tests
'''

# -- Import external dependencies --
from pathlib import Path

# -- Import internal config classes --
from sift.config import AppConfig, Destination, Filters

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