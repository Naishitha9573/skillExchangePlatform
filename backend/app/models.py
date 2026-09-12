from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db import Base

class TimestampMixin:
    created_at=Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class User(Base, TimestampMixin):
    __tablename__ = "users"
    id=Column(Integer, primary_key=True)
    email=Column(String(255), unique=True, nullable=False, index=True)
    password_hash=Column(String(255), nullable=False)
    full_name=Column(String(120), nullable=False)
    bio=Column(Text, default="")
    location=Column(String(120), default="")
    avatar_url=Column(String(500), default="")
    profile=relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    skills=relationship("Skill", back_populates="owner", cascade="all, delete-orphan")

class Profile(Base, TimestampMixin):
    __tablename__="profiles"
    id=Column(Integer, primary_key=True)
    user_id=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    bio=Column(Text, default="", nullable=False)
    location=Column(String(120), default="", nullable=False)
    avatar_url=Column(String(500), default="", nullable=False)
    user=relationship("User", back_populates="profile")

class SkillCatalog(Base, TimestampMixin):
    __tablename__="skill_catalog"
    id=Column(Integer, primary_key=True)
    name=Column(String(160), nullable=False)
    category=Column(String(60), nullable=False)
    __table_args__=(UniqueConstraint("name","category",name="uq_skill_catalog_name_category"),)
    listings=relationship("Skill", back_populates="catalog")

class Skill(Base, TimestampMixin):
    __tablename__="skills"
    id=Column(Integer, primary_key=True)
    owner_id=Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    catalog_id=Column(Integer, ForeignKey("skill_catalog.id", ondelete="RESTRICT"), nullable=True, index=True)
    # Legacy listing fields remain populated so existing API consumers keep their contract.
    title=Column(String(160), nullable=False)
    type=Column(String(20), nullable=False) # Offering / Requesting
    category=Column(String(60), nullable=False)
    description=Column(Text, nullable=False)
    tags=Column(String(500), default="")
    level=Column(String(30), default="Beginner")
    availability=Column(String(120), default="Flexible")
    owner=relationship("User", back_populates="skills")
    catalog=relationship("SkillCatalog", back_populates="listings")
    __table_args__=(
        CheckConstraint("type IN ('Offering','Requesting')", name="ck_skills_type"),
        CheckConstraint("level IN ('Beginner','Intermediate','Advanced')", name="ck_skills_level"),
    )

class SwapRequest(Base, TimestampMixin):
    __tablename__="swap_requests"
    id=Column(Integer, primary_key=True)
    requester_id=Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    receiver_id=Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    offered_skill_id=Column(Integer, ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False, index=True)
    requested_skill_id=Column(Integer, ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False, index=True)
    message=Column(Text, default="")
    status=Column(String(20), default="pending", index=True)
    requester=relationship("User", foreign_keys=[requester_id])
    receiver=relationship("User", foreign_keys=[receiver_id])
    offered_skill=relationship("Skill", foreign_keys=[offered_skill_id])
    requested_skill=relationship("Skill", foreign_keys=[requested_skill_id])
    __table_args__=(
        CheckConstraint("requester_id != receiver_id", name="ck_swap_distinct_users"),
        CheckConstraint("status IN ('pending','accepted','rejected','cancelled','completed')", name="ck_swap_status"),
        Index("ix_swap_pending_pair", "requester_id", "requested_skill_id", unique=True, sqlite_where=(status == "pending")),
    )

class Conversation(Base, TimestampMixin):
    __tablename__="conversations"
    id=Column(Integer, primary_key=True)
    participant_one_id=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    participant_two_id=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    participant_one=relationship("User", foreign_keys=[participant_one_id])
    participant_two=relationship("User", foreign_keys=[participant_two_id])
    messages=relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    __table_args__=(
        CheckConstraint("participant_one_id < participant_two_id", name="ck_conversation_ordered_participants"),
        UniqueConstraint("participant_one_id","participant_two_id",name="uq_conversation_participants"),
    )

class Message(Base, TimestampMixin):
    __tablename__="messages"
    id=Column(Integer, primary_key=True)
    conversation_id=Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True, index=True)
    sender_id=Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    receiver_id=Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    body=Column(Text, nullable=False)
    sender=relationship("User", foreign_keys=[sender_id])
    receiver=relationship("User", foreign_keys=[receiver_id])
    conversation=relationship("Conversation", back_populates="messages")

class Rating(Base, TimestampMixin):
    __tablename__="ratings"
    id=Column(Integer, primary_key=True)
    rater_id=Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    rated_id=Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    swap_id=Column(Integer, ForeignKey("swap_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    score=Column(Integer, nullable=False)
    review=Column(Text, default="")
    __table_args__=(
        CheckConstraint("rater_id != rated_id", name="ck_rating_distinct_users"),
        CheckConstraint("score BETWEEN 1 AND 5", name="ck_rating_score"),
        UniqueConstraint("rater_id","swap_id",name="uq_rating_rater_swap"),
    )

class Notification(Base, TimestampMixin):
    __tablename__="notifications"
    id=Column(Integer, primary_key=True)
    user_id=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title=Column(String(160), nullable=False)
    body=Column(Text, nullable=False)
    kind=Column(String(40), default="info")
    read=Column(Boolean, default=False, nullable=False)
    user=relationship("User", foreign_keys=[user_id])

class LearningSession(Base, TimestampMixin):
    __tablename__="learning_sessions"
    id=Column(Integer, primary_key=True)
    organizer_id=Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    participant_id=Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    swap_id=Column(Integer, ForeignKey("swap_requests.id", ondelete="SET NULL"), nullable=True, index=True)
    topic=Column(String(180), nullable=False)
    scheduled_at=Column(DateTime, nullable=False)
    duration_minutes=Column(Integer, default=60)
    meeting_link=Column(String(500), default="")
    status=Column(String(30), default="scheduled")
    organizer=relationship("User", foreign_keys=[organizer_id])
    participant=relationship("User", foreign_keys=[participant_id])
    __table_args__=(
        CheckConstraint("organizer_id != participant_id", name="ck_session_distinct_users"),
        CheckConstraint("duration_minutes BETWEEN 15 AND 180", name="ck_session_duration"),
        CheckConstraint("status IN ('scheduled','completed','cancelled')", name="ck_session_status"),
    )
