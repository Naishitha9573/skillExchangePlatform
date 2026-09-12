from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from jose import jwt
from sqlalchemy import create_engine, text
from starlette.websockets import WebSocketDisconnect

import app.db as database_module
from app.core.config import settings
from app.db import initialize_database
from conftest import auth


def test_expired_and_wrong_token_type_rejected(client, people):
    for payload in ({'sub':str(people['ids'][0]),'exp':datetime.now(timezone.utc)-timedelta(seconds=5),'type':'access'},
                    {'sub':str(people['ids'][0]),'exp':datetime.now(timezone.utc)+timedelta(minutes=5),'type':'oauth_state'}):
        token=jwt.encode(payload,settings.SECRET_KEY,algorithm='HS256')
        assert client.get('/api/v1/sessions',headers={'Authorization':f'Bearer {token}'}).status_code == 401
        with client.websocket_connect('/api/v1/ws') as socket:
            socket.send_json({'type':'auth','token':token})
            with pytest.raises(WebSocketDisconnect) as closed:
                socket.receive_json()
            assert closed.value.code == 4401


def test_google_callback_is_bound_to_browser_and_verified_email(client, monkeypatch):
    monkeypatch.setattr(settings,'GOOGLE_CLIENT_ID','test-client')
    monkeypatch.setattr(settings,'GOOGLE_CLIENT_SECRET','test-only-placeholder')
    monkeypatch.setattr(settings,'GOOGLE_REDIRECT_URI','http://localhost:5173/auth/google/callback')
    assert client.get('/api/v1/auth/providers').json()['google'] is True
    state=parse_qs(urlparse(client.get('/api/v1/auth/google/authorize').json()['authorization_url']).query)['state'][0]
    assert client.cookies.get('skillswap_oauth_state') == state
    assert client.post('/api/v1/auth/google/callback',json={'state':'mismatch','code':'test-code'}).status_code == 400

    class GoogleClient:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def post(self, url, data):
            return httpx.Response(200,json={'access_token':'test-google-token'},request=httpx.Request('POST',url))
        def get(self,url,headers):
            return httpx.Response(200,json={'email':'google-user@example.com','email_verified':True,'name':'Google Learner'},request=httpx.Request('GET',url))

    monkeypatch.setattr('app.main.httpx.Client',GoogleClient)
    response=client.post('/api/v1/auth/google/callback',json={'state':state,'code':'test-code'})
    assert response.status_code == 200, response.text
    assert response.json()['user']['full_name'] == 'Google Learner'
    assert not client.cookies.get('skillswap_oauth_state')
    assert client.post('/api/v1/auth/google/callback',json={'state':state,'code':'test-code'}).status_code == 400


def test_notification_and_review_ownership(client, people):
    client.post('/api/v1/messages',headers=auth(people),json={'receiver_id':people['ids'][1],'body':'hello'})
    notification=client.get('/api/v1/notifications',headers=auth(people,1)).json()[0]
    assert client.patch(f"/api/v1/notifications/{notification['id']}/read",headers=auth(people,2)).status_code == 404
    assert client.post(f"/api/v1/ratings/{people['swap']}",headers=auth(people),json={'score':5}).status_code == 400
    assert client.get('/api/v1/skills/mine',headers=auth(people)).json()[0]['owner_id'] == people['ids'][0]


def test_original_database_upgrade_preserves_history(tmp_path, monkeypatch):
    legacy=create_engine(f"sqlite:///{(tmp_path / 'legacy.db').as_posix()}")
    now='2026-01-01 10:00:00'
    with legacy.begin() as connection:
        connection.execute(text('CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(255), password_hash VARCHAR(255), full_name VARCHAR(120), bio TEXT, location VARCHAR(120), avatar_url VARCHAR(500), created_at DATETIME)'))
        connection.execute(text('CREATE TABLE messages (id INTEGER PRIMARY KEY, sender_id INTEGER, receiver_id INTEGER, body TEXT, created_at DATETIME)'))
        connection.execute(text("INSERT INTO users VALUES (1,'one@example.com',NULL,'One','','','',:now),(2,'two@example.com',NULL,'Two','','','',:now)"),{'now':now})
        connection.execute(text("INSERT INTO messages VALUES (1,1,2,'Original message',:now)"),{'now':now})
    monkeypatch.setattr(database_module,'engine',legacy)
    initialize_database();initialize_database()
    with legacy.connect() as connection:
        row=connection.execute(text('SELECT body, conversation_id, read_at, client_id FROM messages')).one()
        assert row.body == 'Original message' and row.conversation_id and row.read_at and row.client_id is None
        assert connection.execute(text('SELECT COUNT(*) FROM conversations')).scalar() == 1
        assert connection.execute(text('SELECT COUNT(*) FROM profiles')).scalar() == 2
    legacy.dispose()
