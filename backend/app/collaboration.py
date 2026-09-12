"""Chat and scheduling operations on the existing relational models.

REST remains the durable source of truth; the realtime hub only delivers events.
All functions that mutate data commit before publishing an event.
"""
import base64
import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response
from sqlalchemy import and_, func, or_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.auth import current_user
from app.core.config import settings
from app.db import get_db
from app.models import Conversation, LearningSession, Message, Notification, SwapRequest, User
from app.schemas import ConversationCreate, ConversationRead, MessageCreate, SessionCreate, SessionStatus
from app.realtime import hub

router = APIRouter(prefix="/api/v1", tags=["Collaboration"])


def utc_iso(value):
    return value.replace(tzinfo=timezone.utc).isoformat() if value else None


def utc_naive(value):
    # Existing clients sent naive UTC. New clients always send an explicit offset.
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value


def notify(db, user_id, title, body, kind="info"):
    db.add(Notification(user_id=user_id, title=title, body=body, kind=kind))


def pair_filter(first, second):
    return or_(and_(SwapRequest.requester_id == first, SwapRequest.receiver_id == second),
               and_(SwapRequest.requester_id == second, SwapRequest.receiver_id == first))


def conversation_for(db, first_id, second_id):
    one, two = sorted((first_id, second_id))
    if one == two:
        raise HTTPException(400, "Choose another member")
    row = db.query(Conversation).filter_by(participant_one_id=one, participant_two_id=two).first()
    if row:
        return row
    if not db.query(SwapRequest.id).filter(pair_filter(one, two), SwapRequest.status.in_(["pending", "accepted", "completed"])).first():
        raise HTTPException(403, "Propose or accept a swap before starting a conversation")
    try:
        with db.begin_nested():
            row = Conversation(participant_one_id=one, participant_two_id=two)
            db.add(row)
            db.flush()
    except IntegrityError:
        row = db.query(Conversation).filter_by(participant_one_id=one, participant_two_id=two).one()
    return row


def owned_conversation(db, conversation_id, user_id):
    row = db.query(Conversation).filter(Conversation.id == conversation_id,
        or_(Conversation.participant_one_id == user_id, Conversation.participant_two_id == user_id)).first()
    if not row:
        raise HTTPException(404, "Conversation not found")
    return row


def message_json(m):
    return {"id": m.id, "conversation_id": m.conversation_id, "body": m.body,
            "sender_id": m.sender_id, "receiver_id": m.receiver_id,
            "created_at": utc_iso(m.created_at), "read_at": utc_iso(m.read_at), "client_id": m.client_id}


def persist_message(db, user_id, data):
    client_id = str(data.client_id) if data.client_id else None
    if client_id:
        existing = db.query(Message).filter_by(sender_id=user_id, client_id=client_id).first()
        if existing:
            if existing.receiver_id != data.receiver_id or existing.body != data.body:
                raise HTTPException(409, "This message identifier was already used")
            return message_json(existing), False
    if data.receiver_id == user_id or not db.get(User, data.receiver_id):
        raise HTTPException(404, "Member not found")
    conversation = conversation_for(db, user_id, data.receiver_id)
    m = Message(conversation_id=conversation.id, sender_id=user_id, receiver_id=data.receiver_id,
                body=data.body, client_id=client_id)
    db.add(m)
    conversation.updated_at = datetime.utcnow()
    notify(db, data.receiver_id, "New message", f"{db.get(User, user_id).full_name} sent you a message.", "message")
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(Message).filter_by(sender_id=user_id, client_id=client_id).first() if client_id else None
        if not existing or existing.receiver_id != data.receiver_id or existing.body != data.body:
            raise HTTPException(409, "Please retry this message")
        return message_json(existing), False
    return message_json(m), True


async def message_event(message):
    await hub.publish([message["sender_id"], message["receiver_id"]], {"type": "message.created", "message": message})
    await hub.publish([message["receiver_id"]], {"type": "notifications.changed"})


