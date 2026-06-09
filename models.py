"""Data models for the API.

Pydantic models are used for request and response validation, 
while the dataclass is used for internal state management.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field


class Status(str, Enum):
    """The possible states of a monitor."""

    ACTIVE = "active"    #counting down; will alert if timer reaches zero
    PAUSED = "paused"    #snoozed by a technitian; hence no alerts are sent
    DOWN = "down"        #the timer expires and an alert is sent


@dataclass
class Monitor:
    """Represents a monitor with its state and configuration."""

    id: str
    timeout: int
    alert_email: str
    status: Status = Status.ACTIVE


class RegisterRequest(BaseModel):
    """Request model for creating a new monitor."""

    id: str = Field(..., min_length=1, examples=["device-1"])
    timeout: int = Field(..., gt=0, description="Countdown in seconds", examples=[60])
    alert_email: str = Field(..., examples=["admin@critmon.com"])


class MonitorView(BaseModel):
    """Public, read-only view of a monitor returned by the API."""

    id: str
    timeout: int
    alert_email: str
    status: Status

    @classmethod
    def of(cls, monitor: Monitor) -> MonitorView:
        """Creates a MonitorView from an internal Monitor record."""
        return cls(
            id=monitor.id,
            timeout=monitor.timeout,
            alert_email=monitor.alert_email,
            status=monitor.status,
        )

  
class MessageResponse(BaseModel):
    """A confirmation message returned after creating, updating, or pausing a monitor."""

    message: str
    monitor: MonitorView | None = None
