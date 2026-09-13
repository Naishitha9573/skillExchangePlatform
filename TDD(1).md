# Technical Design Document (TDD)
## Skill Exchange Platform (SkillSwap)

**Project Type:** Team Project / Hackathon  
**Document Version:** 1.0  
**Status:** Draft for Development

---

## 1. Technical Overview

SkillSwap is a full-stack web application that allows users to create skill profiles, discover complementary skills, connect with other users, and manage skill exchange requests.

The system follows a client-server architecture:

**Frontend → REST API → Backend Services → Database**

Optional supporting services can be added for authentication, notifications, file storage, and AI-powered matching.

---

## 2. Proposed Technology Stack

### Frontend

- React.js
- JavaScript / TypeScript where applicable
- Vite
- HTML5
- CSS3
- Responsive UI

### Backend

- Python
- FastAPI
- REST APIs
- JWT-based authentication

### Database

- PostgreSQL

### Development & Deployment

- Git
- GitHub
- Docker
- Vercel or equivalent frontend hosting
- Render/Railway/AWS or equivalent backend hosting

### Optional AI Layer

- Python
- Scikit-learn
- LLM/API integration where required

---

## 3. High-Level Architecture

```text
                    ┌──────────────────────┐
                    │      User / Web      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   React Frontend     │
                    │  UI / State / API    │
                    └──────────┬───────────┘
                               │ HTTPS / REST
                               ▼
                    ┌──────────────────────┐
                    │     FastAPI API      │
                    │ Routes / Validation  │
                    └──────────┬───────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
        ┌──────────────┐ ┌────────────┐ ┌─────────────┐
        │ Auth Service │ │ Skill/     │ │ Exchange    │
        │ JWT / Users  │ │ Match      │ │ Service     │
        └──────────────┘ └────────────┘ └─────────────┘
                │              │              │
                └──────────────┼──────────────┘
                               ▼
                    ┌──────────────────────┐
                    │     PostgreSQL       │
                    └──────────────────────┘
```

---

## 4. Frontend Architecture

A recommended structure:

```text
frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── layouts/
│   ├── services/
│   ├── hooks/
│   ├── context/
│   ├── utils/
│   ├── assets/
│   ├── App.jsx
│   └── main.jsx
├── public/
├── package.json
└── vite.config.js
```

### Main Pages

- Landing Page
- Login
- Registration
- Dashboard
- Profile
- Skills
- Discover/Search
- User Profile
- Exchange Requests
- Active Exchanges
- Exchange History
- Notifications
- Reviews

---

## 5. Backend Architecture

Recommended structure:

```text
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── models/
│   ├── schemas/
│   ├── routes/
│   ├── services/
│   ├── repositories/
│   └── utils/
├── tests/
├── requirements.txt
├── Dockerfile
└── .env.example
```

### Responsibilities

**Routes**
- Receive HTTP requests.
- Validate inputs.
- Call services.
- Return responses.

**Schemas**
- Request/response validation.
- Serialization.

**Models**
- Database entities.

**Services**
- Business logic.

**Repositories**
- Database operations.

**Core**
- Configuration.
- Database connection.
- Security/authentication.

---

## 6. Authentication Design

JWT authentication is recommended.

### Registration Flow

```text
Client
  ↓
POST /auth/register
  ↓
Validate input
  ↓
Check existing user
  ↓
Hash password
  ↓
Store user
  ↓
Return success
```

### Login Flow

```text
Client
  ↓
POST /auth/login
  ↓
Validate credentials
  ↓
Verify password hash
  ↓
Generate JWT
  ↓
Return token
```

### Protected Request

```text
Frontend
  ↓
Authorization: Bearer <JWT>
  ↓
FastAPI Authentication Dependency
  ↓
Validate token
  ↓
Identify current user
  ↓
Execute protected operation
```

Passwords must be hashed using a secure password-hashing library. Plain-text passwords must never be stored.

---

## 7. Database Design

### Users

```text
users
-----
id              PK
name
email           UNIQUE
password_hash
bio
experience_level
profile_image
created_at
updated_at
```

### Skills

```text
skills
------
id              PK
name            UNIQUE
category
description
created_at
```

### User Skills

```text
user_skills
-----------
id              PK
user_id         FK -> users.id
skill_id        FK -> skills.id
type            OFFERED / WANTED
level
created_at
```

### Exchange Requests

```text
exchange_requests
-----------------
id              PK
requester_id    FK -> users.id
recipient_id    FK -> users.id
offered_skill_id FK -> skills.id
wanted_skill_id  FK -> skills.id
message
status
created_at
updated_at
```

### Exchanges

```text
exchanges
---------
id              PK
request_id      FK -> exchange_requests.id
status
started_at
completed_at
created_at
updated_at
```

### Reviews

```text
reviews
-------
id              PK
exchange_id     FK -> exchanges.id
reviewer_id     FK -> users.id
reviewee_id     FK -> users.id
rating
comment
created_at
```

