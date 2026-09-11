# SkillSwap AI — Hackathon Feature Map

## Core product
- Peer-to-peer skill exchange: users offer skills and request skills.
- Search, category filters, skill levels, tags and availability.
- Skill detail pages with owner profiles and exchange proposals.
- JWT authentication and password hashing.
- Swap lifecycle: pending → accepted/rejected → completed/cancelled.
- Peer messaging with notification polling.

## AI layer
### 1. Explainable AI Matching
The matching engine scores keyword overlap, category alignment and complementary offer/request intent. Every recommendation contains a human-readable reason.

### 2. AI Skill Coach
`POST /api/v1/coach` converts a learning goal into a 4-week roadmap with:
- weekly focus areas
- concrete actions
- current-skill context
- mentor suggestions from the community
- an actionable learning tip

This works without a paid AI API, which makes the demo reliable offline.

## Trust + community
- Ratings and reviews after successful exchanges.
- Reputation metrics on the dashboard.
- Community leaderboard.
- XP and levels.
- Achievement badges.
- Activity streak indicator.
- Notification center for swaps, messages and scheduled sessions.

## Collaboration
### Learning Sessions
Users can schedule focused peer-learning sessions with:
- partner
- topic
- date/time
- duration
- optional meeting URL
- scheduled/completed/cancelled state

## Hackathon differentiation
### Skill economy without money
The platform reframes unused knowledge as a community resource. A student can exchange one capability for another instead of purchasing another course.

### Closed-loop learning
Discover → AI match → propose swap → message → schedule session → complete → rate → earn XP → become more discoverable.

### Explainability
The AI does not only say "92% match". It tells the user why the match exists, improving trust and making the AI easy to defend to judges.

## Recommended 3-minute demo
1. Landing page: explain the money-free skill economy.
2. Login with `ananya@demo.com / demo123`.
3. Dashboard: show AI matches + XP/badges.
4. AI Coach: enter `Machine Learning` and generate the roadmap.
5. Explore: open Rahul's Python offering.
6. Send a swap proposal.
7. Switch to Rahul and accept it.
8. Open Sessions and schedule a peer-learning session.
9. Send a message; show the notification badge.
10. Complete the exchange and show the leaderboard/reputation loop.

## Future-ready integrations
The architecture can later plug in:
- Gemini/OpenAI embeddings for semantic matching
- WebSockets for real-time chat
- Google Calendar integration
- email/push notifications
- vector database for semantic skill search
- PostgreSQL + Redis for production scale


## Innovation Hub — added for the next hackathon round
- **AI Match Lab:** exposes an explainable match score with semantic, keyword and category factors.
- **AI Skill Gap Radar:** compares a learner's current skills with a target and produces readiness, gaps and next steps.
- **Skill Verification Challenge:** lightweight adaptive quiz + verified badge result for Python/React/SQL foundations.
- **Community Challenges:** teaching, building and skill-chain missions with XP rewards.
- **Impact Analytics:** people connected, learning hours, sessions completed, knowledge points and average rating.
- **Judge-ready product loop:** discover → match → verify → exchange → schedule → measure impact.

### Stronger judging criteria coverage
| Criterion | Product evidence |
|---|---|
| Innovation | Explainable AI matching + skill-gap radar + verification |
| Technical complexity | React, FastAPI, JWT, SQLAlchemy, scoring pipeline, analytics |
| User impact | Peer learning, access to mentors, measurable community learning hours |
| Engagement | XP, badges, leaderboard, challenges, streaks |
| Trust | Ratings, verification challenge, profile reputation |
| Demo quality | Innovation Hub creates a single screen for the “wow” moment |

### 5-minute judge demo
1. Login and show dashboard reputation.
2. Open **Innovation** and run **AI Match Lab**.
3. Explain the score breakdown instead of saying “AI gave 92%”.
4. Show **Skill Gap Radar** and readiness.
5. Take the verification challenge and earn the verified result.
6. Show community challenges and XP.
7. Finish with the impact dashboard and the peer-learning loop.
