# Ctrl+Eat Web App

Ctrl+Eat is a food recommendation/tracking project in early development.  
This repository consolidates the frontend and backend into one codebase:

- A Next.js app for the UI and API bridge layer
- A Flask service for backend logic and database operations

## Project Structure

```text
web-app/
├─ src/
│  ├─ app/
│  │  ├─ page.js                         # Login UI
│  │  ├─ page.module.css                 # Login styles
│  │  └─ api/
│  │     └─ auth/
│  │        ├─ login/route.js            # Next route -> Flask /login
│  │        └─ create-account/route.js   # Next route -> Flask /create_acc
│  └─ lib/
│     └─ backendProxy.js                 # Shared proxy helper to Flask
├─ backend/
│  ├─ flask_app_runner.py                # Flask dev entrypoint
│  └─ flask_service/
│     ├─ main.py                         # Flask route definitions
│     ├─ account_handling.py             # Account/login logic
│     ├─ food_tracking.py                # Meal tracking logic
│     ├─ goal_tracking.py                # Goal tracking logic
│     └─ globals.py                      # DB connection config/utilities
├─ .env.example                          # Example environment variables
├─ package.json
└─ README.md
```

## Current Tech Stack

### Frontend

- **Next.js 16** (App Router)
- **React 19**
- CSS Modules for page styling

### Backend

- **Python 3**
- **Flask**
- `flask-cors` for CORS support
- `psycopg2-binary` for PostgreSQL/Supabase connection
- `werkzeug.security` for password hashing and verification
- `email-validator` for email validation

### Data/Infra

- PostgreSQL (Supabase-hosted in current dev setup)

## Current Implemented Flow

- Login page is served by Next.js at `/`
- Frontend sends login request to Next.js API route:
  - `POST /api/auth/login`
- Next.js route proxies request to Flask:
  - `POST /login`
- Create-account proxy is also available:
  - `POST /api/auth/create-account` -> Flask `POST /create_acc`

## Setup and Run

Open two terminals and run backend + frontend separately.

### 1) Backend (Flask)

From the `web-app` directory:

```bash
cd /home/perezdev/Team-8-Software-Engineering-Project/web-app
```

#### Preferred (virtual environment)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask flask-cors psycopg2-binary werkzeug email-validator
python backend/flask_app_runner.py
```

#### If your Linux/WSL setup blocks venv/pip (PEP 668)

```bash
python3 -m pip install --user --break-system-packages flask flask-cors psycopg2-binary werkzeug email-validator
python3 backend/flask_app_runner.py
```

Flask should start at `http://127.0.0.1:5000`.

### 2) Frontend (Next.js)

In another terminal:

```bash
cd /home/perezdev/Team-8-Software-Engineering-Project/web-app
cp .env.example .env.local
npm install
npm run dev
```

Next.js should start at `http://localhost:3000`.

## Environment Variables

Create `.env.local` in `web-app`:

```bash
FLASK_API_BASE_URL=http://127.0.0.1:5000
```

## Quick Verification

### Browser test

1. Open `http://localhost:3000`
2. Submit login form
3. Check response message on page (`Login successful.` for valid credentials)

### API test

```bash
curl -s -X POST "http://localhost:3000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"1234"}'
```

Expected successful response:

```json
{"message":"Login successful."}
```

## Important Notes

- Current backend returns auth result mainly via `message` text.
- Invalid credentials may still return HTTP `200` with an error message string.
- Passwords in the DB must be hashed (not plain text) for login to work.
- This project is in early-stage development; architecture is set up for clean frontend/backend separation while staying in one repository.
