import json
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manages active WebSocket connections for live forensic job feeds."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        self.active_connections[job_id].add(websocket)

    def disconnect(self, job_id: str, websocket: WebSocket):
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def broadcast_job_event(self, job_id: str, event_data: dict):
        if job_id in self.active_connections:
            payload = json.dumps(event_data)
            for connection in list(self.active_connections[job_id]):
                try:
                    await connection.send_text(payload)
                except Exception:
                    self.disconnect(job_id, connection)


manager = ConnectionManager()


@router.websocket("/ws/jobs/{job_id}")
async def job_live_feed(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint streaming live artifacts, execution progress,
    and threat alerts for a specific forensic triage job.
    """
    await manager.connect(job_id, websocket)
    try:
        # Send initial connected greeting
        await websocket.send_json({
            "event": "connected",
            "job_id": job_id,
            "message": "Subscribed to live job event stream"
        })
        while True:
            # Keep alive / receive client pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(job_id, websocket)
