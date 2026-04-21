# Ctrl+Eat Web App

Ctrl+Eat is a full-stack food tracking and recommendation app. Users can create
an account, complete a nutrition profile, save dietary preferences, search for
meals, log meals, track nutrient goals, and chat with an AI meal-planning
assistant.

The project is split into two local services:

- **Frontend:** Next.js app with API bridge routes
- **Backend:** Flask service for account, database, recommendation, and chat logic

## Tech Stack

- **Frontend:** Next.js 16, React 19, CSS Modules
- **Backend:** Python 3, Flask, Flask-CORS
- **Database:** PostgreSQL, commonly hosted with Supabase
- **External APIs:** Spoonacular for recipe search, Gemini for optional AI chat/explanations

## Project Structure

```text
web-app/
|- src/
|  |- app/
|  |  |- page.js                         # Main app UI
|  |  |- page.module.css                 # Main app styles
|  |  `- api/                            # Next.js API bridge routes
|  `- lib/
|     |- backendProxy.js                 # Shared proxy helper to Flask
|     |- session.js                      # Signed HTTP-only session helpers
|     `- authedRoute.js                  # Authenticated proxy helper
|- backend/
|  |- flask_app_runner.py                # Flask development entrypoint
|  |- schema.sql                         # PostgreSQL schema and seed data
|  |- requirements.txt                   # Python dependencies
|  |- pytest.ini                         # Backend test config
|  `- flask_service/
|     |- main.py                         # Flask route definitions
|     |- account_handling.py             # Account/login logic
|     |- admin.py                        # Admin-only user management
|     |- food_tracking.py                # Meal search/logging logic
|     |- recommendations.py              # Meal scoring/recommendation logic
|     |- chat.py                         # Gemini-backed assistant logic
|     `- globals.py                      # Env config and DB helpers
|- .env.example                          # Template environment variables
|- package.json                          # Frontend dependencies and scripts
`- README.md
```

## Prerequisites

Install these before running the app:

- **Node.js** 20 or newer
- **npm**
- **Python** 3.10 or newer
- **PostgreSQL database**, such as Supabase

Optional but recommended:

- A Spoonacular API key for recipe search
- A Gemini API key for AI chat and AI-generated recommendation text

## Environment Setup

From the `web-app` directory, copy the example env file:

```bash
cp .env.example .env.local
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env.local
```

Edit `.env.local` with your own values:

```env
FLASK_API_BASE_URL=http://127.0.0.1:5000
AUTH_SESSION_SECRET=replace-with-a-long-random-secret
ADMIN_BOOTSTRAP_USERNAMES=admin-username

POSTGRES_HOST=your-postgres-host
POSTGRES_DB=postgres
POSTGRES_USER=your-postgres-user
POSTGRES_PASSWORD=your-postgres-password
POSTGRES_PORT=5432
POSTGRES_SSLMODE=require

SPOONACULAR_API_KEY=your-spoonacular-key

GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-2.5-flash
```

### Environment Variable Notes

- `AUTH_SESSION_SECRET` should be any long random string. It signs session cookies.
- `ADMIN_BOOTSTRAP_USERNAMES` is a comma-separated list of usernames that should become admins when they log in or create an account.
- `POSTGRES_*` values come from your PostgreSQL/Supabase database connection settings.
- For Supabase on IPv4-only networks, use the **Session Pooler** connection values.
- `SPOONACULAR_API_KEY` is required for live recipe search.
- `GEMINI_API_KEY` is optional. Without it, chat uses a local fallback and recommendations still work deterministically.

## Database Setup

Create a PostgreSQL database, then run the schema file:

```text
backend/schema.sql
```

For Supabase:

1. Open your Supabase project.
2. Go to **SQL Editor**.
3. Paste the contents of `backend/schema.sql`.
4. Run the query.

The schema creates the login table, profile data, dietary preferences, meals,
nutrients, meal logs, goals, recommendation feedback, and seed nutrient/diet
values.

## Install Dependencies

From the `web-app` directory:

```bash
npm install
```

Then install backend dependencies.

macOS/Linux/WSL:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

If your Python environment blocks virtual environments, install the packages
using your system's preferred Python package workflow.

## Run The App

Open two terminals from the `web-app` directory.

### Terminal 1: Flask Backend

macOS/Linux/WSL:

```bash
source .venv/bin/activate
python backend/flask_app_runner.py
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python backend\flask_app_runner.py
```

The backend should run at:

```text
http://127.0.0.1:5000
```

### Terminal 2: Next.js Frontend

```bash
npm run dev
```

The frontend should run at:

```text
http://localhost:3000
```

Open `http://localhost:3000` in your browser.

## Creating An Admin User

Add the username to `.env.local`:

```env
ADMIN_BOOTSTRAP_USERNAMES=testuser
```

Restart Flask, then create or log in with that username. The backend will promote
that account to `admin`. Admin users see an **Admin** tab where they can:

- list users
- see account metadata and meal counts
- promote/demote roles
- reset user passwords
- delete users, except themselves or the final admin

## Common Commands

Run backend tests:

```bash
python -m pytest backend
```

Run frontend lint:

```bash
npm run lint
```

Build the frontend:

```bash
npm run build
```

## Quick Verification

Check Flask:

```bash
curl http://127.0.0.1:5000/health
```

Expected shape:

```json
{
  "success": true,
  "message": "Healthy.",
  "data": {
    "service": "ctrl-eat-backend"
  }
}
```

Check login through the frontend API:

```bash
curl -X POST "http://localhost:3000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"your-username","password":"your-password"}'
```

Successful responses use this general shape:

```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "username": "your-username",
    "role": "user"
  }
}
```

## Troubleshooting

### Backend says database is not configured

Check that `.env.local` exists in `web-app/` and includes:

```env
POSTGRES_HOST=
POSTGRES_USER=
POSTGRES_PASSWORD=
```

Restart Flask after changing env values.

### Supabase direct host does not connect

If Supabase says the direct host is not IPv4-compatible, use the **Session
Pooler** connection settings instead of the direct database host.

### Missing database columns or tables

Run the latest `backend/schema.sql` in your database. The app expects that schema.

### Spoonacular search does not work

Set `SPOONACULAR_API_KEY` in `.env.local`, then restart Flask.

### Gemini chat does not work

Set `GEMINI_API_KEY` and `GEMINI_MODEL` in `.env.local`, then restart Flask.
If Gemini returns quota/model errors, check your Google AI Studio project,
available models, and API quota.

### Frontend cannot reach backend

Make sure Flask is running on `http://127.0.0.1:5000` and that `.env.local`
contains:

```env
FLASK_API_BASE_URL=http://127.0.0.1:5000
```

## Notes

- Do not commit `.env.local`; it contains secrets.
- Passwords are stored hashed with Werkzeug.
- Chat history is session-local in the browser and is not persisted to the database.
- Flask returns a consistent JSON shape:

```json
{
  "success": true,
  "message": "Success.",
  "data": {}
}
```
