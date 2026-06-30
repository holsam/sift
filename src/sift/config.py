'''
Sift: configuration management and handling
'''

# -- Import external dependencies --
import yaml
from pathlib import Path
from platformdirs import user_config_path
from pydantic import BaseModel, Field

# -- Define variables for config directory/file paths --
CONFIG_DIR = user_config_path('sift')
CONFIG_FILE = CONFIG_DIR / 'config.yaml'

# -- Destination: class which holds informaiton about a labelled target directory --
class Destination(BaseModel):
    key: str
    path: str


# -- Filters: class which holds file selection filters --
class Filters(BaseModel):
    extensions: list[str] = Field(default_factory=list)

    # Filters.normalised: returns a set of lowercase extensions all beginning with a dot
    def normalised(self) -> set[str]:
        out: set[str] = set()
        for ext in self.extensions:
            ext = ext.strip().lower()
            if not ext:
                continue
            out.add(ext if ext.startswith('.') else f'.{ext}')
        return out


# -- AppConfig: class which holds Sift configuration information for saving/loading --
class AppConfig(BaseModel):
    source_paths: list[str] = Field(default_factory=list)
    recursive: bool = True
    filters: Filters = Field(default_factory=Filters)
    destinations: list[Destination] = Field(default_factory=list)

    # AppConfig.load: class method which loads a file to a validated AppConfig class instance
    @classmethod
    def load(cls, path: Path = CONFIG_FILE) -> 'AppConfig':
        if not path.exists():
            return cls()
        data = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
        return cls.model_validate(data)

    # AppConfig.save: save an AppConfig class to a given file
    def save(self, path: Path = CONFIG_FILE) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump()
        path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding='utf-8')
