"""Corruption-tolerant JSON cache reads and atomic writes."""

import fcntl
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


def read_json_cache(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def write_json_cache(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with lock_path.open("a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temp:
            json.dump(value, temp, ensure_ascii=False, sort_keys=True)
            temp.flush(); os.fsync(temp.fileno()); temporary_path = Path(temp.name)
        os.replace(temporary_path, path)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
