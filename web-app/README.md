# Ctrl+Eat Web App

Ctrl+Eat is a food recommendation/tracking project in early development.  
This repository consolidates the frontend and backend into one codebase:

- A Next.js app for the UI and API bridge layer
- A Flask service for backend logic and database operations

## Project Structure

```text
web-app/
|- src/
|  |- app/
|  |  |- page.js                         # Main app UI
|  |  |- page.module.css                 # Main app styles
|  |  `- api/                            # Next API bridge routes
|  `- lib/
|     |- backendProxy.js                 # Shared proxy helper to Flask
|     |- session.js                      # Signed HTTP-only session helpers
|     `- authedRoute.js                  # Authenticated proxy helper
|- backend/
|  |- flask_app_runner.py                # Flask dev entrypoint
|  |- schema.sql                         # PostgreSQL schema
|  |- requirements.txt                   # Python dependencies
|  `- flask_service/
|     |- main.py                         # Flask route definitions
|     |- account_handling.py             # Account/login logic
|     |- food_tracking.py                # Meal tracking logic
|     |- goal_tracking.py                # Goal tracking logic
|     `- globals.py                      # DB connection config/utilities
|- .env.example                          # Example environment variables
|- package.json
`- README.md
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

- Login/create account is served by Next.js at `/`
- Successful auth sets a signed HTTP-only session cookie
- Next.js API routes infer the current user from that session and proxy to Flask
- The app includes profile onboarding, preferences, search, meal logging, goals, progress, and recommendations
- Flask returns a consistent JSON shape:

```json
{ "success": true, "message": "Success.", "data": {} }
```

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
pip install -r backend/requirements.txt
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
AUTH_SESSION_SECRET=replace-with-a-long-random-secret
POSTGRES_HOST=aws-1-us-east-1.pooler.supabase.com
POSTGRES_DB=postgres
POSTGRES_USER=postgres.project-ref
POSTGRES_PASSWORD=replace-rotated-supabase-password
POSTGRES_PORT=5432
SPOONACULAR_API_KEY=replace-rotated-spoonacular-key
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
```

Before running against Supabase, apply `backend/schema.sql` and rotate the database/API keys that were previously committed in source.

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
{"success":true,"message":"Login successful.","data":{"username":"test"}}
```

## Important Notes

- Invalid credentials now return HTTP `401`.
- Passwords in the DB must be hashed for login to work.
- AI explanations/chat are optional; chat uses a local fallback and deterministic recommendation scoring works without `GEMINI_API_KEY`.
- Spoonacular search requires `SPOONACULAR_API_KEY`.
