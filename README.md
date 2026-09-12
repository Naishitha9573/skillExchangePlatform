# 🚀 Skill Exchange Platform

A full-stack web application that helps users **learn, teach, share, and exchange skills** with other users. The platform connects learners with people who have the skills they want to learn, creating opportunities for peer-to-peer learning and collaboration.

---

## 📌 Project Overview

The **Skill Exchange Platform** is designed to solve the problem of finding suitable people for learning and sharing skills.

Users can:

- Create an account
- Build their profile
- Add skills they can teach
- Specify skills they want to learn
- Discover other users
- Find suitable skill partners
- Connect with other users
- Exchange knowledge and skills

### 💡 Example

**User A**

**Can Teach:**
- Python
- Java
- Machine Learning

**Wants to Learn:**
- React
- UI/UX

**User B**

**Can Teach:**
- React
- UI/UX

**Wants to Learn:**
- Python
- Java
- Machine Learning

This creates a **mutual skill exchange**.

---

## 🎯 Objectives

The main objectives of the project are:

- Create a platform for peer-to-peer learning.
- Allow users to showcase their skills.
- Help users find suitable learning partners.
- Support skill exchange between users.
- Provide secure user authentication.
- Provide APIs for frontend-backend communication.
- Store user and skill information efficiently.
- Provide a simple and user-friendly interface.
- Build a platform that can be extended with AI-based matching in the future.

---

## ✨ Key Features

### 👤 User Registration

Users can create an account and join the platform.

### 🔐 User Login & Authentication

Users can securely log in and access authenticated features.

### 🧑‍💻 User Profile

Users can create and manage their profiles.

Profile information can include:

- Name
- Bio
- Skills
- Learning interests
- Experience
- Other relevant information

### 🛠️ Skill Management

Users can manage two types of skills.

#### Skills I Can Teach

Skills that the user knows and can teach to others.

#### Skills I Want to Learn

Skills that the user wants to learn from other users.

### 🔎 Skill Discovery

Users can discover other users based on their teaching and learning skills.

### 🤝 Skill Matching

The platform can identify potential matches between users with complementary skill requirements.

### 🌐 Full-Stack Application

The project includes:

- Frontend
- Backend
- Database
- Authentication
- REST APIs

---

## 🔄 Application Workflow

```text
                         USER
                           │
                           ▼
                   Register / Login
                           │
                           ▼
                    Create Profile
                           │
                           ▼
                  Add Teaching Skills
                           │
                           ▼
                  Add Learning Skills
                           │
                           ▼
                   Discover Users
                           │
                           ▼
                    Find Skill Match
                           │
                           ▼
                    Connect / Learn
                           │
                           ▼
                     Skill Exchange
```

---

## 🏗️ System Architecture

```text
┌──────────────────────────────────────────┐
│                  USER                    │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│                FRONTEND                  │
│                                          │
│               React.js                   │
│        JavaScript / HTML / CSS           │
│                  Vite                    │
└────────────────────┬─────────────────────┘
                     │
                     │ REST API
                     ▼
┌──────────────────────────────────────────┐
│                BACKEND                   │
│                                          │
│                FastAPI                   │
│                 Python                   │
│               SQLAlchemy                 │
│            JWT Authentication            │
└────────────────────┬─────────────────────┘
                     │
                     │ Database Operations
                     ▼
┌──────────────────────────────────────────┐
│                DATABASE                  │
│                                          │
│             User Information             │
│             Skill Information            │
│          Authentication Data             │
│              Other Data                  │
└──────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Frontend

- React.js
- JavaScript
- HTML5
- CSS3
- Vite
- React Icons

### Backend

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- JWT Authentication
- REST APIs

### Database

- SQL Database
- SQLAlchemy ORM

### Development Tools

## Database Notes

The backend keeps the existing `/api/v1/skills` response contract while storing reusable skill names in `skill_catalog` and user-specific offers or learning goals in `skills`. Profiles and ordered user conversations are separate relational entities, and swap, session, rating, and notification records use foreign keys, status checks, indexes, and timestamps.

On startup, `backend/app/db.py` creates new tables and performs an idempotent additive upgrade for the original SQLite database. Existing skill rows, profile fields, and direct messages are preserved and backfilled into the catalog, profiles, and conversations tables. For production, run this upgrade during deployment and take a database backup first; the current compatibility columns on `users` and `skills` should be retained until all clients have moved to the normalized relationships.

- Git
- GitHub
- Visual Studio Code
- npm
- Python Virtual Environment

---

## 📁 Project Structure

```text
SkillSwap-Hackathon/
│
├── app/
│   ├── main.py
│   ├── models/
│   ├── routes/
│   ├── schemas/
│   ├── services/
│   └── ...
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── scripts/
│   └── ...
│
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
```

> The exact folders and files may change as development continues.

---

## 💻 Requirements

Before running the project, install:

- Python 3.10+
- Node.js
- npm
- Git
- Visual Studio Code

### Check Python

```bash
python --version
```

### Check Node.js

```bash
node --version
```

### Check npm

```bash
npm --version
```

### Check Git

```bash
git --version
```

---

## 📥 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/Naishitha9573/skillExchangePlatform.git
```

