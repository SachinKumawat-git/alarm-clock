from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .models import Alarm

DEFAULT_PATH = Path.home() / ".alarmclock" / "alarms.json"


class AlarmStore:
    """JSON persistence. Not multi-process safe: last writer wins on concurrent saves."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_PATH

    def load(self) -> list[Alarm]:
        if not self.path.exists():
            return []
        try:
            raw = self.path.read_text(encoding="utf-8").strip()
        except OSError:
            raise
        if not raw:
            return []
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Corrupt alarm store {self.path}: {exc}") from exc
        if not isinstance(data, list):
            raise ValueError(f"Invalid alarm store format in {self.path}")
        return [Alarm.from_dict(item) for item in data]

    def save(self, alarms: list[Alarm]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps([a.to_dict() for a in alarms], indent=2)
        fd, tmp_name = tempfile.mkstemp(
            dir=str(self.path.parent),
            prefix=".alarms-",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as tmp:
                tmp.write(payload)
                tmp.write("\n")
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(tmp_name, self.path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
