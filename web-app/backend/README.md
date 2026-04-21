# Backend Service

This folder contains the consolidated Flask backend used by the Next.js app.

## What this does

- `backend/flask_service/` stores account, meals, goals, and app routes.
- `backend/flask_app_runner.py` starts the Flask app in development.
- Next.js API routes in `src/app/api/` proxy requests to this service.

## Run Flask backend

From `web-app/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python backend/flask_app_runner.py
```

Backend will run on `http://127.0.0.1:5000`.

## Connect Next.js to Flask

Set `FLASK_API_BASE_URL` in `web-app/.env.local`:

```bash
FLASK_API_BASE_URL=http://127.0.0.1:5000
```

The backend also needs the Postgres and Spoonacular variables listed in `../.env.example`.
Run `schema.sql` in Supabase before using the app against a fresh database.
