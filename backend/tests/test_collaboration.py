from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from starlette.websockets import WebSocketDisconnect

from app.db import SessionLocal, initialize_database
from app.models import LearningSession, Message, Notification, SwapRequest
from app.realtime import hub
from conftest import auth, receive_type, socket_auth


def booking(people, minutes=60, **overrides):
    return {"participant_id": people["ids"][1], "swap_id": people["swap"], "topic": "React hooks together",
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat(),
            "duration_minutes": 30, **overrides}


def test_auth_validation_and_existing_swap_flow(client):
    assert client.post('/api/v1/auth/register', json={"email":"a@example.com","full_name":"  ","password":"Password123"}).status_code == 422
    accounts = []
    for name in ("Alex", "Jordan"):
        response = client.post('/api/v1/auth/register', json={"email":f"{name.lower()}@example.com","full_name":name,"password":"Password123"})
        assert response.status_code == 200, response.text
        accounts.append(response.json())
    headers = [{"Authorization": f"Bearer {a['access_token']}"} for a in accounts]
    assert client.post('/api/v1/auth/login',json={"email":"alex@example.com","password":"wrong"}).status_code == 401
    skills = [client.post('/api/v1/skills',headers=h,json={"title":title,"type":"Offering","category":"Technology","description":"Practical learning"}).json() for h,title in zip(headers,("React","Python"))]
    request = client.post('/api/v1/swaps',headers=headers[0],json={"receiver_id":accounts[1]['user']['id'],"offered_skill_id":skills[0]['id'],"requested_skill_id":skills[1]['id']})
    assert request.status_code == 200, request.text
    sid = request.json()['id']
    assert client.patch(f'/api/v1/swaps/{sid}',headers=headers[0],json={"status":"accepted"}).status_code == 403
    assert client.patch(f'/api/v1/swaps/{sid}',headers=headers[1],json={"status":"accepted"}).status_code == 200
    assert len(client.get('/api/v1/conversations',headers=headers[0]).json()) == 1
    assert client.delete(f"/api/v1/skills/{skills[0]['id']}",headers=headers[0]).status_code == 409


def test_chat_persistence_unread_ownership_and_idempotency(client, people):
    data = {"receiver_id":people['ids'][1],"body":"  Hello Jordan!  ","client_id":str(uuid4())}
    with client.websocket_connect('/api/v1/ws') as a, client.websocket_connect('/api/v1/ws') as b, client.websocket_connect('/api/v1/ws') as outsider:
        for index,socket in enumerate((a,b,outsider)):
            socket_auth(socket,people['tokens'][index])
        message = client.post('/api/v1/messages',headers=auth(people),json=data)
        assert message.status_code == 200, message.text
        m = message.json()
        assert m['body'] == 'Hello Jordan!'
        assert m['created_at'].endswith('+00:00')
        assert receive_type(a,'message.created')['message']['id'] == m['id']
        assert receive_type(b,'message.created')['message']['id'] == m['id']
        outsider.send_json({"type":"ping"})
        assert outsider.receive_json()['type'] == 'pong'
        assert client.get('/api/v1/conversations',headers=auth(people,1)).json()[0]['unread_count'] == 1
        assert client.get('/api/v1/conversations',headers=auth(people,2)).json() == []
        assert client.post(f"/api/v1/conversations/{m['conversation_id']}/read",headers=auth(people,2),json={"through_id":m['id']}).status_code == 404
        assert client.post(f"/api/v1/conversations/{m['conversation_id']}/read",headers=auth(people,1),json={"through_id":m['id']}).json()['read_count'] == 1
        assert receive_type(a,'messages.read')['reader_id'] == people['ids'][1]
        assert client.get('/api/v1/conversations',headers=auth(people,1)).json()[0]['unread_count'] == 0
        assert client.post('/api/v1/messages',headers=auth(people),json=data).json()['id'] == m['id']
        assert client.post('/api/v1/messages',headers=auth(people),json={**data,'body':'Different content'}).status_code == 409
    with SessionLocal() as db:
        assert db.query(Message).count() == 1
        assert db.query(Notification).filter_by(kind='message').count() == 1
    assert client.get(f"/api/v1/messages/{people['ids'][0]}",headers=auth(people,1)).json()[0]['read_at']


