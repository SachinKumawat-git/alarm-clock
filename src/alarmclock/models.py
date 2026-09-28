from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class AlarmStatus(str, Enum):
    PENDING = "pending"
    FIRED = "fired"
    CANCELLED = "cancelled"


@dataclass
class Alarm:
    id: str
    at: datetime
    message: str
    status: AlarmStatus

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "at": self.at.isoformat(timespec="seconds"),
            "message": self.message,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Alarm:
        try:
            at = datetime.fromisoformat(data["at"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid alarm record: bad 'at' ({exc})") from exc
        if at.tzinfo is not None:
            at = at.astimezone().replace(tzinfo=None)
        try:
            return cls(
                id=str(data["id"]),
                at=at,
                message=str(data["message"]),
                status=AlarmStatus(data["status"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid alarm record: {exc}") from exc
