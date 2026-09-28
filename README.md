# Alarm Clock CLI

A local Python CLI alarm clock for a senior take-home assessment. Set, list, cancel, and run alarms in the terminal; fire with a clear message and beep. Persistence is a JSON file — no web UI, no database.

## Quick start

Requires **Python 3.11+**. Stdlib only; no `pip install`.

```powershell
cd alarm-clock
$env:PYTHONPATH = "src"

python -m alarmclock set --in 10s -m "demo"
python -m alarmclock list
python -m alarmclock run
```

On macOS/Linux: `export PYTHONPATH=src`.

### Commands

| Command | Description |
|---|---|
| `set --at HH:MM -m "..."` | Alarm today at local `HH:MM` (past times rejected) |
| `set --in Ns\|Nm\|Nh -m "..."` | Relative delay (`10s`, `5m`, `1h`) |
| `list` | Show all alarms (id, time, status, message) |
| `cancel <id>` | Cancel a pending alarm by short id |
| `run` | Blocking 1s poll loop; fires due alarms until Ctrl+C |

Storage: `~/.alarmclock/alarms.json`.

## Requirements chosen / cut

**In scope**

- Absolute (`--at`) and relative (`--in`) scheduling
- List / cancel / foreground `run`
- Terminal notify + `\a` beep
- JSON persistence under the home directory
- Clear errors and non-zero exit codes

**Explicitly out of scope**

- Recurrence, snooze, editing alarms
- Web UI, React, fancy TUI
- SQLite or any database server
- Background daemon / OS service
- Cloud sync, multi-user, notifications APIs

## Architecture

```text
cli.py  →  service.py  →  store.py
                ↓
           notifier.py
```

| Module | Role |
|---|---|
| `cli.py` | argparse subcommands, parsing, exit codes |
| `service.py` | create / list / cancel / due / mark fired |
| `store.py` | load/save `~/.alarmclock/alarms.json` (atomic replace) |
| `notifier.py` | alarm text + terminal bell |
| `models.py` | `Alarm` (`id`, `at`, `message`, `status`) |

Statuses: `pending` → `fired` | `cancelled`.

## Engineering decisions

1. **Separate `run` process** — easy to demo on Windows (set in one terminal, run in another).
2. **JSON file, not a DB** — matches the brief; inspectable; zero deps.
3. **1-second poll** — simple and good enough for a CLI demo.
4. **Reject past `--at`; allow short `--in`** — honest wall-clock semantics; still easy to demo.
5. **Stdlib only** — argparse, dataclasses, datetime, json, pathlib, uuid, time.
6. **Atomic writes** — temp file + `os.replace` to avoid truncated JSON on crash.
7. **Accepted limit** — not multi-process safe; concurrent writers → last save wins.

## How I used AI

1. **Refine** — locked must/won't with the recruiter constraints (CLI, no DB, short build).
2. **Design** — CLI → service → store + notifier; commands and data model agreed before code.
3. **Plan** — file layout and build order (`models`/`store` → `service` → `notifier`/`cli`).
4. **Implement** — layered slices; no scope creep.
5. **Review** — senior pass for races, Windows paths, validation; applied only important fixes.
6. **Validate** — manual smoke: `--in`, past `--at` rejection, list/cancel, `run` + Ctrl+C.

## Limitations / next steps

- Concurrent `set`/`cancel` while `run` is active can lose updates (no file lock).
- `\a` beep depends on the terminal; some Windows hosts mute it.
- No unit tests beyond a stub (time logic is testable via an injectable clock if extended).
- Possible next steps: file locking, snooze, daily repeat, `pip install -e .` packaging — only if the brief expands.

## Tests

`tests/test_service.py` is a stub today. When tests are added:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```
