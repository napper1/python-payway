from __future__ import annotations

import json
import pathlib


def load_json_file(file_path: str) -> dict:
    file = pathlib.Path(file_path)
    with open(file) as f:
        return json.load(f)
