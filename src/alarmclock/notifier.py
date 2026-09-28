from __future__ import annotations

import sys

from .models import Alarm


def notify(alarm: Alarm) -> None:
    """Print a clear alarm alert and beep via terminal bell."""
    when = alarm.at.strftime("%H:%M:%S")
    sys.stdout.write("\a")
    sys.stdout.write(
        f"\n*** ALARM [{alarm.id}] @ {when} ***\n"
        f"{alarm.message}\n\n"
    )
    sys.stdout.flush()
