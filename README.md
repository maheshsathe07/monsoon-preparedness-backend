# Monsoon Preparedness Backend

FastAPI service for the Monsoon Preparedness GenAI solution. The service is scoped to backend APIs only so a v0-generated frontend can be added later and integrated against `/api/v1`.

## What is included

- FastAPI app with profile, chat, checklist, weather, emergency ID, alerts, supplies, reports, and auth endpoints.
- OpenAI integration through a backend proxy only. Keys never need to reach the frontend.
- Supabase REST persistence for demo-friendly deployment.
- Open-Meteo weather forecast integration with risk level calculation.
- QR and PDF helpers for emergency ID cards and recovery reports.
- SQL migration file for Supabase tables with RLS intentionally not enabled for demo flow.

## Quick start

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.template .env
uvicorn main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

## Supabase Setup

Open Supabase SQL Editor and run:

```sql
-- migrations/001_initial_schema.sql
```

Do not enable RLS for the demo if you want low-friction inserts from the backend service.

## Environment

Use `.env.template` as the shape. Put real keys in `.env` only. `.env` is ignored by git.

For Supabase writes from this backend, prefer a server-side service role key in `SUPABASE_SERVICE_ROLE_KEY`. Keep it only in Railway/Vercel environment variables or a local `.env`.

For the deployed frontend, set this in Railway:

```env
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:5174,https://monsoon-preparedness-app-s6kv.vercel.app
```

## Deployment

Railway:

```powershell
cd backend
railway up
```

Vercel serverless:

```powershell
cd backend
vercel
```

The Vercel entrypoint is `api/index.py`. Local development can use either `uvicorn main:app --reload --port 8000` or `uvicorn app.main:app --reload --port 8000`.

## Frontend contract

All user-facing endpoints are mounted under `/api/v1`, for example:

- `POST /api/v1/profile`
- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `POST /api/v1/chat`
- `GET /api/v1/checklist/{user_id}`
- `GET /api/v1/weather/{lat}/{lng}`
