from __future__ import annotations

import argparse
import re
import sys
import time
from datetime import datetime, timedelta

from .notifier import notify
from .service import AlarmService, AlarmServiceError

_DURATION_RE = re.compile(r"^(\d+)([smh])$", re.IGNORECASE)


def parse_at(value: str) -> datetime:
    value = value.strip()
    try:
        hour_s, minute_s = value.split(":", 1)
        hour, minute = int(hour_s), int(minute_s)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid --at value '{value}'; expected HH:MM"
        ) from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise argparse.ArgumentTypeError(
            f"Invalid --at value '{value}'; hour/minute out of range"
        )
    now = datetime.now()
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


def parse_in(value: str) -> datetime:
    match = _DURATION_RE.fullmatch(value.strip())
    if not match:
        raise argparse.ArgumentTypeError(
            f"Invalid --in value '{value}'; expected Ns, Nm, or Nh (e.g. 10s, 5m, 1h)"
        )
    amount = int(match.group(1))
    unit = match.group(2).lower()
    if amount <= 0:
        raise argparse.ArgumentTypeError("--in duration must be greater than 0")
    delta = {
        "s": timedelta(seconds=amount),
        "m": timedelta(minutes=amount),
        "h": timedelta(hours=amount),
    }[unit]
    return datetime.now() + delta


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alarmclock",
        description="Local CLI alarm clock (JSON-backed, stdlib only).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    set_p = sub.add_parser("set", help="Create a new alarm")
    when = set_p.add_mutually_exclusive_group(required=True)
    when.add_argument(
        "--at",
        type=parse_at,
        metavar="HH:MM",
        help="Fire today at HH:MM (local). Past times are rejected.",
    )
    when.add_argument(
        "--in",
        dest="in_",
        type=parse_in,
        metavar="DURATION",
        help="Fire after duration: Ns, Nm, or Nh",
    )
    set_p.add_argument(
        "-m",
        "--message",
        required=True,
        help="Alarm message",
    )

    sub.add_parser("list", help="List all alarms")

    cancel_p = sub.add_parser("cancel", help="Cancel a pending alarm")
    cancel_p.add_argument("id", help="Short alarm id")

    sub.add_parser("run", help="Block and fire due alarms (1s poll)")

    return parser


def cmd_set(service: AlarmService, args: argparse.Namespace) -> int:
    at = args.at if args.at is not None else args.in_
    alarm = service.create_alarm(at, args.message)
    when = alarm.at.strftime("%Y-%m-%d %H:%M:%S")
    print(f"Created alarm {alarm.id} for {when}: {alarm.message}")
    return 0


def cmd_list(service: AlarmService, _args: argparse.Namespace) -> int:
    alarms = service.list_alarms()
    if not alarms:
        print("No alarms.")
        return 0
    print(f"{'ID':<8}  {'WHEN':<19}  {'STATUS':<9}  MESSAGE")
    for alarm in alarms:
        when = alarm.at.strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"{alarm.id:<8}  {when:<19}  {alarm.status.value:<9}  {alarm.message}"
        )
    return 0


def cmd_cancel(service: AlarmService, args: argparse.Namespace) -> int:
    alarm = service.cancel_alarm(args.id)
    print(f"Cancelled {alarm.id}")
    return 0


def cmd_run(service: AlarmService, _args: argparse.Namespace) -> int:
    print("Running… Ctrl+C to stop.")
    try:
        while True:
            now = datetime.now()
            for alarm in service.due_alarms(now):
                notify(alarm)
                try:
                    service.mark_fired(alarm.id)
                except AlarmServiceError as exc:
                    # Cancelled/changed between due check and mark; keep looping.
                    print(f"warning: {exc}", file=sys.stderr)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 1

    service = AlarmService()
    handlers = {
        "set": cmd_set,
        "list": cmd_list,
        "cancel": cmd_cancel,
        "run": cmd_run,
    }
    try:
        return handlers[args.command](service, args)
    except AlarmServiceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