@router.post("/messages")
def send_message(data: MessageCreate, tasks: BackgroundTasks, user: User = Depends(current_user), db: Session = Depends(get_db)):
    message, created = persist_message(db, user.id, data)
    if created:
        tasks.add_task(message_event, message)
    return message


@router.get("/messages/{other_id}")
def messages(other_id: int, before_id: int | None = Query(None, gt=0), limit: int = Query(100, ge=1, le=100),
             user: User = Depends(current_user), db: Session = Depends(get_db)):
    one, two = sorted((user.id, other_id))
    conversation = db.query(Conversation).filter_by(participant_one_id=one, participant_two_id=two).first()
    if not conversation:
        return []
    owned_conversation(db, conversation.id, user.id)
    query = db.query(Message).filter(Message.conversation_id == conversation.id)
    if before_id:
        query = query.filter(Message.id < before_id)
    return [message_json(m) for m in reversed(query.order_by(Message.id.desc()).limit(limit).all())]


@router.get("/conversations")
def conversations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    # Aggregate last-message and unread counts in one query instead of loading histories.
    last = db.query(Message.conversation_id, func.max(Message.id).label("last_id")).group_by(Message.conversation_id).subquery()
    unread = db.query(Message.conversation_id, func.count(Message.id).label("count")).filter(
        Message.receiver_id == user.id, Message.read_at.is_(None)).group_by(Message.conversation_id).subquery()
    rows = db.query(Conversation, Message, func.coalesce(unread.c.count, 0)).options(
        joinedload(Conversation.participant_one), joinedload(Conversation.participant_two)).outerjoin(
        last, last.c.conversation_id == Conversation.id).outerjoin(Message, Message.id == last.c.last_id).outerjoin(
        unread, unread.c.conversation_id == Conversation.id).filter(
        or_(Conversation.participant_one_id == user.id, Conversation.participant_two_id == user.id)).order_by(Conversation.updated_at.desc()).all()
    result = []
    for c, m, count in rows:
        partner = c.participant_two if c.participant_one_id == user.id else c.participant_one
        result.append({"id": c.id, "partner": {"id": partner.id, "full_name": partner.full_name, "avatar_url": partner.avatar_url},
                       "last_message": message_json(m) if m else None, "unread_count": count, "updated_at": utc_iso(c.updated_at)})
    return result


