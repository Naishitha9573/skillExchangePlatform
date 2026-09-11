# SkillSwap AI — Final Hackathon Build

## The five priorities implemented

### 1. Reliability first
- React Error Boundary protects the whole app from one component crashing the demo.
- Swaps uses synchronous `useEffect` cleanup and explicit loading/error/success states.
- React and React DOM are pinned to 18.3.1.
- Backend swap transitions are validated: pending → accepted/rejected/cancelled → completed.
- Deterministic demo data can be recreated with `python seed.py --reset`.

### 2. Real AI
The backend supports an optional Gemini-powered semantic matching endpoint:

`POST /api/v1/ai/live-match`

Set `GEMINI_API_KEY` in `backend/.env`. The key stays server-side. Without a key, the product automatically falls back to its local semantic matcher, so the demo still works.

The AI considers:
- semantic meaning
- complementary offer/request intent
- category fit
- skill level
- practical goal

The UI labels the provider so judges can see whether the live LLM or fallback engine is active.

### 3. One unforgettable demo
Use `/judge` as the presentation control room:

**Discover → AI Match → Swap → Message → Schedule → Learn → Complete → Rate**

The page contains live database metrics and demo accounts.

### 4. Measurable impact
The dashboard and Innovation Hub calculate metrics from real database records:
- users
- skills
- swaps
- completed swaps
- completed learning hours
- ratings
- community connections

No hard-coded impact numbers are required for the demo.

### 5. Judge-ready presentation
Use the following 3–5 minute script:

1. Problem: students have knowledge but cannot easily find reciprocal learning partners.
2. Solution: SkillSwap AI converts unused knowledge into peer learning exchanges.
3. Demo: log in as Ananya, show AI match to Rahul, send/accept swap, message, schedule, complete.
4. AI: open Innovation Hub and show the explainable match score and skill-gap analysis.
5. Impact: open Judge Demo and show measurable learning hours, completed exchanges and trust signals.
6. Close: “We don't just match people. We turn knowledge into measurable peer learning.”

## Demo accounts

- `ananya@demo.com` / `demo123` — React mentor → Python learner
- `rahul@demo.com` / `demo123` — Python mentor → React learner
- `meera@demo.com` / `demo123`
- `arjun@demo.com` / `demo123`

## Setup

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python seed.py --reset
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Optional Gemini AI

Copy `backend/.env.example` to `backend/.env` and add your backend-only key:

```text
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Never put the Gemini key in `frontend/.env` or commit it to GitHub.