### Step 2: Enter the Project Directory

```bash
cd skillExchangePlatform
```

---

# 🐍 Backend Setup

### Step 1: Create Virtual Environment

```bash
python -m venv venv
```

### Step 2: Activate Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

After activation, the terminal should show:

```text
(venv)
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Variables

The application may require environment variables for:

- Database configuration
- Authentication
- Secret keys
- Other services

Create a `.env` file according to `.env.example`.

Example:

```env
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
```

If additional variables are required, add them according to the project's `.env.example`.

### ⚠️ Important

Never upload `.env` to GitHub.

Never commit:

- Passwords
- API keys
- Secret keys
- Database credentials
- Private tokens
- Access tokens

---

# ▶️ Running the Backend

From the project root:

```bash
python -m uvicorn app.main:app --reload
```

Alternatively:

```bash
uvicorn app.main:app --reload
```

The backend normally runs at:

```text
http://127.0.0.1:8000
```

---

# 📚 API Documentation

FastAPI provides automatic API documentation.

### Swagger UI

```text
http://127.0.0.1:8000/docs
```

### ReDoc

```text
http://127.0.0.1:8000/redoc
```

Swagger UI can be used to view and test the backend APIs.

---

# ⚛️ Frontend Setup

Open a **new terminal**.

Move into the frontend directory:

```bash
cd frontend
```

Install frontend dependencies:

```bash
npm install
```

Start the frontend:

```bash
npm run dev
```

Vite will display the local application URL.

Usually:

```text
http://localhost:5173
```

---

# 🚀 Run the Complete Application

The frontend and backend should normally run in separate terminals.

### Terminal 1 — Backend

```bash
cd skillExchangePlatform
venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

API Documentation:

```text
http://127.0.0.1:8000/docs
```

### Terminal 2 — Frontend

```bash
cd skillExchangePlatform/frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# 🔗 Frontend–Backend Communication

The frontend communicates with the FastAPI backend using REST APIs.

```text
React Frontend
      │
      │ HTTP Request
      ▼
FastAPI Backend
      │
      │ Database Query
      ▼
Database
      │
      │ Response
      ▼
FastAPI Backend
      │
      │ JSON Response
      ▼
React Frontend
```

---

# 🔐 Authentication Flow

The authentication process follows this general flow:

```text
User
  │
  ▼
Register / Login
  │
  ▼
FastAPI Backend
  │
  ▼
Validate Credentials
  │
  ▼
Generate Authentication Token
  │
  ▼
Authenticated User
  │
  ▼