def test_websocket_send_and_reconnect_history(client, people):
    cid = str(uuid4())
    with client.websocket_connect('/api/v1/ws') as socket:
        socket_auth(socket,people['tokens'][0])
        socket.send_json({"type":"message.send","receiver_id":people['ids'][1],"body":"Sent on a socket","client_id":cid})
        assert receive_type(socket,'message.ack')['message']['client_id'] == cid
        socket.send_json({"type":"message.send","receiver_id":people['ids'][1],"body":"   "})
        assert receive_type(socket,'error')['request_type'] == 'message.send'
    with client.websocket_connect('/api/v1/ws') as socket:
        socket_auth(socket,people['tokens'][0])
        socket.send_json({"type":"message.send","receiver_id":people['ids'][1],"body":"Sent on a socket","client_id":cid})
        receive_type(socket,'message.ack')
    assert len(client.get(f"/api/v1/messages/{people['ids'][1]}",headers=auth(people)).json()) == 1


def test_unrelated_users_cannot_start_chat_or_book(client, people):
    assert client.post('/api/v1/messages',headers=auth(people,2),json={"receiver_id":people['ids'][0],"body":"Uninvited"}).status_code == 403
    assert client.post('/api/v1/conversations',headers=auth(people,2),json={"participant_id":people['ids'][0]}).status_code == 403
    assert client.post('/api/v1/sessions',headers=auth(people,2),json=booking(people)).status_code == 403
    assert client.post('/api/v1/sessions',headers=auth(people),json=booking(people,participant_id=people['ids'][0])).status_code == 400


@pytest.mark.parametrize('payload', [{}, {'type':'auth','token':'invalid'}, {'type':'message.send','body':'hi'}])
def test_unauthenticated_socket_rejected(client, payload):
    with client.websocket_connect('/api/v1/ws') as socket:
        socket.send_json(payload)
        with pytest.raises(WebSocketDisconnect) as closed:
            socket.receive_json()
        assert closed.value.code == 4401


def test_socket_origin_rejected(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect('/api/v1/ws',headers={'origin':'https://untrusted.example'}):
            pass


def test_schedule_validation_conflicts_reschedule_and_completion(client, people):
    assert client.post('/api/v1/sessions',headers=auth(people),json=booking(people,minutes=-10)).status_code == 400
    assert client.post('/api/v1/sessions',headers=auth(people),json=booking(people,topic='  ')).status_code == 422
    assert client.post('/api/v1/sessions',headers=auth(people),json=booking(people,duration_minutes=0)).status_code == 422
    created = client.post('/api/v1/sessions',headers=auth(people),json=booking(people))
    assert created.status_code == 200, created.text
    s = created.json(); sid = s['id']
    assert s['scheduled_at'].endswith('+00:00') and s['swap_id'] == people['swap']
    assert client.post('/api/v1/sessions',headers=auth(people),json=booking(people)).status_code == 409
    assert client.post('/api/v1/sessions',headers=auth(people,1),json=booking(people,participant_id=people['ids'][0])).status_code == 409
    assert client.get('/api/v1/sessions',headers=auth(people,2)).json() == []
    assert client.get(f'/api/v1/sessions/{sid}',headers=auth(people,2)).status_code == 404
    assert client.patch(f'/api/v1/sessions/{sid}',headers=auth(people,2),json={'status':'cancelled'}).status_code == 404
    assert client.patch(f'/api/v1/sessions/{sid}',headers=auth(people),json={'status':'completed'}).status_code == 400
    new_time = (datetime.now(timezone(timedelta(hours=5,minutes=30)))+timedelta(hours=3)).isoformat()
    assert client.patch(f'/api/v1/sessions/{sid}',headers=auth(people,1),json={'scheduled_at':new_time,'duration_minutes':60}).status_code == 200
    assert client.get(f'/api/v1/sessions/{sid}',headers=auth(people)).json()['duration_minutes'] == 60
    with SessionLocal() as db:
        db.get(LearningSession,sid).scheduled_at=datetime.utcnow()-timedelta(minutes=40);db.commit()
    assert client.patch(f'/api/v1/sessions/{sid}',headers=auth(people,1),json={'status':'completed'}).status_code == 200
    with SessionLocal() as db:
        assert db.get(SwapRequest,people['swap']).status == 'completed'
    assert client.patch(f'/api/v1/sessions/{sid}',headers=auth(people),json={'scheduled_at':new_time}).status_code == 409
    assert client.post(f"/api/v1/ratings/{people['swap']}",headers=auth(people),json={'score':5,'review':'A lovely exchange'}).status_code == 200
    assert client.post(f"/api/v1/ratings/{people['swap']}",headers=auth(people),json={'score':4}).status_code == 409


def test_concurrent_bookings_are_serialized(client, people):
    payload = booking(people)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(client.post,'/api/v1/sessions',headers=auth(people),json=payload) for _ in range(2)]
        codes = [f.result().status_code for f in futures]
    assert sorted(codes) == [200,409]


