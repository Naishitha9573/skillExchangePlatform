"""Deterministic hackathon demo data.
Run: python seed.py --reset
"""
import argparse
from datetime import datetime, timedelta
from app.db import Base,engine,SessionLocal
from app.models import User,Skill,SwapRequest,Message,Rating,Notification,LearningSession
from app.auth import hash_password

Base.metadata.create_all(bind=engine)
parser=argparse.ArgumentParser(); parser.add_argument('--reset',action='store_true'); args=parser.parse_args()
db=SessionLocal()
if args.reset:
    for model in [Rating,Message,Notification,LearningSession,SwapRequest,Skill,User]:
        db.query(model).delete()
    db.commit()
if db.query(User).count()==0:
    users=[
      User(email="ananya@demo.com",password_hash=hash_password("demo123"),full_name="Ananya Rao",bio="Frontend developer who loves teaching React and learning backend engineering.",location="Bengaluru"),
      User(email="rahul@demo.com",password_hash=hash_password("demo123"),full_name="Rahul Verma",bio="Python, FastAPI and data mentor. Loves building practical projects.",location="Hyderabad"),
      User(email="meera@demo.com",password_hash=hash_password("demo123"),full_name="Meera Nair",bio="Graphic designer and language learner.",location="Kochi"),
      User(email="arjun@demo.com",password_hash=hash_password("demo123"),full_name="Arjun Shah",bio="Cloud learner looking for frontend practice.",location="Pune")]
    db.add_all(users); db.commit(); [db.refresh(u) for u in users]
    skills=[
      Skill(owner_id=users[0].id,title="React & Frontend Mentoring",type="Offering",category="Technology",description="Learn React, component design, hooks and modern frontend patterns through practical mini projects.",tags="react, javascript, frontend, vite",level="Intermediate",availability="Weekends"),
      Skill(owner_id=users[0].id,title="Python for Beginners",type="Requesting",category="Technology",description="Looking for a friendly Python mentor for automation and backend basics.",tags="python, backend, fastapi",level="Beginner",availability="Evenings"),
      Skill(owner_id=users[1].id,title="Python & FastAPI Mentoring",type="Offering",category="Technology",description="Hands-on Python, FastAPI, APIs and data analysis guidance for students.",tags="python, fastapi, backend, api, data",level="Advanced",availability="Flexible"),
      Skill(owner_id=users[1].id,title="Public Speaking Practice",type="Requesting",category="Communication",description="Want weekly practice sessions to become more confident presenting technical ideas.",tags="speaking, presentation",level="Intermediate",availability="Weekdays"),
      Skill(owner_id=users[2].id,title="Canva & Visual Design",type="Offering",category="Design",description="Design posters, social creatives and pitch decks with Canva and basic design principles.",tags="canva, design, branding, presentation",level="Intermediate",availability="Weekends"),
      Skill(owner_id=users[2].id,title="English Conversation",type="Requesting",category="Languages",description="Looking for conversation partners to improve fluency and confidence.",tags="english, communication, speaking",level="Beginner",availability="Flexible"),
      Skill(owner_id=users[3].id,title="AWS Cloud Basics",type="Offering",category="Technology",description="Learn cloud fundamentals, deployment concepts and beginner AWS workflows.",tags="aws, cloud, deployment, devops",level="Intermediate",availability="Weekends"),
      Skill(owner_id=users[3].id,title="Frontend Project Review",type="Requesting",category="Technology",description="Looking for feedback on React projects and UI architecture.",tags="react, frontend, ui, javascript",level="Beginner",availability="Evenings")]
    db.add_all(skills); db.commit(); [db.refresh(s) for s in skills]
    now=datetime.utcnow()
    # A visible demo journey: accepted + completed exchanges.
    s1=SwapRequest(requester_id=users[0].id,receiver_id=users[1].id,offered_skill_id=skills[0].id,requested_skill_id=skills[2].id,message="I can mentor React while you help me with FastAPI.",status="completed",created_at=now-timedelta(days=5))
    s2=SwapRequest(requester_id=users[3].id,receiver_id=users[0].id,offered_skill_id=skills[6].id,requested_skill_id=skills[0].id,message="I would love a React project review in exchange for AWS basics.",status="accepted",created_at=now-timedelta(days=1))
    s3=SwapRequest(requester_id=users[2].id,receiver_id=users[1].id,offered_skill_id=skills[4].id,requested_skill_id=skills[2].id,message="Can we exchange design feedback for Python help?",status="pending",created_at=now-timedelta(hours=5))
    db.add_all([s1,s2,s3]); db.commit(); [db.refresh(x) for x in [s1,s2,s3]]
    db.add_all([
      Message(sender_id=users[0].id,receiver_id=users[1].id,body="Your FastAPI skill looks like a perfect match for my Python goal.",created_at=now-timedelta(days=4)),
      Message(sender_id=users[1].id,receiver_id=users[0].id,body="Absolutely. I can teach FastAPI if you help me improve my React dashboard.",created_at=now-timedelta(days=4,minutes=-10)),
      Rating(rater_id=users[0].id,rated_id=users[1].id,swap_id=s1.id,score=5,review="Clear explanations and very practical examples."),
      Rating(rater_id=users[1].id,rated_id=users[0].id,swap_id=s1.id,score=5,review="Great React mentor and patient teacher."),
      LearningSession(organizer_id=users[0].id,participant_id=users[1].id,swap_id=s1.id,topic="React ↔ FastAPI project sprint",scheduled_at=now-timedelta(days=2),duration_minutes=90,meeting_link="https://meet.google.com/demo",status="completed"),
      LearningSession(organizer_id=users[3].id,participant_id=users[0].id,swap_id=s2.id,topic="AWS basics + React project review",scheduled_at=now+timedelta(days=1),duration_minutes=60,meeting_link="https://meet.google.com/demo",status="scheduled"),
      Notification(user_id=users[1].id,title="New swap proposal",body="Meera proposed a design ↔ Python exchange.",kind="swap",read=0),
      Notification(user_id=users[0].id,title="Learning session completed",body="Your React ↔ FastAPI session is complete. Leave a rating to build trust.",kind="session",read=0)
    ]); db.commit()
print("Demo seed complete.")
print("Ananya: ananya@demo.com / demo123")
print("Rahul:  rahul@demo.com / demo123")
print("Meera:  meera@demo.com / demo123")
print("Arjun:  arjun@demo.com / demo123")
