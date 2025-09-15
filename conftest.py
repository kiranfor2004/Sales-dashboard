import pytest
from pathlib import Path

LEGACY_FILENAMES = {"test_simple.py"}
IGNORE_DIR_PARTS = {".venv", "backend", "frontend"}

def pytest_ignore_collect(collection_path: Path, path: Path):  # type: ignore[override]
    p = Path(str(path))
    if any(part in IGNORE_DIR_PARTS for part in p.parts):
        if p.name not in ("test_api.py", "test_import_app.py"):
            return True
    if p.name in LEGACY_FILENAMES:
        return True
    return False