### Notifications

```text
notifications
-------------
id              PK
user_id         FK -> users.id
type
title
message
is_read
created_at
```

---

## 8. Entity Relationships

```text
User
 │
 ├──< UserSkill >── Skill
 │
 ├──< ExchangeRequest
 │                  │
 │                  └── Exchange
 │                         │
 │                         └──< Review
 │
 └──< Notification
```

A user can have multiple offered/wanted skills.

A skill can belong to many users.

An exchange request connects two users.

A completed exchange can produce reviews.

---

## 9. Skill Matching Logic

### Basic Matching

A simple initial matching algorithm can compare:

```text
User A wants: Python
User A offers: React

User B wants: React
User B offers: Python
```

This creates a strong reciprocal match.

### Matching Score

A basic score can be calculated using:

```text
Match Score =
    Offered Skill Compatibility
  + Wanted Skill Compatibility
  + Experience Compatibility
  + Optional Profile/Interest Similarity
```

The initial implementation should prioritize transparent rule-based matching.

AI/ML matching can be introduced later without changing the core exchange workflow.

---

## 10. REST API Design

### Authentication

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

### Users

```text
GET    /api/users
GET    /api/users/{user_id}
PUT    /api/users/me
DELETE /api/users/me
```

### Skills

```text
GET  /api/skills
POST /api/skills
GET  /api/skills/{skill_id}
```

### User Skills

```text
GET    /api/users/me/skills
POST   /api/users/me/skills
DELETE /api/users/me/skills/{skill_id}
```

### Discovery / Matching

```text
GET /api/discover
GET /api/matches
```

### Exchange Requests

```text
POST   /api/exchange-requests
GET    /api/exchange-requests
GET    /api/exchange-requests/{id}
PATCH  /api/exchange-requests/{id}/accept
PATCH  /api/exchange-requests/{id}/reject
```

### Exchanges

```text
GET   /api/exchanges
GET   /api/exchanges/{id}
PATCH /api/exchanges/{id}/start
PATCH /api/exchanges/{id}/complete
PATCH /api/exchanges/{id}/cancel
```

### Reviews

```text
POST /api/exchanges/{id}/reviews
GET  /api/users/{id}/reviews
```

### Notifications

```text
GET   /api/notifications
PATCH /api/notifications/{id}/read
```

---

## 11. Example Exchange Request

### Request

```json
{
  "recipient_id": 25,
  "offered_skill_id": 4,
  "wanted_skill_id": 9,
  "message": "I can help you with React in exchange for Python guidance."
}
```

### Response

```json
{
  "id": 101,
  "status": "pending",
  "message": "I can help you with React in exchange for Python guidance."
}
```

---

## 12. API Error Handling

Use consistent HTTP status codes.

| Status | Meaning |
|---|---|
| 200 | Successful request |
| 201 | Resource created |
| 400 | Invalid request |
| 401 | Authentication required/invalid |
| 403 | Permission denied |
| 404 | Resource not found |
| 409 | Conflict |
| 422 | Validation error |
| 500 | Internal server error |

Responses should provide useful error messages without exposing sensitive implementation details.

---

## 13. Security Design

### Required Controls

- Password hashing
- JWT authentication
- Authorization checks
- Input validation
- SQL injection protection through ORM/parameterized queries
- CORS configuration
- Environment-based secrets
- HTTPS in production
- Secure error handling

### Environment Variables

Example:

```env
DATABASE_URL=
SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=
CORS_ORIGINS=
```

Do not commit `.env` containing real secrets to GitHub.

Provide:

```text
.env.example
```

instead.

---

## 14. Database Migration Strategy

Database schema changes should use a migration system such as Alembic.

Recommended workflow:

```text
Modify Model
    ↓
Create Migration
    ↓
Review Migration
    ↓
Apply Migration
    ↓
Test Application
```

Production database changes should never depend on manually modifying tables.

---

## 15. Frontend–Backend Integration

The frontend should communicate with the backend through a centralized API layer.

Example:

```text
src/services/api.js
```

The API layer should manage:
- Base URL
- Authentication token
- HTTP requests
- Error handling
- Common headers

Do not scatter backend URLs throughout UI components.

---

## 16. State Management

Application state can be divided into:

### Authentication State

- Current user
- Login status
- Access token

### Profile State

- User profile
- Skills
- Preferences

### Exchange State

- Pending requests
- Active exchanges
- Completed exchanges

### Notification State

- Notifications
- Unread count

Use React Context or an appropriate state-management solution depending on project complexity.

---

## 17. Validation

Validation should occur at multiple levels:

```text
Frontend validation
        ↓
Backend schema validation
        ↓
Business-rule validation
        ↓
Database constraints
```

Frontend validation improves user experience, but backend validation is mandatory for security and correctness.

---

## 18. Testing Strategy

### Unit Testing

