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