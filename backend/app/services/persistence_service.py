"""Locked append-only JSONL persistence and CSV-safe export."""

import csv
from datetime import UTC, datetime
import fcntl
import io
import json
import os
from pathlib import Path
from typing import Any, Iterable
from uuid import UUID, uuid4

from app.core.config import settings


def anonymous_session_id(value: str | None = None) -> str:
    if value:
        try:
            return str(UUID(value))
        except ValueError:
            pass
    return str(uuid4())


def append_jsonl(kind: str, record: dict[str, Any]) -> None:
    if kind not in {"feedback", "survey"}:
        raise ValueError("unsupported persistence kind")
    directory = settings.DATA_DIR.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{kind}.jsonl"
    payload = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


def timestamp_utc() -> str:
    return datetime.now(UTC).isoformat()


def read_jsonl(kind: str) -> list[dict[str, Any]]:
    path = settings.DATA_DIR.resolve() / f"{kind}.jsonl"
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
        for line in handle:
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    rows.append(value)
            except json.JSONDecodeError:
                continue
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return rows


def _csv_safe(value: Any) -> str:
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    text = "" if value is None else str(value)
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def export_csv(rows: Iterable[dict[str, Any]]) -> str:
    materialized = list(rows)
    headers = sorted({key for row in materialized for key in row})
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=headers, extrasaction="ignore")
    if headers:
        writer.writeheader()
        for row in materialized:
            writer.writerow({key: _csv_safe(row.get(key)) for key in headers})
    return output.getvalue()
