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

## Deploy on Railway (UI)

### 1. Create a new project in the Railway dashboard

Go to [railway.com](https://railway.com), create a new project, and connect your GitHub repo.

### 2. Add a Postgres database

In the project, click **Add Service → Database → PostgreSQL**.

### 3. Add the DATABASE_URL variable

In your app service's **Variables** tab, add:

```
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

This uses Railway's reference syntax to pull the connection string from the Postgres service.

### 4. Configure the start command

In your service settings, set the start command:

```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Railway auto-detects Python and installs from `requirements.txt` on each deploy.

### 5. Add a public domain

In your app service, go to the **Settings** tab and click **Generate Domain** under the Networking section. Railway will assign a public URL for your service.

### 6. Enable PR environments

In your Railway project settings, go to **Environments → Enable PR Environments**. From then on, every pull request gets its own isolated deployment with its own Postgres instance, and Railway tears it down automatically when the PR closes.

## Deploy on Railway (CLI)

### 1. Install the Railway CLI and log in

```bash
npm install -g @railway/cli
railway login
```

### 2. Initialize the project

From the `pr-environments` directory, link to a new or existing Railway project:

```bash
railway init
```

### 3. Add a Postgres database

```bash
railway add --database postgres
```

### 4. Add the DATABASE_URL variable

```bash
railway variables set DATABASE_URL='${{Postgres.DATABASE_URL}}'
```

This uses Railway's reference syntax to pull the connection string from the Postgres service.

### 5. Set the start command

```bash
railway service update --start-command "uvicorn main:app --host 0.0.0.0 --port \$PORT"
```

### 6. Deploy

```bash
railway up
```

### 7. Add a public domain

```bash
railway domain
```

Railway will generate and print a public URL for your service.

### 8. Enable PR environments

PR environments must be enabled in the Railway dashboard: go to your project settings, then **Environments → Enable PR Environments**. From then on, every pull request gets its own isolated deployment with its own Postgres instance, and Railway tears it down automatically when the PR closes.

## Local development

```bash
# install deps (using uv)
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

# start (requires a local DATABASE_URL)
DATABASE_URL=postgresql://... uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