def test_private_call_signaling_cleanup_and_cancellation(client, people):
    s = client.post('/api/v1/sessions',headers=auth(people),json=booking(people,minutes=5)).json(); sid = s['id']
    assert client.get(f'/api/v1/sessions/{sid}/ice-config',headers=auth(people,2)).status_code == 404
    assert client.get(f'/api/v1/sessions/{sid}/ice-config',headers=auth(people)).status_code == 200
    with client.websocket_connect('/api/v1/ws') as a, client.websocket_connect('/api/v1/ws') as b, client.websocket_connect('/api/v1/ws') as outsider:
        for i,socket in enumerate((a,b,outsider)):
            socket_auth(socket,people['tokens'][i])
        outsider.send_json({'type':'call.join','session_id':sid})
        assert receive_type(outsider,'error')['message'] == 'Session not found'
        a.send_json({'type':'call.join','session_id':sid});receive_type(a,'call.waiting')
        b.send_json({'type':'call.join','session_id':sid})
        assert receive_type(a,'call.peer_ready')['initiator'] is True
        assert receive_type(b,'call.peer_ready')['initiator'] is False
        a.send_json({'type':'call.offer','session_id':sid,'description':{'type':'offer','sdp':'test-offer'}})
        assert receive_type(b,'call.offer')['description']['sdp'] == 'test-offer'
        b.send_json({'type':'call.answer','session_id':sid,'description':{'type':'answer','sdp':'test-answer'}})
        assert receive_type(a,'call.answer')['description']['sdp'] == 'test-answer'
        a.send_json({'type':'call.ice','session_id':sid,'candidate':{'candidate':'candidate:test','sdpMid':'0','sdpMLineIndex':0}})
        assert receive_type(b,'call.ice')['candidate']['sdpMid'] == '0'
        b.send_json({'type':'call.leave'});receive_type(a,'call.peer_left')
        b.send_json({'type':'call.join','session_id':sid});receive_type(a,'call.peer_ready');receive_type(b,'call.peer_ready')
        assert client.patch(f'/api/v1/sessions/{sid}',headers=auth(people),json={'status':'cancelled'}).status_code == 200
        receive_type(a,'call.closed');receive_type(b,'call.closed')
        a.send_json({'type':'call.join','session_id':sid});assert receive_type(a,'error')['request_type'] == 'call.join'
    assert not hub.rooms and not hub.users


def test_call_window_and_duplicate_tab(client, people):
    s = client.post('/api/v1/sessions',headers=auth(people),json=booking(people)).json()
    assert client.get(f"/api/v1/sessions/{s['id']}/ice-config",headers=auth(people)).status_code == 409
    with SessionLocal() as db:
        db.get(LearningSession,s['id']).scheduled_at=datetime.utcnow()+timedelta(minutes=5);db.commit()
    with client.websocket_connect('/api/v1/ws') as a, client.websocket_connect('/api/v1/ws') as duplicate:
        socket_auth(a,people['tokens'][0]);socket_auth(duplicate,people['tokens'][0])
        a.send_json({'type':'call.join','session_id':s['id']});receive_type(a,'call.waiting')
        duplicate.send_json({'type':'call.join','session_id':s['id']})
        assert 'another tab' in receive_type(duplicate,'error')['message']


def test_migration_is_idempotent_and_preserves_new_unread(client, people):
    sent = client.post('/api/v1/messages',headers=auth(people),json={'receiver_id':people['ids'][1],'body':'Keep me unread'}).json()
    initialize_database();initialize_database()
    with SessionLocal() as db:
        assert db.get(Message,sent['id']).read_at is None
        assert db.query(Message).count() == 1
