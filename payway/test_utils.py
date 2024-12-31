from __future__ import annotations

import json
import pathlib
from typing import Any


def load_json_file(file_path: str) -> dict[str, Any]:
    file = pathlib.Path(file_path)
    with open(file) as f:
        return json.load(f)
