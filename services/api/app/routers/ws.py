import uuid
from enum import Enum

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter(prefix="/ws", tags=["websocket"])


class WSEventType(str, Enum):
    ANSWER_SUBMITTED = "answer.submitted"
    QUESTION_SUGGESTED = "question.suggested"
    FINDING_DETECTED = "finding.detected"
    ERROR = "error"


class WSMessage(BaseModel):
    event: WSEventType
    payload: dict


class ConnectionManager:
    def __init__(self):
        # interview_id -> list of active websocket connections
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, interview_id: str, ws: WebSocket):
        await ws.accept()
        self._connections.setdefault(interview_id, []).append(ws)

    def disconnect(self, interview_id: str, ws: WebSocket):
        connections = self._connections.get(interview_id, [])
        if ws in connections:
            connections.remove(ws)

    async def broadcast(self, interview_id: str, message: WSMessage):
        for ws in list(self._connections.get(interview_id, [])):
            try:
                await ws.send_text(message.model_dump_json())
            except Exception:
                self.disconnect(interview_id, ws)


manager = ConnectionManager()


@router.websocket("/interviews/{interview_id}")
async def interview_ws(interview_id: uuid.UUID, websocket: WebSocket):
    sid = str(interview_id)
    await manager.connect(sid, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("event")
            payload = data.get("payload", {})

            if event == WSEventType.ANSWER_SUBMITTED:
                # Fast path: echo back to all clients so frontend stays in sync
                # Agent will pick this up via Kafka consumer (slow path)
                msg = WSMessage(event=WSEventType.ANSWER_SUBMITTED, payload=payload)
                await manager.broadcast(sid, msg)

            else:
                await websocket.send_json(
                    WSMessage(event=WSEventType.ERROR, payload={"detail": f"Unknown event: {event}"}).model_dump()
                )

    except WebSocketDisconnect:
        manager.disconnect(sid, websocket)
