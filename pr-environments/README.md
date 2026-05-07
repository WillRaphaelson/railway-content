# pr-environments

A minimal FastAPI + Postgres API demonstrating Railway PR environments. Each pull request gets its own isolated deployment with its own database.

## Files

```
pr-environments/
├── main.py           # FastAPI app with /trains endpoints
├── requirements.txt  # Python dependencies
└── .gitignore
```

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

## Deploy on Railway

### 1. Create a new project in the Railway dashboard

Go to [railway.com](https://railway.com), create a new project, and connect your GitHub repo.

### 2. Add a Postgres database

In the project, click **Add Service → Database → PostgreSQL**. Railway will automatically inject `DATABASE_URL` into your app's environment.

### 3. Configure the start command

In your service settings, set the start command:

```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Railway auto-detects Python and installs from `requirements.txt` on each deploy.

### 4. Enable PR environments

In your Railway project settings, go to **Environments → Enable PR Environments**. From then on, every pull request gets its own isolated deployment with its own Postgres instance, and Railway tears it down automatically when the PR closes.

## Local development

```bash
# install deps (using uv)
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

# run (requires a local DATABASE_URL)
DATABASE_URL=postgresql://... uvicorn main:app --reload
```
