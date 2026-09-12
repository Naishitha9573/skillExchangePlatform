"""Every test uses a temporary database; never imports the app with a real DB URL."""
import os
import secrets
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
_temporary = tempfile.TemporaryDirectory(prefix="skillswap-tests-")
_database = Path(_temporary.name) / "test.db"
os.environ.update(DATABASE_URL=f"sqlite:///{_database.as_posix()}", SECRET_KEY=secrets.token_urlsafe(48),
                  GOOGLE_CLIENT_ID="", GOOGLE_CLIENT_SECRET="", GEMINI_API_KEY="", TURN_SECRET="", TURN_URLS="")

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.auth import create_token  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.models import Profile, Skill, SwapRequest, User  # noqa: E402


@pytest.fixture
def client():
    assert Path(engine.url.database).resolve() == _database.resolve()
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session", autouse=True)
def close_test_database():
    yield
    engine.dispose()
    _temporary.cleanup()


@pytest.fixture
def people(client):
    with SessionLocal() as db:
        users = [User(email=f"{name.lower().replace(' ', '')}@example.com", full_name=name, profile=Profile()) for name in ("Alex Morgan", "Jordan Rivera", "Third Member")]
        db.add_all(users)
        db.flush()
        skills = [Skill(owner_id=u.id, title=title, description="Learn together through practical examples", type="Offering", category="Technology")
                  for u, title in zip(users, ("React", "Python", "SQL"))]
        db.add_all(skills)
        db.flush()
        swap = SwapRequest(requester_id=users[0].id, receiver_id=users[1].id, offered_skill_id=skills[0].id, requested_skill_id=skills[1].id, status="accepted")
        db.add(swap)
        db.commit()
        return {"ids": [u.id for u in users], "tokens": [create_token(u.id) for u in users], "swap": swap.id, "skills": [s.id for s in skills]}


def auth(people, index=0):
    return {"Authorization": f"Bearer {people['tokens'][index]}"}


def receive_type(socket, kind):
    for _ in range(40):
        event = socket.receive_json()
        if event["type"] == kind:
            return event
    raise AssertionError(f"Expected {kind}")


def socket_auth(socket, token):
    socket.send_json({"type": "auth", "token": token})
    return receive_type(socket, "ready")
