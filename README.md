# SkillSwap AI — Hackathon Edition

SkillSwap AI is a full-stack peer-to-peer skill exchange platform. Users publish skills they can teach or want to learn, discover opportunities, receive explainable AI match scores, propose skill-for-skill swaps, message other members, and build a trusted exchange history.

## Why it is hackathon-ready
- AI-assisted complementary skill matching without requiring a paid AI API.
- Real authentication with JWT + hashed passwords.
- Search and category/type filters.
- Skill CRUD and profile management.
- Swap lifecycle: pending → accepted/rejected → completed/cancelled.
- Messaging between users.
- Ratings and reputation loop.
- XP, levels, achievement badges and community leaderboard.
- AI Skill Coach with a personalized 4-week roadmap.
- Learning-session scheduling with optional meeting links.
- Notification center for swaps, messages and sessions.
- Dashboard with live activity metrics and progress.
- Innovation Hub with AI Match Lab, AI Skill Gap Radar, skill verification, challenges and impact analytics.
- Responsive, presentation-ready React UI.
- SQLite by default for zero-setup demos; PostgreSQL-compatible via DATABASE_URL.

## Demo accounts after seeding
- ananya@demo.com / demo123
- rahul@demo.com / demo123
- meera@demo.com / demo123

## Run backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # Windows
# cp .env.example .env # macOS/Linux
python seed.py
python run.py
```
API docs: http://localhost:8000/docs

## Run frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

## Hackathon demo flow
1. Login as Ananya.
2. Open Dashboard and show AI recommendations.
3. Open **Innovation** for the judge-facing AI Match Lab and Skill Gap Radar.
3. Explore skills and open Rahul's Python skill.
4. Propose a swap using Ananya's React offering.
5. Login as Rahul in another browser/incognito window.
6. Open Swaps and accept the request.
7. Send a message.
8. Mark the swap completed.
9. Explain the matching score: shared category/keywords + complementary offer/request relationship.

## Feature details
See `HACKATHON_FEATURES.md` for the full feature map, API additions and recommended demo flow.

## Suggested pitch
"SkillSwap AI converts unused knowledge into a learning network. Instead of paying for every course, a student can trade one hour of what they know for one hour of what they need. Our explainable matching engine identifies complementary opportunities, while profiles, messaging, swap states and ratings create a trustworthy exchange loop."
