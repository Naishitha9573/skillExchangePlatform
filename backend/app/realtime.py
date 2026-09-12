"""Single-process realtime delivery and private WebRTC signaling.

Deploy one Uvicorn worker. A shared event bus/room registry is required before
scaling workers; database messages remain durable independently of this hub.
"""
import asyncio
import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from jose import jwt
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.auth import current_user, _secret_key
from app.core.config import settings
from app.db import SessionLocal
from app.schemas import MessageCreate

router = APIRouter()


@dataclass(eq=False)
class Connection:
    socket: WebSocket
    user_id: int
    queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(maxsize=256))
    room_id: int | None = None


class RealtimeHub:
    def __init__(self):
        self.users = defaultdict(set)
        self.rooms = {}

    async def emit(self, connection, event):
        try:
            connection.queue.put_nowait(event)
        except asyncio.QueueFull:
            await connection.socket.close(code=1013, reason="Reconnect to catch up")

    async def publish(self, user_ids, event):
        for uid in set(user_ids):
            for connection in tuple(self.users.get(uid, ())):
                await self.emit(connection, event)

    async def leave(self, connection):
        sid = connection.room_id
        connection.room_id = None
        if sid is None:
            return
        room = self.rooms.get(sid, {})
        if room.get(connection.user_id) is connection:
            room.pop(connection.user_id)
            for peer in tuple(room.values()):
                await self.emit(peer, {"type": "call.peer_left", "session_id": sid})
        if not room:
            self.rooms.pop(sid, None)

    async def close_room(self, session_id, reason):
        room = self.rooms.pop(session_id, {})
        for connection in room.values():
            connection.room_id = None
            await self.emit(connection, {"type": "call.closed", "session_id": session_id, "message": reason})

    async def join(self, connection, session_id):
        room = self.rooms.get(session_id, {})
        if connection.user_id in room and room[connection.user_id] is not connection:
            raise HTTPException(409, "You already joined this call in another tab or device")
        if connection.room_id == session_id:
            return
        await self.leave(connection)
        room = self.rooms.setdefault(session_id, {})
        if len(room) >= 2:
            raise HTTPException(403, "This private call is full")
        room[connection.user_id] = connection
        connection.room_id = session_id
        await self.emit(connection, {"type": "call.joined", "session_id": session_id})
        if len(room) == 2:
            first, second = room.values()
            await self.emit(second, {"type": "call.peer_ready", "session_id": session_id, "initiator": False})
            await self.emit(first, {"type": "call.peer_ready", "session_id": session_id, "initiator": True})
        else:
            await self.emit(connection, {"type": "call.waiting", "session_id": session_id})


hub = RealtimeHub()


def authenticate(token):
    with SessionLocal() as db:
        user = current_user(token=token, db=db)
        payload = jwt.decode(token, _secret_key(), algorithms=["HS256"])
        return user.id, payload["exp"]


def check_room(session_id, user_id):
    from app.collaboration import call_available, owned_session
    with SessionLocal() as db:
        session = owned_session(db, session_id, user_id)
        if not call_available(session):
            raise HTTPException(409, "This session is not open for a call")


def save_message(user_id, payload):
    from app.collaboration import persist_message
    data = MessageCreate.model_validate(payload)
    with SessionLocal() as db:
        return persist_message(db, user_id, data)


async def writer(connection):
    while True:
        event = await connection.queue.get()
        await asyncio.wait_for(connection.socket.send_json(event), timeout=10)


