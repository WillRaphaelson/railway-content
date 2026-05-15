# agent-runner

A FastAPI webhook service that runs [Claude Code](https://docs.claude.com/en/docs/claude-code) on GitHub issues. When a new issue is opened, the service clones the repo, lets Claude implement it on a new branch, opens a PR, and comments back on the issue with the PR link.

## Structure

```
agent-runner/
├── agent_server.py     # FastAPI app with /webhook endpoint + pipeline
├── requirements.txt    # Python dependencies
└── Dockerfile          # Python + git + gh CLI + Claude Code
```

The Dockerfile installs `git`, the GitHub CLI (`gh`), Node.js, and the `@anthropic-ai/claude-code` npm package so the runner can drive Claude Code as a subprocess.

## How it works

1. GitHub sends a webhook to `/webhook` on every issue event.
2. The handler verifies the `x-hub-signature-256` HMAC against `GITHUB_WEBHOOK_SECRET` and triggers the pipeline.
3. The pipeline clones the repo into a tempdir, checks out `claude/issue-<number>`, and writes a prompt file built from the issue title and body.
4. `claude --print --dangerously-skip-permissions` is invoked with `Bash,Read,Edit,Write` allowed. Claude works autonomously and records any assumptions in `CLAUDE_NOTES.md`.
5. The runner commits, pushes, opens a PR via `gh pr create`, and posts the PR URL back as a comment on the issue.

## Webhook endpoint

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhook` | GitHub `issues` webhook receiver |

The endpoint expects a JSON `issues` event with an `x-hub-signature-256` header. It returns immediately with `{"status": "ok"}` and runs the pipeline in the background.

## Required environment variables

| Variable | Description |
|----------|-------------|
| `GITHUB_WEBHOOK_SECRET` | Shared secret used to verify webhook HMAC signatures. Any long random string — generate one with `openssl rand -hex 32` |
| `GITHUB_TOKEN` | A token used to clone, push, open PRs, and comment. See below |
| `ANTHROPIC_API_KEY` | API key used by the Claude Code CLI. Create one at [console.anthropic.com](https://console.anthropic.com) → **API Keys** |

## Create a GitHub token

The runner needs a token with write access to the target repo. A fine-grained personal access token scoped to a single repo is the safest option.

### Fine-grained PAT (recommended)

1. Go to [github.com/settings/personal-access-tokens](https://github.com/settings/personal-access-tokens) → **Generate new token**.
2. **Resource owner:** the user or org that owns the target repo.
3. **Repository access:** **Only select repositories** → pick the repo the runner should work on.
4. **Repository permissions:** set all three of the following to **Read and write** (not just Read — a Contents: Read-only token authenticates but 403s on `git push`):
   - **Contents** (clone and push branches)
   - **Pull requests** (open PRs)
   - **Issues** (post comments)
5. Generate the token and copy it. This is the value you'll use for `GITHUB_TOKEN`.

### Or, via the GitHub CLI

```bash
gh auth login --scopes repo
gh auth token
```

The printed token can be used as `GITHUB_TOKEN`. Note that classic tokens with `repo` scope are broader than the fine-grained version above — prefer the fine-grained PAT for production.

## Deploy on Railway (UI)

### 1. Create a new project

Go to [railway.com](https://railway.com), create a new project, and connect your GitHub repo.

### 2. Deploy the runner service

Add a service pointing to the `agent-runner/` directory (or set the root directory in service settings). Railway will detect the Dockerfile and use it. Configure it:

- **Variables:**
  - `GITHUB_WEBHOOK_SECRET=<a long random string>`
  - `GITHUB_TOKEN=<a GitHub PAT or fine-grained token with repo scope>`
  - `ANTHROPIC_API_KEY=<your Anthropic API key>`
- **Networking:** Generate a public domain so GitHub can reach the webhook.

The container starts on `$PORT` automatically — Railway injects it and `uvicorn` binds to `0.0.0.0:3000` as defined in the Dockerfile. If you'd rather bind to `$PORT`, override the start command to `uvicorn agent_server:app --host 0.0.0.0 --port $PORT`.

### 3. Register the webhook in GitHub

In the target repo, go to **Settings → Webhooks → Add webhook**:

- **Payload URL:** `https://<your-railway-domain>/webhook`
- **Content type:** `application/json`
- **Secret:** the same value as `GITHUB_WEBHOOK_SECRET`
- **Events:** select **Let me select individual events** and check **Issues** only.

### 4. Try it

Open an issue describing a small change. The runner will pick it up, push a branch, open a PR, and comment on the issue with the PR link.

---

## Deploy on Railway (CLI)

### 1. Install the Railway CLI and log in

```bash
npm install -g @railway/cli
railway login
```

### 2. Initialize the project

```bash
cd agent-runner
railway init
```

### 3. Deploy the runner

```bash
railway up --service agent-runner
railway variables set GITHUB_WEBHOOK_SECRET='<a long random string>' --service agent-runner
railway variables set GITHUB_TOKEN='<github token with repo scope>' --service agent-runner
railway variables set ANTHROPIC_API_KEY='<your anthropic api key>' --service agent-runner
railway domain --service agent-runner
```

### 4. Register the webhook with the GitHub CLI

```bash
gh api repos/<owner>/<repo>/hooks \
  --method POST \
  --field name=web \
  --field active=true \
  --field 'events[]=issues' \
  --field config[url]="https://<your-railway-domain>/webhook" \
  --field config[content_type]=json \
  --field config[secret]="<same value as GITHUB_WEBHOOK_SECRET>"
```

### 5. Try it

```bash
gh issue create --repo <owner>/<repo> --title "Add a /healthz endpoint" --body "Return 200 OK with {\"ok\": true}."
```

---

## Local development

```bash
cd agent-runner
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
npm install -g @anthropic-ai/claude-code

GITHUB_WEBHOOK_SECRET=dev-secret \
GITHUB_TOKEN=<token> \
ANTHROPIC_API_KEY=<key> \
uvicorn agent_server:app --host 0.0.0.0 --port 3000 --reload
```

To test the webhook against your local server, expose it with a tunnel (e.g. `ngrok http 3000`) and point the GitHub webhook at the tunnel URL.

## Security notes

- The runner verifies every webhook with HMAC-SHA256 before doing any work, so the endpoint is safe to expose publicly.
- The container runs as a non-root `appuser` (uid 1000), not as root.
- Claude Code runs with `--dangerously-skip-permissions` inside the container. The blast radius is the tempdir clone of the repo — the container has no persistent volume — but the `GITHUB_TOKEN` it uses is real. Scope the token to only the repos you want the runner to touch.
- Anyone who can open an issue on a repo with the webhook installed can trigger a run. For public repos this means anyone on GitHub — restrict accordingly, or filter the webhook payload to a set of allowed authors before running the pipeline.

## Troubleshooting

- **`git push` returns 403 "Permission denied"** — the `GITHUB_TOKEN` is missing `Contents: Read and write` on the target repo, or the repo isn't in the fine-grained PAT's "Selected repositories" list. Verify with `curl -s -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/repos/<owner>/<repo> | jq '.permissions'` — `push` must be `true`.
- **`gh pr create` fails** — needs `Pull requests: Read and write`.
- **`gh issue comment` fails** — needs `Issues: Read and write`.