Access Protected APIs
```

Authentication-related secrets must never be committed to GitHub.

---

# 🧩 Main Modules

## 1. User Management

Responsible for:

- Registration
- Login
- User information
- Profile management

## 2. Skill Management

Responsible for:

- Adding skills
- Updating skills
- Removing skills
- Teaching skills
- Learning skills

## 3. Skill Discovery

Responsible for helping users find people based on their skills and interests.

## 4. Skill Matching

Responsible for identifying users with complementary skill requirements.

## 5. Authentication

Responsible for:

- User authentication
- Authorization
- Protected endpoints
- Token management

## 6. Database

Responsible for storing:

- User information
- Skill information
- Authentication-related information
- Platform data

---

# 🧪 Testing Checklist

Before pushing changes to GitHub, verify:

- [ ] Backend starts successfully
- [ ] Frontend starts successfully
- [ ] Registration works
- [ ] Login works
- [ ] Profile works
- [ ] Skills can be added
- [ ] Skills can be updated
- [ ] Skills can be removed
- [ ] Skill discovery works
- [ ] Matching works
- [ ] APIs respond correctly
- [ ] Database operations work
- [ ] No console errors
- [ ] No sensitive information is committed

---

# 🌿 Git & GitHub Workflow

All team members should follow the same Git workflow.

## 1. Get the Latest Code

Before starting work:

```bash
git checkout main
git pull origin main
```

## 2. Create a Feature Branch

Do not directly develop new features on `main`.

Example:

```bash
git checkout -b feature/login
```

Other examples:

```bash
git checkout -b feature/profile
```

```bash
git checkout -b feature/skill-matching
```

```bash
git checkout -b feature/frontend-ui
```

```bash
git checkout -b feature/backend-api
```

---

# 💾 Commit Changes

Check your changes:

```bash
git status
```

Add your files:

```bash
git add .
```

Commit:

```bash
git commit -m "Add user profile functionality"
```

### Recommended Commit Messages

```text
Add user authentication
Fix login API
Add user profile
Update profile UI
Add skill management
Add skill matching
Fix database connection
Update API validation
Improve frontend UI
Update documentation
```

---

# 📤 Push Your Feature Branch

Example:

```bash
git push origin feature/login
```

Replace `feature/login` with your actual branch name.

---

# 🔀 Pull Request Workflow

After completing your feature:

1. Push your feature branch.
2. Open the GitHub repository.
3. Create a Pull Request.
4. Explain what was changed.
5. Ask a teammate to review the changes.
6. Fix review comments if required.
7. Test again.
8. Merge into `main` after approval.

---

# ⚠️ Git Rules for Team Members

## ✅ DO

- Pull the latest code before starting work.
- Create a separate feature branch.
- Commit frequently.
- Use meaningful commit messages.
- Test changes locally.
- Review changes before pushing.
- Communicate before modifying shared components.
- Create Pull Requests for major features.

## ❌ DON'T

- Do not force-push to `main`.
- Do not delete another teammate's work.
- Do not commit `.env`.
- Do not commit passwords.
- Do not commit API keys.
- Do not commit `node_modules`.
- Do not commit `venv`.
- Do not overwrite another teammate's changes.
- Do not make major database changes without informing the team.

---

# 🚫 Files That Should Not Be Uploaded

The `.gitignore` file should normally contain:

```text
.env
venv/
.venv/
node_modules/
__pycache__/
*.pyc
*.log
dist/
build/
```

Large datasets, trained models, and other large files should be handled according to the team's repository and deployment strategy.

---

# 👥 Team Development Guidelines

The project is developed collaboratively.

### Recommended Responsibilities

| Area | Responsibilities |
|---|---|
| Frontend | React pages, components, UI and frontend logic |
| Backend | FastAPI APIs and business logic |
| Database | Models, schema and database operations |
| Authentication | Registration, login and authorization |
| Skills | Skill creation and management |
| Matching | Skill matching and recommendation logic |
| Testing | API and application testing |
| Deployment | Deployment and configuration |
| Documentation | README and technical documentation |

Team members should communicate before changing shared architecture or core components.

---

# 📋 New Team Member Setup

A new team member should follow these steps:

### 1. Clone Repository

```bash
git clone https://github.com/Naishitha9573/skillExchangePlatform.git
```

### 2. Enter Project

```bash
cd skillExchangePlatform
```

### 3. Create Virtual Environment

```bash
python -m venv venv
```

### 4. Activate Virtual Environment

```bash
venv\Scripts\activate
```

### 5. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure Environment Variables

Create `.env` using `.env.example`.

### 7. Start Backend

```bash
python -m uvicorn app.main:app --reload
```

### 8. Open Another Terminal

```bash
cd frontend
```

### 9. Install Frontend Dependencies

```bash
npm install
```

### 10. Start Frontend

```bash
npm run dev
```

### 11. Open the Application

Use the URL shown by Vite, normally:

```text
http://localhost:5173
```

---

# 🔮 Future Enhancements

The platform can be extended with:

- 🤖 AI-powered skill matching
- 💬 Real-time chat
- 📅 Skill exchange scheduling
- ⭐ User ratings and reviews
- 🔔 Notifications
- 🏆 User achievement system
- 📊 User activity dashboard
- 🎯 Personalized skill recommendations
- 📱 Mobile application
- 🔎 Advanced search and filtering
- 👥 Group learning
- 📹 Video learning sessions
- 🧠 Intelligent recommendation system
- 📈 Learning progress tracking

---

# 🔒 Security Guidelines

Security is important for the project.

Never commit:

```text
Passwords
API Keys
Secret Keys
Database Credentials
Access Tokens
Private Configuration
.env
```

Always use environment variables for sensitive configuration.

If a secret is accidentally pushed to GitHub, immediately revoke or rotate the secret.

---

# 📊 Project Status

🚧 **Status: Active Development**

The Skill Exchange Platform is currently under active development.

Features, UI components, APIs, database structures, and matching functionality may continue to evolve.

---

# 🌐 GitHub Repository

## Skill Exchange Platform

Repository:

https://github.com/Naishitha9573/skillExchangePlatform

---

# 🤝 Contributing

Team members can contribute using the following process:

```text
Clone Repository
      ↓
Pull Latest Changes
      ↓
Create Feature Branch
      ↓
Develop Feature
      ↓
Test Locally
      ↓
Commit Changes
      ↓
Push Feature Branch
      ↓
Create Pull Request
      ↓
Code Review
      ↓
Merge into Main
```

---

# ⭐ Quick Commands

### Clone

```bash
git clone https://github.com/Naishitha9573/skillExchangePlatform.git
```

### Update

```bash
git pull origin main
```

### Create Branch

```bash
git checkout -b feature/your-feature
```

### Check Status

```bash
git status
```

### Add Changes

```bash
git add .
```

### Commit

```bash
git commit -m "Describe your changes"
```

### Push

```bash
git push origin feature/your-feature
```

---

# 🚀 Quick Start

## Backend

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

## Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

---

# 🔗 Local URLs

### Frontend

```text
http://localhost:5173
```

### Backend

```text
http://127.0.0.1:8000
```

### API Documentation

```text
http://127.0.0.1:8000/docs
```

---

# 📄 License

This project is developed as an educational and hackathon project by the project team.

---

# 💡 Project Vision

The vision of the **Skill Exchange Platform** is to create a collaborative learning ecosystem where people can:

**Learn from others → Share their knowledge → Build connections → Exchange skills → Grow together**

---

# 🌟 Skill Exchange Platform

## Learn. Share. Connect. Grow. 🚀