async def handle_event(connection, payload):
    from app.collaboration import message_event
    kind = payload.get("type")
    if kind == "ping":
        if connection.room_id is not None:
            try:
                await run_in_threadpool(check_room, connection.room_id, connection.user_id)
            except HTTPException as exc:
                await hub.close_room(connection.room_id, exc.detail)
        await hub.emit(connection, {"type": "pong"})
    elif kind == "message.send":
        message, created = await run_in_threadpool(save_message, connection.user_id, payload)
        if created:
            await message_event(message)
        await hub.emit(connection, {"type": "message.ack", "message": message})
    elif kind == "call.leave":
        await hub.leave(connection)
    elif kind in {"call.join", "call.offer", "call.answer", "call.ice"}:
        sid = payload.get("session_id")
        if not isinstance(sid, int) or isinstance(sid, bool) or sid < 1:
            raise HTTPException(400, "Invalid session identifier")
        await run_in_threadpool(check_room, sid, connection.user_id)
        if kind == "call.join":
            await hub.join(connection, sid)
            return
        if connection.room_id != sid or hub.rooms.get(sid, {}).get(connection.user_id) is not connection:
            raise HTTPException(403, "Join your session before signaling")
        event = {"type": kind, "session_id": sid}
        if kind == "call.ice":
            candidate = payload.get("candidate")
            if not isinstance(candidate, dict) or not isinstance(candidate.get("candidate"), str) or len(candidate["candidate"]) > 4096:
                raise HTTPException(400, "Invalid ICE candidate")
            event["candidate"] = {k: candidate[k] for k in ("candidate", "sdpMid", "sdpMLineIndex", "usernameFragment") if k in candidate}
        else:
            description = payload.get("description")
            if not isinstance(description, dict) or description.get("type") != kind.split(".")[1] or not isinstance(description.get("sdp"), str):
                raise HTTPException(400, "Invalid session description")
            event["description"] = {"type": description["type"], "sdp": description["sdp"]}
        for peer in tuple(hub.rooms.get(sid, {}).values()):
            if peer is not connection:
                await hub.emit(peer, event)
    else:
        raise HTTPException(400, "Unknown realtime event")


@router.websocket("/api/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Browsers send Origin; enforce the same explicit origin list as REST CORS.
    origin = websocket.headers.get("origin")
    if origin and origin not in settings.cors_origins:
        await websocket.close(code=4403)
        return
    await websocket.accept()
    connection = None
    writer_task = None
    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=10)
        if len(raw) > 4096:
            raise HTTPException(401, "Invalid authentication")
        auth = json.loads(raw)
        if not isinstance(auth, dict) or auth.get("type") != "auth" or not isinstance(auth.get("token"), str):
            raise HTTPException(401, "Authentication required")
        uid, expires = await run_in_threadpool(authenticate, auth["token"])
        if len(hub.users.get(uid, ())) >= 5:
            await websocket.close(code=4429, reason="Too many open tabs")
            return
        connection = Connection(websocket, uid)
        hub.users[uid].add(connection)
        writer_task = asyncio.create_task(writer(connection))
        await hub.emit(connection, {"type": "ready", "user_id": uid})
        recent = deque()
        while True:
            remaining = expires - time.time()
            if remaining <= 0:
                await websocket.close(code=4401, reason="Sign in again")
                break
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=min(45, remaining))
            except asyncio.TimeoutError:
                await websocket.close(code=4401 if time.time() >= expires else 1001, reason="Connection timed out")
                break
            if time.time() >= expires:
                await websocket.close(code=4401, reason="Sign in again")
                break
            if writer_task.done():
                break
            if len(raw.encode("utf-8")) > 65536:
                await websocket.close(code=1009, reason="Event too large")
                break
            now = time.monotonic()
            while recent and recent[0] < now - 10:
                recent.popleft()
            recent.append(now)
            if len(recent) > 180:
                await websocket.close(code=4429, reason="Too many events")
                break
            payload = {}
            try:
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise HTTPException(400, "Expected an event object")
                await handle_event(connection, payload)
            except (HTTPException, ValidationError, ValueError) as exc:
                await hub.emit(connection, {"type": "error", "message": exc.detail if isinstance(exc, HTTPException) else "Invalid event data",
                    "request_type": payload.get("type") if isinstance(payload, dict) else None,
                    "client_id": str(payload.get("client_id", ""))[:36] if isinstance(payload, dict) else None})
    except (HTTPException, ValueError, KeyError):
        await websocket.close(code=4401, reason="Invalid authentication")
    except (WebSocketDisconnect, asyncio.TimeoutError, RuntimeError):
        pass
    finally:
        if connection:
            await hub.leave(connection)
            hub.users[connection.user_id].discard(connection)
            if not hub.users[connection.user_id]:
                hub.users.pop(connection.user_id, None)
        if writer_task:
            writer_task.cancel()
            await asyncio.gather(writer_task, return_exceptions=True)
