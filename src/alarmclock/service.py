from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from .models import Alarm, AlarmStatus
from .store import AlarmStore


class AlarmServiceError(ValueError):
    """User-facing service error."""


class AlarmService:
    def __init__(self, store: AlarmStore | None = None) -> None:
        self._store = store or AlarmStore()

    def create_alarm(self, at: datetime, message: str) -> Alarm:
        message = message.strip()
        if not message:
            raise AlarmServiceError("Message must not be empty")
        now = datetime.now()
        if at.tzinfo is not None:
            at = at.astimezone().replace(tzinfo=None)
        if at <= now:
            raise AlarmServiceError("Cannot set alarm in the past")

        alarm = Alarm(
            id=uuid4().hex[:8],
            at=at,
            message=message,
            status=AlarmStatus.PENDING,
        )
        alarms = self._store.load()
        alarms.append(alarm)
        self._store.save(alarms)
        return alarm

    def list_alarms(self) -> list[Alarm]:
        alarms = self._store.load()
        return sorted(alarms, key=lambda a: a.at)

    def cancel_alarm(self, alarm_id: str) -> Alarm:
        alarm_id = alarm_id.strip().lower()
        alarms = self._store.load()
        for alarm in alarms:
            if alarm.id == alarm_id:
                if alarm.status != AlarmStatus.PENDING:
                    raise AlarmServiceError(
                        f"Alarm {alarm_id} is {alarm.status.value}, not pending"
                    )
                alarm.status = AlarmStatus.CANCELLED
                self._store.save(alarms)
                return alarm
        raise AlarmServiceError(f"Alarm not found: {alarm_id}")

    def due_alarms(self, now: datetime) -> list[Alarm]:
        return [
            a
            for a in self._store.load()
            if a.status == AlarmStatus.PENDING and a.at <= now
        ]

    def mark_fired(self, alarm_id: str) -> Alarm:
        alarm_id = alarm_id.strip().lower()
        alarms = self._store.load()
        for alarm in alarms:
            if alarm.id == alarm_id:
                if alarm.status != AlarmStatus.PENDING:
                    raise AlarmServiceError(
                        f"Alarm {alarm_id} is {alarm.status.value}, not pending"
                    )
                alarm.status = AlarmStatus.FIRED
                self._store.save(alarms)
                return alarm
        raise AlarmServiceError(f"Alarm not found: {alarm_id}")
