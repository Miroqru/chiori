"""
Функции для чтения и записи json файлов.
"""

import json
from pathlib import Path
from typing import Optional


def write_json(path: Path, content: dict) -> None:
    if not path.exists():
        path.parents[0].mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        json.dump(content, f, ensure_ascii=True, indent=4)

def load_json(path: Path, data: Optional[dict]=None) -> dict:
    if not path.exists() and data is not None:
        write_json(path, data)

    with open(path) as f:
        return json.load(f)
