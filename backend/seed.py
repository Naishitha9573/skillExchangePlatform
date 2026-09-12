"""Create the opt-in SkillSwap demo dataset.

Run explicitly from backend/: ``python seed.py --reset``.
This script is never imported by application startup.
"""
import argparse
from datetime import datetime, timedelta

from app.auth import hash_password
from app.db import SessionLocal, initialize_database
from app.models import Conversation, LearningSession, Message, Notification, Profile, Rating, Skill, SkillCatalog, SwapRequest, User

parser = argparse.ArgumentParser(description="Seed SkillSwap demo data")
parser.add_argument("--reset", action="store_true", help="replace existing database rows")
args = parser.parse_args()
initialize_database()
db = SessionLocal()

try:
    if args.reset:
        for model in [Rating, Message, Notification, LearningSession, Conversation, SwapRequest, Skill, SkillCatalog, Profile, User]:
            db.query(model).delete()
        db.commit()
    if db.query(User).count():
        print("Demo data already exists. Use --reset to recreate it.")
        raise SystemExit(0)

    people = [
        ("Ananya Rao", "ananya@demo.com", "Bengaluru", "Frontend developer helping people turn ideas into calm, clear interfaces.", "React", "Python"),
        ("Rahul Verma", "rahul@demo.com", "Hyderabad", "Backend engineer who teaches practical APIs and thoughtful data workflows.", "Python", "React"),
        ("Meera Nair", "meera@demo.com", "Kochi", "Visual designer focused on accessible systems, storytelling, and useful feedback.", "Figma", "English Communication"),
        ("Arjun Shah", "arjun@demo.com", "Pune", "Cloud learner building reliable foundations one project at a time.", "AWS Cloud", "UI/UX Design"),
        ("Zoya Khan", "zoya@demo.com", "Mumbai", "Product designer who enjoys making complex workflows feel welcoming.", "UI/UX Design", "SQL & Excel"),
        ("Kabir Menon", "kabir@demo.com", "Chennai", "Data analyst turning messy spreadsheets into decisions teams can act on.", "SQL & Excel", "Public Speaking"),
        ("Ishita Sen", "ishita@demo.com", "Kolkata", "Machine learning practitioner who loves explaining the intuition behind models.", "Machine Learning", "Photography"),
        ("Dev Patel", "dev@demo.com", "Ahmedabad", "Java developer and patient pair-programming partner for early-career builders.", "Java", "FastAPI"),
        ("Tara Iyer", "tara@demo.com", "Bengaluru", "Photographer documenting everyday places and teaching visual composition.", "Photography", "Digital Marketing"),
        ("Nikhil Bansal", "nikhil@demo.com", "Delhi", "Video editor helping creators find rhythm, clarity, and a confident voice.", "Video Editing", "Graphic Design"),
        ("Sana Ali", "sana@demo.com", "Jaipur", "Brand strategist blending research, writing, and practical growth experiments.", "Digital Marketing", "Node.js"),
        ("Rohan Das", "rohan@demo.com", "Bhubaneswar", "Competitive programmer who makes problem solving feel less intimidating.", "C++", "English Communication"),
        ("Aditi Kulkarni", "aditi@demo.com", "Nagpur", "Security learner sharing safe, responsible ways to build and ship software.", "Cybersecurity", "Python"),
        ("Vikram Joshi", "vikram@demo.com", "Mysuru", "Full-stack builder and open-source contributor who likes useful tooling.", "Node.js", "Competitive Programming"),
        ("Lina Thomas", "lina@demo.com", "Thiruvananthapuram", "Communication coach helping technical people present ideas with confidence.", "Public Speaking", "Data Science"),
        ("Omar Sheikh", "omar@demo.com", "Lucknow", "Data scientist exploring responsible insights from real-world datasets.", "Data Science", "Figma"),
        ("Pooja Desai", "pooja@demo.com", "Surat", "Graphic designer creating expressive visuals for small teams and communities.", "Graphic Design", "Java"),
        ("Yash Malhotra", "yash@demo.com", "Chandigarh", "Git and delivery nerd helping teams collaborate without losing momentum.", "Git & GitHub", "Machine Learning"),
        ("Nora Fernandes", "nora@demo.com", "Goa", "English communication partner and curious learner who brings warmth to practice.", "English Communication", "Video Editing"),
        ("Siddharth Bose", "siddharth@demo.com", "Guwahati", "FastAPI builder interested in clean contracts, testing, and dependable services.", "FastAPI", "AWS Cloud"),
    ]
    category = {
        "React": "Technology", "Python": "Technology", "Figma": "Design", "English Communication": "Communication",
        "AWS Cloud": "Technology", "UI/UX Design": "Design", "SQL & Excel": "Business", "Public Speaking": "Communication",
        "Machine Learning": "Technology", "Photography": "Creative", "Java": "Technology", "FastAPI": "Technology",
        "Video Editing": "Creative", "Digital Marketing": "Business", "Graphic Design": "Design", "C++": "Technology",
        "Cybersecurity": "Technology", "Node.js": "Technology", "Competitive Programming": "Technology", "Data Science": "Technology",
        "Git & GitHub": "Technology",
    }
    users = [User(email=email, password_hash=hash_password("demo123"), full_name=name, bio=bio, location=location,
                  profile=Profile(bio=bio, location=location))
             for name, email, location, bio, _, _ in people]
    db.add_all(users)
    db.commit()
    for user in users:
        db.refresh(user)

    skills = []
    levels = ["Intermediate", "Advanced", "Intermediate", "Beginner"]
    for index, (user, person) in enumerate(zip(users, people)):
        offering, requesting = person[-2:]
        skills.extend([
            Skill(owner_id=user.id, title=offering, type="Offering", category=category[offering],
                  description=f"A practical, friendly exchange around {offering.lower()}, with examples shaped to your goals.",
                  tags=offering.lower().replace(" & ", ", ").replace(" ", ","), level=levels[index % 4], availability="Weekend mornings"),
            Skill(owner_id=user.id, title=requesting, type="Requesting", category=category[requesting],
                  description=f"Looking for a peer who can help me build confidence in {requesting.lower()} through a focused project.",
                  tags=requesting.lower().replace(" & ", ", ").replace(" ", ","), level="Beginner", availability="Flexible"),
        ])
    catalogs = {}
    for skill in skills:
        key = (skill.title, skill.category)
        if key not in catalogs:
            catalogs[key] = SkillCatalog(name=skill.title, category=skill.category)
            db.add(catalogs[key])
        skill.catalog = catalogs[key]
    db.add_all(skills)
    db.commit()
    for skill in skills:
        db.refresh(skill)

    offers, goals = skills[::2], skills[1::2]
    now = datetime.utcnow()
    swaps = []
    for index in range(10):
        requester, receiver = users[index], users[(index + 1) % len(users)]
        status = ["completed", "completed", "accepted", "pending", "completed"][index % 5]
        requested = goals[(index + 1) % len(goals)]
        swaps.append(SwapRequest(requester_id=requester.id, receiver_id=receiver.id, offered_skill_id=offers[index].id,
                     requested_skill_id=requested.id,
                     message=f"I can share {offers[index].title} in exchange for your {requested.title} perspective.",
                                 status=status, created_at=now - timedelta(days=10 - index)))
    db.add_all(swaps)
    db.commit()
    for swap in swaps:
        db.refresh(swap)

    completed = [swap for swap in swaps if swap.status == "completed"]
    accepted = [swap for swap in swaps if swap.status in {"accepted", "completed"}]
    for swap in accepted:
        one, two = sorted((swap.requester_id, swap.receiver_id))
        conversation = Conversation(participant_one_id=one, participant_two_id=two)
        db.add(conversation)
        db.flush()
        db.add_all([
            Message(conversation_id=conversation.id, sender_id=swap.requester_id, receiver_id=swap.receiver_id,
                    body=f"Your {swap.requested_skill.title} goal looks like a great match. Shall we find a time?",
                    created_at=swap.created_at + timedelta(hours=2)),
            Message(conversation_id=conversation.id, sender_id=swap.receiver_id, receiver_id=swap.requester_id,
                    body="Absolutely. I am excited to learn together.", created_at=swap.created_at + timedelta(hours=3)),
        ])
    for swap in completed:
        db.add_all([
            Rating(rater_id=swap.requester_id, rated_id=swap.receiver_id, swap_id=swap.id, score=5,
                   review="Clear, generous, and practical. I left with something I could use immediately."),
            Rating(rater_id=swap.receiver_id, rated_id=swap.requester_id, swap_id=swap.id, score=4,
                   review="A thoughtful exchange with great questions and follow-through."),
            LearningSession(organizer_id=swap.requester_id, participant_id=swap.receiver_id, swap_id=swap.id,
                            topic=f"{swap.offered_skill.title} exchange", scheduled_at=now - timedelta(days=6),
                            duration_minutes=60, meeting_link="", status="completed"),
        ])
    for swap in accepted[:3]:
        db.add(LearningSession(organizer_id=swap.receiver_id, participant_id=swap.requester_id, swap_id=swap.id,
                               topic=f"Next steps: {swap.requested_skill.title}", scheduled_at=now + timedelta(days=1 + swap.id),
                               duration_minutes=60, meeting_link="", status="scheduled"))
    for index, user in enumerate(users):
        db.add(Notification(user_id=user.id, title="Your next exchange is close", kind="match", read=index % 3 == 0,
                            body="We found a complementary skill in the community. Explore your recommendations."))
    db.add(Notification(user_id=users[0].id, title="Session complete", kind="session", read=False,
                        body="Your exchange is complete. Leave a review to help your partner build trust."))
    db.commit()
    print("Demo seed complete: 20 users, 40 skills, exchanges, conversations, sessions, ratings, and notifications.")
    print("Learner: ananya@demo.com / demo123")
    print("Mentor:  rahul@demo.com / demo123")
finally:
    db.close()
