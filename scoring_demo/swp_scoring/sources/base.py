"""The sources.toml loader."""

import tomllib
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_sources_config(path: Path | None = None) -> dict:
    path = path or (CONFIG_DIR / "sources.toml")
    with open(path, "rb") as f:
        return tomllib.load(f)
