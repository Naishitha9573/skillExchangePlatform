from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db import Base

class User(Base):
    __tablename__ = "users"
    id=Column(Integer, primary_key=True)
    email=Column(String(255), unique=True, nullable=False, index=True)
    password_hash=Column(String(255), nullable=False)
    full_name=Column(String(120), nullable=False)
    bio=Column(Text, default="")
    location=Column(String(120), default="")
    avatar_url=Column(String(500), default="")
    created_at=Column(DateTime, default=datetime.utcnow)
    skills=relationship("Skill", back_populates="owner", cascade="all, delete-orphan")

class Skill(Base):
    __tablename__="skills"
    id=Column(Integer, primary_key=True)
    owner_id=Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title=Column(String(160), nullable=False)
    type=Column(String(20), nullable=False) # Offering / Requesting
    category=Column(String(60), nullable=False)
    description=Column(Text, nullable=False)
    tags=Column(String(500), default="")
    level=Column(String(30), default="Beginner")
    availability=Column(String(120), default="Flexible")
    created_at=Column(DateTime, default=datetime.utcnow)
    owner=relationship("User", back_populates="skills")

class SwapRequest(Base):
    __tablename__="swap_requests"
    id=Column(Integer, primary_key=True)
    requester_id=Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id=Column(Integer, ForeignKey("users.id"), nullable=False)
    offered_skill_id=Column(Integer, ForeignKey("skills.id"), nullable=False)
    requested_skill_id=Column(Integer, ForeignKey("skills.id"), nullable=False)
    message=Column(Text, default="")
    status=Column(String(20), default="pending", index=True)
    created_at=Column(DateTime, default=datetime.utcnow)
    requester=relationship("User", foreign_keys=[requester_id])
    receiver=relationship("User", foreign_keys=[receiver_id])
    offered_skill=relationship("Skill", foreign_keys=[offered_skill_id])
    requested_skill=relationship("Skill", foreign_keys=[requested_skill_id])

class Message(Base):
    __tablename__="messages"
    id=Column(Integer, primary_key=True)
    sender_id=Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id=Column(Integer, ForeignKey("users.id"), nullable=False)
    body=Column(Text, nullable=False)
    created_at=Column(DateTime, default=datetime.utcnow)
    sender=relationship("User", foreign_keys=[sender_id])
    receiver=relationship("User", foreign_keys=[receiver_id])

class Rating(Base):
    __tablename__="ratings"
    id=Column(Integer, primary_key=True)
    rater_id=Column(Integer, ForeignKey("users.id"), nullable=False)
    rated_id=Column(Integer, ForeignKey("users.id"), nullable=False)
    swap_id=Column(Integer, ForeignKey("swap_requests.id"), nullable=False)
    score=Column(Integer, nullable=False)
    review=Column(Text, default="")
    created_at=Column(DateTime, default=datetime.utcnow)
    __table_args__=(UniqueConstraint("rater_id","swap_id",name="uq_rating_rater_swap"),)

class Notification(Base):
    __tablename__="notifications"
    id=Column(Integer, primary_key=True)
    user_id=Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title=Column(String(160), nullable=False)
    body=Column(Text, nullable=False)
    kind=Column(String(40), default="info")
    read=Column(Integer, default=0)
    created_at=Column(DateTime, default=datetime.utcnow)
    user=relationship("User", foreign_keys=[user_id])

class LearningSession(Base):
    __tablename__="learning_sessions"
    id=Column(Integer, primary_key=True)
    organizer_id=Column(Integer, ForeignKey("users.id"), nullable=False)
    participant_id=Column(Integer, ForeignKey("users.id"), nullable=False)
    swap_id=Column(Integer, ForeignKey("swap_requests.id"), nullable=True)
    topic=Column(String(180), nullable=False)
    scheduled_at=Column(DateTime, nullable=False)
    duration_minutes=Column(Integer, default=60)
    meeting_link=Column(String(500), default="")
    status=Column(String(30), default="scheduled")
    created_at=Column(DateTime, default=datetime.utcnow)
    organizer=relationship("User", foreign_keys=[organizer_id])
    participant=relationship("User", foreign_keys=[participant_id])
