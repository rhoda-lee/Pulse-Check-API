"""Pulse-Check API; a Dead Man's Switch for remote devices.

The web layer: defines the FastAPI app and its routes and translates the
errors raised by the ``monitors`` module into HTTP responses.

Run:   uvicorn main:app --reload
Docs:  http://127.0.0.1:8000/docs
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

import monitors
from models import MessageResponse, MonitorView, RegisterRequest

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Cancel any running countdown tasks when the app shuts down."""
    yield
    monitors.cancel_all()


app = FastAPI(title="Pulse-Check API", version="1.0.0", lifespan=lifespan)


@app.post("/monitors", status_code=201, response_model=MessageResponse)
async def create_monitor(body: RegisterRequest) -> MessageResponse:
    """Register a monitor and start its countdown (User Story 1)."""
    try:
        monitor = monitors.create(body.id, body.timeout, body.alert_email)
    except monitors.MonitorAlreadyExists:
        raise HTTPException(status_code=409, detail=f"Monitor '{body.id}' already exists") from None
    return MessageResponse(
        message=f"Monitor '{monitor.id}' created; countdown started at {monitor.timeout}s.",
        monitor=MonitorView.of(monitor),
    )


@app.post("/monitors/{monitor_id}/heartbeat", response_model=MessageResponse)
async def heartbeat(monitor_id: str) -> MessageResponse:
    """Reset the countdown; also resumes or revives the monitor (User Story 2)."""
    try:
        monitor = monitors.heartbeat(monitor_id)
    except monitors.MonitorNotFound:
        raise HTTPException(status_code=404, detail=f"Monitor '{monitor_id}' not found") from None
    return MessageResponse(
        message=f"Heartbeat received; timer reset to {monitor.timeout}s.",
        monitor=MonitorView.of(monitor),
    )


@app.post("/monitors/{monitor_id}/pause", response_model=MessageResponse)
async def pause(monitor_id: str) -> MessageResponse:
    """Pause monitoring so no alert fires until the next heartbeat (Bonus)."""
    try:
        monitor = monitors.pause(monitor_id)
    except monitors.MonitorNotFound:
        raise HTTPException(status_code=404, detail=f"Monitor '{monitor_id}' not found") from None
    return MessageResponse(
        message=f"Monitor '{monitor.id}' paused; send a heartbeat to resume.",
        monitor=MonitorView.of(monitor),
    )


@app.get("/monitors", response_model=list[MonitorView])
async def list_monitors() -> list[MonitorView]:
    """List all monitors and their current status (Developer's Choice)."""
    return [MonitorView.of(m) for m in monitors.list_all()]


@app.get("/monitors/{monitor_id}", response_model=MonitorView)
async def get_monitor(monitor_id: str) -> MonitorView:
    """Get a single monitor's status (Developer's Choice)."""
    try:
        monitor = monitors.get(monitor_id)
    except monitors.MonitorNotFound:
        raise HTTPException(status_code=404, detail=f"Monitor '{monitor_id}' not found") from None
    return MonitorView.of(monitor)
