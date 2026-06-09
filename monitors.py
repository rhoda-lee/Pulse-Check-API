"""In-memory monitor management and the countdown timers.

This module owns all monitor state and the asyncio tasks that count down each
device's timer with no web/HTTP code.
"""


from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from models import Monitor, Status

logger = logging.getLogger("pulse")

_monitors: dict[str, Monitor] = {}       # id -> Monitor record
_tasks: dict[str, asyncio.Task] = {}     # id -> its running countdown task


class MonitorNotFound(Exception):
    """Raised when an operation references a monitor id that does not exist."""


class MonitorAlreadyExists(Exception):
    """Raised when registering an id that is already being monitored."""


def _fire_alert(monitor_id: str) -> None:
    """Emit the device-down alert as a JSON log line."""
    alert = {
        "ALERT": f"Device {monitor_id} is down!",
        "time": datetime.now(timezone.utc).isoformat(),
    }
    logger.critical(json.dumps(alert))


async def _countdown(monitor_id: str) -> None:
    """Each monitor gets its own countdown coroutine that sleeps for its timeout. 
    
    A heartbeat cancels that coroutine and starts a fresh one. If a
    countdown is ever allowed to finish, the device is marked DOWN and an alert
    fires.
    """
    await asyncio.sleep(_monitors[monitor_id].timeout)
    _monitors[monitor_id].status = Status.DOWN
    _fire_alert(monitor_id)


def _start_timer(monitor_id: str) -> None:
    """Cancel any running countdown for this monitor and start a fresh one."""
    if monitor_id in _tasks:
        _tasks[monitor_id].cancel()
    _monitors[monitor_id].status = Status.ACTIVE
    _tasks[monitor_id] = asyncio.create_task(_countdown(monitor_id))


def create(monitor_id: str, timeout: int, alert_email: str) -> Monitor:
    """Register a new monitor and start its countdown."""
    if monitor_id in _monitors:
        raise MonitorAlreadyExists(monitor_id)
    _monitors[monitor_id] = Monitor(id=monitor_id, timeout=timeout, alert_email=alert_email)
    _start_timer(monitor_id)
    return _monitors[monitor_id]


def heartbeat(monitor_id: str) -> Monitor:
    """Reset a monitor's timer (also resumes a paused or revives a down monitor)."""
    if monitor_id not in _monitors:
        raise MonitorNotFound(monitor_id)
    _start_timer(monitor_id)
    return _monitors[monitor_id]


def pause(monitor_id: str) -> Monitor:
    """Stop a monitor's countdown so no alert fires until the next heartbeat."""
    if monitor_id not in _monitors:
        raise MonitorNotFound(monitor_id)
    if monitor_id in _tasks:
        _tasks[monitor_id].cancel()
    _monitors[monitor_id].status = Status.PAUSED
    return _monitors[monitor_id]


def get(monitor_id: str) -> Monitor:
    """Return a single monitor, or raise if it does not exist."""
    if monitor_id not in _monitors:
        raise MonitorNotFound(monitor_id)
    return _monitors[monitor_id]


def list_all() -> list[Monitor]:
    """Return every monitor currently being tracked."""
    return list(_monitors.values())


def cancel_all() -> None:
    """Cancel all running countdowns (used on application shutdown)."""
    for task in _tasks.values():
        task.cancel()
