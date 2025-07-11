# Research Assistant

A full-stack platform for automated research and analysis, featuring a FastAPI backend and a React + Vite + TypeScript frontend.

---

## Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Directory Structure](#directory-structure)
- [Requirements](#requirements)
- [Backend Setup (FastAPI)](#backend-setup-fastapi)
- [Frontend Setup (React + Vite)](#frontend-setup-react--vite)
- [Database Migrations](#database-migrations)
- [Environment Variables](#environment-variables)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Project Overview

Research Assistant is an automated research and analysis platform. It provides a RESTful API for research management and a modern frontend for user interaction.

## Features
- Research project creation and management
- Source and content analysis
- Task queue and background processing
- Modern, type-safe React frontend
- API-first architecture

## Directory Structure
```
Research-Assistant/
  Backend/                # FastAPI backend
    app/                  # Application code (API, models, services, tasks)
    alembic/              # Database migrations
    requirements.txt      # Python dependencies
    main.py               # FastAPI entry point
  research_assistant_frontend/ # React + Vite frontend
    src/                  # Frontend source code
    package.json          # Frontend dependencies and scripts
    README.md             # Frontend-specific documentation
  README.md               # Project-level documentation (this file)
```

## Requirements

- **Backend:**
  - Python 3.12+
  - PostgreSQL (or your configured database)
  - (Recommended) Virtual environment tool (e.g., `venv`)

- **Frontend:**
  - Node.js 18+
  - npm 9+

- **General:**
  - Git (for version control)
  - Modern web browser (for frontend usage)

## Backend Setup (FastAPI)

### Prerequisites
- Python 3.12+
- (Recommended) Create and activate a virtual environment:
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  ```
- Install dependencies:
  ```bash
  pip install -r Backend/requirements.txt
  ```

### Running the Backend
From the project root:
```bash
uvicorn Backend.main:app --reload
```
- The API will be available at `http://localhost:8000`
- Health check: `GET /health`

## Frontend Setup (React + Vite)

See [research_assistant_frontend/README.md](research_assistant_frontend/README.md) for advanced configuration.

### Prerequisites
- Node.js 18+
- npm 9+

### Install dependencies
```bash
npm install --prefix research_assistant_frontend
```

### Start the development server
```bash
npm run dev --prefix research_assistant_frontend
```
- The app will be available at `http://localhost:5173` (or next available port)

## Database Migrations

- Alembic is used for migrations.
- Migration scripts are in `Backend/alembic/versions/`.

### Running migrations
```bash
cd Backend
alembic upgrade head
```

## Environment Variables
- Backend uses `python-dotenv` for environment variables. Create a `.env` file in `Backend/` as needed.
- Frontend uses Vite environment variables (see Vite docs).

## Development Workflow
- Backend: Edit code in `Backend/app/`, restart server as needed.
- Frontend: Edit code in `research_assistant_frontend/src/`, Vite provides hot reload.
- Use `ERRORS.md` in the frontend for tracking and resolving issues.

## Troubleshooting
- If you see `axios` not found errors in the frontend, run:
  ```bash
  npm install axios --prefix research_assistant_frontend
  ```
- For CORS issues, ensure backend `allow_origins` matches frontend dev server URL.
- For database errors, check your `.env` and run migrations.

## License
MIT (or specify your license here) 