from datetime import datetime
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor=dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def initialize_database():
    """Create new tables and upgrade the original SQLite schema in place."""
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    if not settings.DATABASE_URL.startswith("sqlite"):
        return

    inspector=inspect(engine)
    now=datetime.utcnow().isoformat(sep=" ")
    additions={
        "users": ["updated_at"],
        "skills": ["catalog_id", "updated_at"],
        "swap_requests": ["updated_at"],
        "messages": ["conversation_id", "updated_at"],
        "ratings": ["updated_at"],
        "notifications": ["updated_at"],
        "learning_sessions": ["updated_at"],
    }
    column_types={"updated_at":"DATETIME", "catalog_id":"INTEGER", "conversation_id":"INTEGER"}
    with engine.begin() as connection:
        for table, columns in additions.items():
            existing={column["name"] for column in inspector.get_columns(table)}
            for column in columns:
                if column not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {column_types[column]}"))
            if "updated_at" in columns:
                connection.execute(text(f"UPDATE {table} SET updated_at = :now WHERE updated_at IS NULL"), {"now":now})

        connection.execute(text("""
            INSERT OR IGNORE INTO skill_catalog (name, category, created_at, updated_at)
            SELECT title, category, MIN(created_at), :now FROM skills GROUP BY title, category
        """), {"now":now})
        connection.execute(text("""
            UPDATE skills SET catalog_id = (
                SELECT id FROM skill_catalog
                WHERE skill_catalog.name = skills.title AND skill_catalog.category = skills.category
            ) WHERE catalog_id IS NULL
        """))
        connection.execute(text("""
            INSERT OR IGNORE INTO profiles (user_id, bio, location, avatar_url, created_at, updated_at)
            SELECT id, COALESCE(bio, ''), COALESCE(location, ''), COALESCE(avatar_url, ''), created_at, :now FROM users
        """), {"now":now})
        connection.execute(text("""
            INSERT OR IGNORE INTO conversations (participant_one_id, participant_two_id, created_at, updated_at)
            SELECT DISTINCT MIN(sender_id, receiver_id), MAX(sender_id, receiver_id), MIN(created_at), :now
            FROM messages GROUP BY MIN(sender_id, receiver_id), MAX(sender_id, receiver_id)
        """), {"now":now})
        connection.execute(text("""
            UPDATE messages SET conversation_id = (
                SELECT id FROM conversations
                WHERE participant_one_id = MIN(messages.sender_id, messages.receiver_id)
                  AND participant_two_id = MAX(messages.sender_id, messages.receiver_id)
            ) WHERE conversation_id IS NULL
        """))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_skills_catalog_id ON skills (catalog_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_messages_conversation_id ON messages (conversation_id)"))
        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ix_swap_pending_pair
            ON swap_requests (requester_id, requested_skill_id) WHERE status = 'pending'
        """))

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()