@router.post("/conversations")
def open_conversation(data: ConversationCreate, tasks: BackgroundTasks, user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = conversation_for(db, user.id, data.participant_id)
    db.commit()
    tasks.add_task(hub.publish, [user.id, data.participant_id], {"type": "conversations.changed"})
    return {"id": c.id}


@router.post("/conversations/{conversation_id}/read")
def read_conversation(conversation_id: int, data: ConversationRead, tasks: BackgroundTasks,
                      user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = owned_conversation(db, conversation_id, user.id)
    now = datetime.utcnow()
    count = db.query(Message).filter(Message.conversation_id == c.id, Message.receiver_id == user.id,
        Message.id <= data.through_id, Message.read_at.is_(None)).update({Message.read_at: now}, synchronize_session=False)
    db.commit()
    if count:
        tasks.add_task(hub.publish, [c.participant_one_id, c.participant_two_id], {
            "type": "messages.read", "conversation_id": c.id, "reader_id": user.id,
            "through_id": data.through_id, "read_at": utc_iso(now)})
    return {"read_count": count}


@router.get("/partners")
def partners(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(SwapRequest).options(joinedload(SwapRequest.requester), joinedload(SwapRequest.receiver),
        joinedload(SwapRequest.offered_skill), joinedload(SwapRequest.requested_skill)).filter(
        or_(SwapRequest.requester_id == user.id, SwapRequest.receiver_id == user.id),
        SwapRequest.status.in_(["accepted", "completed"])).order_by(SwapRequest.updated_at.desc()).all()
    return [{"swap_id": s.id, "status": s.status, "partner": {
        "id": s.receiver_id if s.requester_id == user.id else s.requester_id,
        "full_name": s.receiver.full_name if s.requester_id == user.id else s.requester.full_name},
        "topics": list(dict.fromkeys([s.offered_skill.title, s.requested_skill.title]))} for s in rows]


def owned_session(db, session_id, user_id):
    s = db.query(LearningSession).options(joinedload(LearningSession.organizer), joinedload(LearningSession.participant)).filter(
        LearningSession.id == session_id, or_(LearningSession.organizer_id == user_id, LearningSession.participant_id == user_id)).first()
    if not s:
        raise HTTPException(404, "Session not found")
    return s


def call_available(s):
    now = datetime.utcnow()
    return s.status == "scheduled" and s.scheduled_at - timedelta(minutes=15) <= now <= s.scheduled_at + timedelta(minutes=s.duration_minutes + 60)


def session_json(s):
    return {"id": s.id, "swap_id": s.swap_id, "topic": s.topic, "scheduled_at": utc_iso(s.scheduled_at),
            "duration_minutes": s.duration_minutes, "meeting_link": s.meeting_link, "status": s.status,
            "organizer": {"id": s.organizer_id, "name": s.organizer.full_name},
            "participant": {"id": s.participant_id, "name": s.participant.full_name},
            "call_available": call_available(s), "call_opens_at": utc_iso(s.scheduled_at - timedelta(minutes=15)),
            "created_at": utc_iso(s.created_at), "updated_at": utc_iso(s.updated_at)}


def lock_calendars(db, user_ids):
    # SQLite requires a write reservation BEFORE the conflict query. PostgreSQL
    # serializes bookings on the two user rows, always in the same order.
    if db.bind.dialect.name == "sqlite":
        db.rollback()
        db.execute(text("BEGIN IMMEDIATE"))
    else:
        db.query(User).filter(User.id.in_(user_ids)).order_by(User.id).with_for_update().all()


def validate_booking(db, user_ids, start, duration, exclude_id=None):
    if start <= datetime.utcnow():
        raise HTTPException(400, "Choose a date and time in the future")
    end = start + timedelta(minutes=duration)
    rows = db.query(LearningSession).filter(LearningSession.status == "scheduled",
        or_(LearningSession.organizer_id.in_(user_ids), LearningSession.participant_id.in_(user_ids)),
        LearningSession.scheduled_at < end, LearningSession.scheduled_at > start - timedelta(minutes=180))
    if exclude_id:
        rows = rows.filter(LearningSession.id != exclude_id)
    if any(s.scheduled_at + timedelta(minutes=s.duration_minutes) > start for s in rows):
        raise HTTPException(409, "This time overlaps another session for you or your partner. Choose a different time.")


async def session_event(session, close_call=False):
    ids = [session["organizer"]["id"], session["participant"]["id"]]
    if close_call:
        await hub.close_room(session["id"], "This session was updated. Return to your schedule.")
    await hub.publish(ids, {"type": "session.updated", "session": session})
    await hub.publish(ids, {"type": "notifications.changed"})
    await hub.publish(ids, {"type": "swaps.changed"})


@router.post("/sessions")
def create_session(data: SessionCreate, tasks: BackgroundTasks, user: User = Depends(current_user), db: Session = Depends(get_db)):
    uid = user.id
    if data.participant_id == uid:
        raise HTTPException(400, "Choose another participant")
    lock_calendars(db, [uid, data.participant_id])
    query = db.query(SwapRequest).filter(pair_filter(uid, data.participant_id), SwapRequest.status.in_(["accepted", "completed"]))
    swap = query.filter(SwapRequest.id == data.swap_id).first() if data.swap_id else query.order_by(SwapRequest.updated_at.desc()).first()
    if not swap:
        raise HTTPException(403, "Accept a swap with this partner before booking a session")
    start = utc_naive(data.scheduled_at)
    validate_booking(db, [uid, data.participant_id], start, data.duration_minutes)
    values = data.model_dump(exclude={"scheduled_at", "swap_id"})
    s = LearningSession(organizer_id=uid, scheduled_at=start, swap_id=swap.id, **values)
    db.add(s)
    notify(db, data.participant_id, "Learning session booked", f"{user.full_name} booked {data.topic}.", "session")
    db.commit()
    result = session_json(s)
    tasks.add_task(session_event, result)
    return result


@router.get("/sessions")
def list_sessions(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(LearningSession).options(joinedload(LearningSession.organizer), joinedload(LearningSession.participant)).filter(
        or_(LearningSession.organizer_id == user.id, LearningSession.participant_id == user.id)).order_by(LearningSession.scheduled_at.asc()).all()
    return [session_json(s) for s in rows]


@router.get("/sessions/{session_id}")
def get_session(session_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return session_json(owned_session(db, session_id, user.id))


@router.patch("/sessions/{session_id}")
def update_session(session_id: int, data: SessionStatus, tasks: BackgroundTasks, user: User = Depends(current_user), db: Session = Depends(get_db)):
    uid = user.id
    s = owned_session(db, session_id, uid)
    pair = [s.organizer_id, s.participant_id]
    lock_calendars(db, pair)
    s = owned_session(db, session_id, uid)
    changes = data.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(400, "No session changes supplied")
    if s.status != "scheduled":
        raise HTTPException(409, f"A {s.status} session cannot be changed")
    scheduling = any(k in changes for k in ("scheduled_at", "duration_minutes", "topic"))
    if scheduling and data.status in {"cancelled", "completed"}:
        raise HTTPException(400, "Reschedule or change status in separate actions")
    if scheduling:
        start = utc_naive(data.scheduled_at) if data.scheduled_at else s.scheduled_at
        validate_booking(db, pair, start, data.duration_minutes or s.duration_minutes, s.id)
        if data.scheduled_at:
            changes["scheduled_at"] = start
    if data.status == "completed" and s.scheduled_at > datetime.utcnow():
        raise HTTPException(400, "A session can be completed only after its scheduled start")
    for key, value in changes.items():
        setattr(s, key, value)
    db.flush()
    if data.status == "completed" and s.swap_id:
        swap = db.get(SwapRequest, s.swap_id)
        other_sessions = db.query(LearningSession.id).filter(LearningSession.swap_id == s.swap_id,
            LearningSession.id != s.id, LearningSession.status == "scheduled").first()
        if swap.status == "accepted" and not other_sessions:
            swap.status = "completed"
    action = "rescheduled" if scheduling else s.status
    for recipient in pair:
        notify(db, recipient, f"Session {action}", f"{s.topic} was {action}.", "session")
    db.commit()
    result = session_json(s)
    tasks.add_task(session_event, result, scheduling or s.status != "scheduled")
    return {**result, "message": "Session updated"}


@router.get("/sessions/{session_id}/ice-config")
def ice_config(session_id: int, response: Response, user: User = Depends(current_user), db: Session = Depends(get_db)):
    s = owned_session(db, session_id, user.id)
    if not call_available(s):
        raise HTTPException(409, "Calls open 15 minutes before the session and close one hour after its end")
    servers = []
    stun = [url.strip() for url in settings.STUN_URLS.split(",") if url.strip()]
    if stun:
        servers.append({"urls": stun})
    if settings.TURN_URLS and settings.TURN_SECRET:
        username = f"{int(time.time()) + settings.TURN_CREDENTIAL_TTL_SECONDS}:{user.id}"
        credential = base64.b64encode(hmac.new(settings.TURN_SECRET.encode(), username.encode(), hashlib.sha1).digest()).decode()
        servers.append({"urls": [url.strip() for url in settings.TURN_URLS.split(",") if url.strip()], "username": username, "credential": credential})
    response.headers["Cache-Control"] = "no-store"
    return {"iceServers": servers}