Test:
- Matching logic
- Authentication utilities
- Service functions
- Validation functions

### API Testing

Test:
- Registration
- Login
- Protected endpoints
- Skill creation
- Exchange requests
- Accept/reject operations
- Reviews

### Integration Testing

Test complete flows:

```text
Register
 → Login
 → Create Profile
 → Add Skills
 → Discover User
 → Send Request
 → Accept Request
 → Complete Exchange
 → Review
```

### Frontend Testing

Test:
- Forms
- Navigation
- Protected pages
- API error states
- Responsive layouts

---

## 19. Deployment Architecture

```text
                 Internet
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
   Frontend Hosting      Backend Hosting
       React                FastAPI
          │                   │
          └─────────┬─────────┘
                    ▼
               PostgreSQL
```

Docker can package the backend consistently.

Example:

```text
Dockerfile
requirements.txt
app/
```

Production configuration should use environment variables rather than hard-coded credentials.

---

## 20. Git Workflow

Recommended team workflow:

```text
main
 │
 ├── feature/auth
 ├── feature/profile
 ├── feature/skills
 ├── feature/matching
 ├── feature/exchange
 └── feature/frontend-ui
```

Process:

```text
Pull latest main
    ↓
Create feature branch
    ↓
Implement feature
    ↓
Test locally
    ↓
Commit
    ↓
Push branch
    ↓
Create Pull Request
    ↓
Review
    ↓
Merge into main
```

Avoid directly pushing unfinished work to `main`.

---

## 21. Team Module Ownership

Suggested division:

| Module | Responsibility |
|---|---|
| Authentication | Register, login, JWT |
| User/Profile | Profile management |
| Skills | Skill CRUD and categorization |
| Matching | Discovery and recommendation logic |
| Exchange | Requests and exchange lifecycle |
| Reviews | Ratings and feedback |
| Frontend | UI and page integration |
| Database | Schema and migrations |
| DevOps | Docker and deployment |
| Testing | Unit/integration/API testing |
| Documentation | BRD, TDD, README, demo material |

One person may own multiple modules depending on team size.

---

## 22. Logging and Monitoring

Backend should log:
- Application startup
- Authentication failures where appropriate
- API errors
- Important exchange operations
- Database failures

Production logs should never expose:
- Passwords
- JWT secrets
- Database passwords
- API keys

---

## 23. Performance Considerations

Initial optimization priorities:

1. Database indexes on frequently queried fields.
2. Pagination for large user/skill lists.
3. Efficient skill matching queries.
4. Avoid unnecessary frontend API calls.
5. Cache static resources where appropriate.
6. Keep API response payloads focused.

Recommended indexes include:
- `users.email`
- `skills.name`
- `user_skills.user_id`
- `user_skills.skill_id`
- `exchange_requests.recipient_id`
- `exchange_requests.requester_id`
- `exchange_requests.status`

---

## 24. Hackathon Demo Flow

The strongest demonstration should show one complete user journey:

```text
Landing Page
     ↓
Register/Login
     ↓
Complete Profile
     ↓
Add "React" as Offered Skill
     ↓
Add "Python" as Wanted Skill
     ↓
Discover Compatible User
     ↓
View Profile
     ↓
Send Skill Exchange Request
     ↓
Other User Accepts
     ↓
Exchange Becomes Active
     ↓
Mark Exchange Completed
     ↓
Submit Rating/Review
     ↓
Dashboard Shows Updated History
```

This demonstrates the platform's complete business value rather than isolated screens.

---

## 25. Future Technical Enhancements

### AI Matching

Introduce semantic embeddings to understand related skills.

Example:

```text
"Machine Learning"
≈
"ML"
≈
"Predictive Modeling"
```

### Recommendation Engine

Recommend:
- People
- Skills
- Learning paths
- Potential exchanges

### Real-Time Communication

Possible technologies:
- WebSockets
- WebRTC
- External communication services

### Skill Verification

Potential verification methods:
- Certificates
- Portfolio links
- Peer endorsements
- Completed exchanges
- Assessment tests

---

## 26. Technical Acceptance Criteria

The system is technically acceptable when:

- Frontend builds successfully.
- Backend starts without errors.
- Database connection works.
- Registration and login work.
- JWT-protected endpoints work.
- CRUD operations persist correctly.
- Unauthorized users cannot access protected resources.
- Exchange workflow works end-to-end.
- Validation and error handling work.
- Tests for critical business logic pass.
- Production environment variables are configured.
- Docker build/run works where Docker deployment is used.
- The deployed application can complete the primary demo flow.

---

## 27. Conclusion

The SkillSwap technical architecture is designed to be modular, secure, maintainable, and suitable for rapid hackathon development.

The initial priority is a reliable end-to-end platform using React, FastAPI, PostgreSQL, JWT authentication, and REST APIs. The architecture leaves room for AI-powered matching, real-time communication, skill verification, and advanced recommendations in future versions.
