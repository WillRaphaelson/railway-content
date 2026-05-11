# pr-environments

A FastAPI + Postgres API with a vanilla JS frontend demonstrating Railway PR environments. Each pull request gets its own isolated deployment with its own database.

## Structure

```
pr-environments/
├── backend/
│   ├── main.py           # FastAPI app with /trains endpoints
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx       # Train list + add modal
│   │   ├── App.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── .gitignore
```

The database is seeded with three example trains on first startup.

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/trains` | List all trains |
| `POST` | `/trains` | Create a train |

**POST body:**
```json
{
  "name": "string",
  "route": "string",
  "description": "string (optional)",
  "color": "string (optional)"
}
```

## Deploy on Railway (UI)

### 1. Create a new project

Go to [railway.com](https://railway.com), create a new project, and connect your GitHub repo.

### 2. Add a Postgres database

In the project, click **Add Service → Database → PostgreSQL**.

### 3. Deploy the backend service

Add a service pointing to the `backend/` directory (or set the root directory in service settings). Configure it:

- **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Variable:** `DATABASE_URL=${{Postgres.DATABASE_URL}}`
- **Networking:** Generate a public domain.

### 4. Deploy the frontend service

Add a second service pointing to the `frontend/` directory. Configure it:

- **Build command:** `npm run build`
- **Start command:** `npm start`
- **Variable:** `VITE_BACKEND_URL=https://${{backend.RAILWAY_PUBLIC_DOMAIN}}`
- **Networking:** Generate a public domain to access the UI.

Railway resolves the reference variable to the backend service's public domain at build time — including in PR environments, where each PR's frontend automatically gets that PR's backend URL.

### 5. Enable PR environments

In your Railway project settings, go to **Environments → Enable PR Environments**. Every pull request then gets its own isolated deployment with its own Postgres instance, torn down automatically when the PR closes.

---

## Deploy on Railway (CLI)

### 1. Install the Railway CLI and log in

```bash
npm install -g @railway/cli
railway login
```

### 2. Initialize the project

```bash
railway init
```

### 3. Add a Postgres database

```bash
railway add --database postgres
```

### 4. Deploy the backend

```bash
cd backend
railway up --service backend
railway variables set DATABASE_URL='${{Postgres.DATABASE_URL}}' --service backend
railway service update --start-command "uvicorn main:app --host 0.0.0.0 --port \$PORT" --service backend
railway domain --service backend
```

### 5. Deploy the frontend

```bash
cd ../frontend
railway up --service frontend
railway variables set VITE_BACKEND_URL='${{backend.RAILWAY_PUBLIC_DOMAIN}}' --service frontend
railway service update --build-command "npm run build" --start-command "npm start" --service frontend
railway domain --service frontend
```

### 6. Enable PR environments

PR environments must be enabled in the Railway dashboard: go to your project settings, then **Environments → Enable PR Environments**.

---

## Local development

### Backend

```bash
cd backend
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
DATABASE_URL=postgresql://... uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
VITE_BACKEND_URL=http://localhost:8000 npm run dev
# open http://localhost:5173
```
