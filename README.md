# AI DSA Coach

AI-powered Interactive Data Structures & Algorithms (DSA) Learning and Technical Interview Preparation Platform.

## 🚀 Overview
AI DSA Coach is designed around the core learning philosophy:
`Think → Attempt → Get Stuck → Get a Hint → Try Again → Solve → Explain → Master`

Rather than providing direct code solutions, the platform tracks problem attempts, evaluates code submissions, computes performance analytics, and prepares for fine-tuned LLM progressive coaching.

---

## 🏗️ Technology Stack

### Frontend
- **Framework:** React + TypeScript + Vite
- **Styling:** Tailwind CSS (Dark Mode / Developer Aesthetic)
- **Editor:** Monaco Editor (`@monaco-editor/react`)
- **Routing:** React Router v6
- **Data Visualization:** Recharts
- **HTTP Client:** Axios (with JWT interceptors)

### Backend
- **Framework:** Python 3.13 + Django 5 + Django REST Framework (DRF)
- **Authentication:** Django Auth + DRF SimpleJWT
- **Database:** PostgreSQL (with SQLite local fallback)
- **ORM & Migrations:** Django ORM & Django Migrations
- **Code Execution:** Isolated Docker Container Sandbox & Subprocess Sandbox with strict timeouts and resource limits.

---

## 📂 Architecture & Directory Structure

```text
ai-dsa-coach/
├── backend/
│   ├── manage.py
│   ├── config/              # Django settings, root URLs, WSGI, ASGI
│   ├── apps/
│   │   ├── users/           # Custom User model & SimpleJWT Auth APIs
│   │   ├── problems/        # 30 DSA Problems catalog & TestCase models
│   │   ├── progress/        # UserProblemProgress tracking & dashboard stats
│   │   ├── submissions/     # Code execution service, Run/Submit APIs, Analytics View
│   │   └── coaching/        # AIService stub abstraction for future LLM coaching
│   └── tests/               # Pytest suite (18 unit tests passing)
├── frontend/
│   ├── src/
│   │   ├── components/      # Navbar, CodeEditor (Monaco), ProtectedRoute, LoadingSpinner
│   │   ├── pages/           # Login, Register, Dashboard, Problems Explorer, Problem Detail, Analytics, Profile
│   │   ├── context/         # AuthContext (global state)
│   │   ├── services/        # api.ts, authService, problemService, progressService, submissionService, analyticsService
│   │   └── types/           # TypeScript interfaces
├── docs/
│   ├── code-execution.md    # Sandbox architecture & security parameters
│   └── database.md          # Database ER diagram & SQL/ORM aggregations
├── data/                    # Dataset storage for future ML fine-tuning
├── ml/                      # ML datasets, preprocessing, training & inference pipelines
├── docker/                  # Docker Compose & Dockerfile configurations
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚡ Quick Start & Local Setup

### 1. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv backend/venv
source backend/venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Apply database migrations
USE_SQLITE=True python backend/manage.py migrate

# Seed 30 curated DSA problems & test cases
USE_SQLITE=True python backend/manage.py seed_problems

# Run backend development server (Port 8000)
USE_SQLITE=True python backend/manage.py runserver 8000
```

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server (Port 5173)
npm run dev -- --port 5173
```

---

## 🧪 Testing & Verification

Run the full Django / Pytest test suite:
```bash
USE_SQLITE=True backend/venv/bin/pytest backend/tests/
```
*Output:* `18 passed in 3.54s`

Build the frontend bundle:
```bash
cd frontend && npm run build
```

---

## 🔒 Security Considerations
* Student code is **NEVER** executed inside the main Django application process.
* Executed in an isolated container/subprocess environment with:
  * Hard execution timeout (4.0s).
  * Strict memory limit (128MB).
  * Network isolation (`--network none`).
  * Read-only workspace mounting.
  * Traceback sanitization to prevent internal host directory exposure.

---

## 📑 Documentation Links
* [Code Execution Sandbox Documentation](docs/code-execution.md)
* [Database Schema & SQL Analytics Documentation](docs/database.md)
